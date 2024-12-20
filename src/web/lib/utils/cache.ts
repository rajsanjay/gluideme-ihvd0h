/**
 * @fileoverview Browser-side caching utilities with TTL, versioning, and stale-while-revalidate support
 * @version 1.0.0
 */

import { CACHE } from '../../config/constants';
import type { AsyncState } from '../../types/common';

// Cache version for invalidation on major changes
const CACHE_VERSION = '1';
const CACHE_PREFIX = 'trms_cache_';
const MAX_KEY_LENGTH = 128;
const MAX_CACHE_SIZE = 5 * 1024 * 1024; // 5MB max cache size
const CRITICAL_CACHE_KEYS = ['user_preferences', 'app_config'];

/**
 * Interface defining the structure of cached entries
 */
export interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
  isCritical: boolean;
  compressed: boolean;
}

/**
 * Stores data in browser cache with TTL, versioning, and size validation
 * @template T Type of data being cached
 * @param key Cache key identifier
 * @param data Data to be cached
 * @param ttl Time-to-live in seconds (defaults to CACHE.TTL)
 * @param isCritical Whether the item is critical and should be preserved
 * @returns Promise resolving to success status
 */
export async function setCacheItem<T>(
  key: string,
  data: T,
  ttl: number = CACHE.TTL,
  isCritical: boolean = false
): Promise<boolean> {
  try {
    // Validate key length
    if (!key || key.length > MAX_KEY_LENGTH) {
      console.error('Invalid cache key length');
      return false;
    }

    const cacheKey = `${CACHE_PREFIX}${CACHE_VERSION}_${key}`;
    const timestamp = Date.now();

    // Check available space and perform LRU eviction if needed
    await ensureCacheSpace();

    // Prepare cache entry
    const entry: CacheEntry<T> = {
      data,
      timestamp,
      ttl,
      isCritical,
      compressed: false
    };

    // Compress if data is large
    const serialized = JSON.stringify(entry);
    if (serialized.length > 50000) {
      entry.compressed = true;
      entry.data = await compressData(data as unknown as string) as unknown as T;
    }

    // Store in localStorage
    localStorage.setItem(cacheKey, JSON.stringify(entry));

    // Update cache metadata
    updateCacheMetadata(cacheKey, serialized.length);

    return true;
  } catch (error) {
    if (error instanceof Error) {
      console.error('Cache storage error:', error.message);
    }
    return false;
  }
}

/**
 * Retrieves and validates cached data with stale-while-revalidate support
 * @template T Expected type of cached data
 * @param key Cache key identifier
 * @param allowStale Whether to return stale data during revalidation
 * @returns Promise resolving to cached data and stale status
 */
export async function getCacheItem<T>(
  key: string,
  allowStale: boolean = true
): Promise<{ data: T | null; isStale: boolean }> {
  try {
    const cacheKey = `${CACHE_PREFIX}${CACHE_VERSION}_${key}`;
    const cached = localStorage.getItem(cacheKey);

    if (!cached) {
      return { data: null, isStale: false };
    }

    const entry = JSON.parse(cached) as CacheEntry<T>;
    const { expired, isStale } = await isExpired(entry, allowStale);

    // Handle compressed data
    if (entry.compressed) {
      entry.data = await decompressData(entry.data as unknown as string) as unknown as T;
    }

    // Update access metadata for LRU
    updateAccessMetadata(cacheKey);

    if (expired) {
      return { data: null, isStale: false };
    }

    return { data: entry.data, isStale };
  } catch (error) {
    if (error instanceof Error) {
      console.error('Cache retrieval error:', error.message);
    }
    return { data: null, isStale: false };
  }
}

/**
 * Removes item from cache with critical item protection
 * @param key Cache key identifier
 * @param forceCritical Force removal even if item is critical
 */
export async function removeCacheItem(
  key: string,
  forceCritical: boolean = false
): Promise<void> {
  try {
    const cacheKey = `${CACHE_PREFIX}${CACHE_VERSION}_${key}`;
    
    // Check if item is critical
    if (!forceCritical && CRITICAL_CACHE_KEYS.includes(key)) {
      console.warn('Attempted to remove critical cache item:', key);
      return;
    }

    localStorage.removeItem(cacheKey);
    removeFromCacheMetadata(cacheKey);
  } catch (error) {
    if (error instanceof Error) {
      console.error('Cache removal error:', error.message);
    }
  }
}

/**
 * Clears all non-critical cached items
 * @param includesCritical Whether to clear critical items as well
 */
