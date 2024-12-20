import type { LoadingState } from '../types/common';

/**
 * Application route paths with type safety
 * @constant
 */
export const ROUTE_PATHS = {
  // Public routes
  HOME: '/',
  SEARCH: '/search',
  ERROR: '/error',
  NOT_FOUND: '/404',
  UNAUTHORIZED: '/401',

  // Student routes
  STUDENT: '/student',
  STUDENT_PLAN: '/student/plan',
  STUDENT_PLAN_DETAIL: '/student/plan/[id]',
  STUDENT_PLAN_EDIT: '/student/plan/[id]/edit',
  STUDENT_PLAN_CREATE: '/student/plan/create',

  // Administrator routes
  DASHBOARD: '/dashboard',
  REQUIREMENTS: '/dashboard/requirements',
  REQUIREMENT_DETAIL: '/dashboard/requirements/[id]',
  REQUIREMENT_EDIT: '/dashboard/requirements/[id]/edit',
  REQUIREMENT_CREATE: '/dashboard/requirements/create',
  
  // System administration routes
  ADMIN: '/admin',
  ADMIN_USERS: '/admin/users',
  ADMIN_INSTITUTIONS: '/admin/institutions',
} as const;

/**
 * Routes that require authentication
 * @constant
 */
export const PROTECTED_ROUTES = [
  ROUTE_PATHS.DASHBOARD,
  ROUTE_PATHS.REQUIREMENTS,
  ROUTE_PATHS.REQUIREMENT_DETAIL,
  ROUTE_PATHS.REQUIREMENT_EDIT,
  ROUTE_PATHS.REQUIREMENT_CREATE,
  ROUTE_PATHS.STUDENT_PLAN,
  ROUTE_PATHS.STUDENT_PLAN_DETAIL,
  ROUTE_PATHS.STUDENT_PLAN_EDIT,
  ROUTE_PATHS.STUDENT_PLAN_CREATE,
  ROUTE_PATHS.ADMIN,
  ROUTE_PATHS.ADMIN_USERS,
  ROUTE_PATHS.ADMIN_INSTITUTIONS,
];

/**
 * Route metadata for SEO and accessibility
 * @constant
 */
export const ROUTE_METADATA: Record<string, {
  title: string;
  description: string;
  requiresAuth: boolean;
  roles?: string[];
}> = {
  [ROUTE_PATHS.HOME]: {
    title: 'Transfer Requirements Management System',
    description: 'Manage and explore course transfer requirements between California colleges and universities',
    requiresAuth: false
  },
  [ROUTE_PATHS.SEARCH]: {
    title: 'Search Transfer Requirements',
    description: 'Search and explore transfer requirements across California institutions',
    requiresAuth: false
  },
  [ROUTE_PATHS.DASHBOARD]: {
    title: 'Administrator Dashboard',
    description: 'Manage transfer requirements and system settings',
    requiresAuth: true,
    roles: ['admin', 'institution_admin']
  },
  [ROUTE_PATHS.REQUIREMENTS]: {
    title: 'Transfer Requirements',
    description: 'View and manage transfer requirement definitions',
    requiresAuth: true,
    roles: ['admin', 'institution_admin']
  },
  [ROUTE_PATHS.STUDENT_PLAN]: {
    title: 'Student Transfer Plan',
    description: 'View and manage your transfer planning progress',
    requiresAuth: true,
    roles: ['student']
  },
  [ROUTE_PATHS.ADMIN]: {
    title: 'System Administration',
    description: 'Manage system settings and user access',
    requiresAuth: true,
    roles: ['admin']
  }
};

/**
 * Generates a type-safe dynamic route path by replacing parameters
 * @param path - The route path template
 * @param params - Parameters to inject into the path
 * @returns The generated route path
 */
export function generatePath(path: string, params: Record<string, string>): string {
  let generatedPath = path;

  // Validate path exists in ROUTE_PATHS
  const validPaths = Object.values(ROUTE_PATHS);
  if (!validPaths.includes(path as any)) {
    throw new Error(`Invalid route path: ${path}`);
  }

  // Replace dynamic parameters
  Object.entries(params).forEach(([key, value]) => {
    const placeholder = `[${key}]`;
    if (!generatedPath.includes(placeholder)) {
      throw new Error(`Parameter ${key} not found in path ${path}`);
    }
    generatedPath = generatedPath.replace(placeholder, value);
  });

  // Validate all parameters were replaced
  if (generatedPath.includes('[') || generatedPath.includes(']')) {
    throw new Error(`Missing required parameters for path ${path}`);
  }

  return generatedPath;
}

/**
 * Checks if a route requires authentication
 * @param path - The route path to check
 * @returns True if the route requires authentication
 */
export function isProtectedRoute(path: string): boolean {
  // Normalize the path
  const normalizedPath = path.split('?')[0].split('#')[0];
  
  // Check exact matches
  if (PROTECTED_ROUTES.includes(normalizedPath as any)) {
    return true;
  }

  // Check if path starts with any protected route prefix
  return PROTECTED_ROUTES.some(protectedRoute => {
    const routeBase = protectedRoute.split('[')[0];
    return normalizedPath.startsWith(routeBase);
  });
}

/**
 * Retrieves metadata for a given route
 * @param path - The route path
 * @returns Route metadata for SEO and accessibility
 */
export function getRouteMetadata(path: string): {
  title: string;
  description: string;
  requiresAuth: boolean;
  roles?: string[];
} {
  // Normalize the path
  const normalizedPath = path.split('?')[0].split('#')[0];
  
  // Find exact match
  if (ROUTE_METADATA[normalizedPath]) {
    return ROUTE_METADATA[normalizedPath];
  }

  // Find matching dynamic route
  const dynamicMatch = Object.entries(ROUTE_METADATA).find(([routePath]) => {
    const routeBase = routePath.split('[')[0];
    return normalizedPath.startsWith(routeBase);
  });

  if (dynamicMatch) {
    return dynamicMatch[1];
  }

  // Return default metadata if no match found
  return {
    title: 'Transfer Requirements Management System',
    description: 'Manage and explore course transfer requirements',
    requiresAuth: false
  };
}