export async function clearCache(includesCritical: boolean = false): Promise<void> {
  try {
    const keys = Object.keys(localStorage);
    const cacheKeys = keys.filter(key => key.startsWith(CACHE_PREFIX));

    for (const key of cacheKeys) {
      const baseKey = key.replace(`${CACHE_PREFIX}${CACHE_VERSION}_`, '');
      
      if (includesCritical || !CRITICAL_CACHE_KEYS.includes(baseKey)) {
        localStorage.removeItem(key);
      }
    }

    resetCacheMetadata();
  } catch (error) {
    if (error instanceof Error) {
      console.error('Cache clear error:', error.message);
    }
  }
}

/**
 * Checks if cache entry is expired with stale grace period support
 * @param entry Cache entry to check
 * @param checkStale Whether to check stale-while-revalidate window
 * @returns Expiration status with stale state
 */
async function isExpired(
  entry: CacheEntry<unknown>,
  checkStale: boolean
): Promise<{ expired: boolean; isStale: boolean }> {
  const now = Date.now();
  const age = now - entry.timestamp;
  const primaryTTL = entry.ttl * 1000;
  const staleTTL = primaryTTL + (CACHE.STALE_WHILE_REVALIDATE * 1000);

  if (age <= primaryTTL) {
    return { expired: false, isStale: false };
  }

  if (checkStale && age <= staleTTL) {
    return { expired: false, isStale: true };
  }

  return { expired: true, isStale: false };
}

/**
 * Ensures cache size remains within limits using LRU eviction
 */
async function ensureCacheSpace(): Promise<void> {
  const metadata = getCacheMetadata();
  if (metadata.totalSize <= MAX_CACHE_SIZE) return;

  const keys = Object.keys(metadata.items)
    .filter(key => !CRITICAL_CACHE_KEYS.includes(key))
    .sort((a, b) => metadata.items[a].lastAccess - metadata.items[b].lastAccess);

  for (const key of keys) {
    await removeCacheItem(key);
    if (getCacheMetadata().totalSize <= MAX_CACHE_SIZE * 0.8) break;
  }
}

/**
 * Compresses string data for storage
 * @param data Data to compress
 * @returns Compressed data string
 */
async function compressData(data: string): Promise<string> {
  // Use CompressionStream when available, fallback to basic encoding
  if (typeof CompressionStream !== 'undefined') {
    const stream = new Blob([data]).stream();
    const compressedStream = stream.pipeThrough(new CompressionStream('gzip'));
    const compressedBlob = await new Response(compressedStream).blob();
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.readAsDataURL(compressedBlob);
    });
  }
  return btoa(encodeURIComponent(data));
}

/**
 * Decompresses stored data
 * @param data Compressed data string
 * @returns Decompressed data string
 */
async function decompressData(data: string): Promise<string> {
  // Use DecompressionStream when available, fallback to basic decoding
  if (typeof DecompressionStream !== 'undefined' && data.startsWith('data:')) {
    const response = await fetch(data);
    const stream = response.body!.pipeThrough(new DecompressionStream('gzip'));
    return new TextDecoder().decode(await new Response(stream).arrayBuffer());
  }
  return decodeURIComponent(atob(data));
}

// Cache metadata management helpers
function getCacheMetadata() {
  const metadata = localStorage.getItem(`${CACHE_PREFIX}metadata`);
  return metadata ? JSON.parse(metadata) : { totalSize: 0, items: {} };
}

function updateCacheMetadata(key: string, size: number) {
  const metadata = getCacheMetadata();
  metadata.items[key] = { size, lastAccess: Date.now() };
  metadata.totalSize = Object.values(metadata.items)
    .reduce((total, item: any) => total + item.size, 0);
  localStorage.setItem(`${CACHE_PREFIX}metadata`, JSON.stringify(metadata));
}

function updateAccessMetadata(key: string) {
  const metadata = getCacheMetadata();
  if (metadata.items[key]) {
    metadata.items[key].lastAccess = Date.now();
    localStorage.setItem(`${CACHE_PREFIX}metadata`, JSON.stringify(metadata));
  }
}

function removeFromCacheMetadata(key: string) {
  const metadata = getCacheMetadata();
  if (metadata.items[key]) {
    metadata.totalSize -= metadata.items[key].size;
    delete metadata.items[key];
    localStorage.setItem(`${CACHE_PREFIX}metadata`, JSON.stringify(metadata));
  }
}

function resetCacheMetadata() {
  localStorage.setItem(`${CACHE_PREFIX}metadata`, JSON.stringify({ totalSize: 0, items: {} }));
}