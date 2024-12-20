/**
 * @file Theme Provider Component
 * @version 1.0.0
 * @description React context provider that manages application-wide theme state with
 * support for light/dark modes, RTL layouts, and WCAG 2.1 AA compliance.
 */

import React, { createContext, useContext, useEffect, useState } from 'react'
import { useTheme as useNextTheme } from 'next-themes'
import { colors, fonts, spacing, transitions } from '@/config/theme'

// Theme context type definition
interface ThemeContextType {
  theme: string
  setTheme: (theme: string) => void
  systemTheme: string | undefined
  direction: 'ltr' | 'rtl'
  setDirection: (direction: 'ltr' | 'rtl') => void
  isTransitioning: boolean
}

// Create theme context with null initial value
const ThemeContext = createContext<ThemeContextType | null>(null)

// Theme provider props interface
interface ThemeProviderProps {
  children: React.ReactNode
  defaultTheme?: string
  transitionDuration?: number
}

/**
 * Theme Provider Component
 * Manages application-wide theme state and provides theme switching functionality
 */
export function ThemeProvider({
  children,
  defaultTheme = 'system',
  transitionDuration = 200
}: ThemeProviderProps) {
  // Initialize theme state using next-themes
  const { theme, setTheme, systemTheme } = useNextTheme()
  
  // RTL support state
  const [direction, setDirection] = useState<'ltr' | 'rtl'>('ltr')
  
  // Theme transition state
  const [isTransitioning, setIsTransitioning] = useState(false)

  // System theme preference detection
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    
    const handleChange = (e: MediaQueryListEvent) => {
      if (theme === 'system') {
        setIsTransitioning(true)
        document.documentElement.classList.toggle('dark', e.matches)
        setTimeout(() => setIsTransitioning(false), transitionDuration)
      }
    }

    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [theme, transitionDuration])

  // Theme CSS variable application
  useEffect(() => {
    const root = document.documentElement
    const currentTheme = theme === 'system' ? systemTheme : theme
    
    // Apply color tokens
    Object.entries(colors).forEach(([key, value]) => {
      const tokenValue = currentTheme === 'dark' ? value.dark : value.light
      root.style.setProperty(`--color-${key}`, tokenValue)
    })

    // Apply font tokens
    Object.entries(fonts).forEach(([key, value]) => {
      root.style.setProperty(`--font-${key}`, value.join(', '))
    })

    // Apply spacing tokens
    Object.entries(spacing).forEach(([key, value]) => {
      root.style.setProperty(`--spacing-${key}`, value)
    })
  }, [theme, systemTheme])

  // Direction change handler
  useEffect(() => {
    document.documentElement.dir = direction
    document.documentElement.setAttribute('dir', direction)
  }, [direction])

  // Theme transition handler
  useEffect(() => {
    const root = document.documentElement
    
    if (isTransitioning) {
      root.style.setProperty('--transition-duration', `${transitionDuration}ms`)
      root.classList.add('theme-transitioning')
    } else {
      root.classList.remove('theme-transitioning')
    }
  }, [isTransitioning, transitionDuration])

  // Theme persistence
  useEffect(() => {
    const savedDirection = localStorage.getItem('direction') as 'ltr' | 'rtl'
    if (savedDirection) {
      setDirection(savedDirection)
    }
  }, [])

  // Theme change handler
  const handleThemeChange = (newTheme: string) => {
    setIsTransitioning(true)
    setTheme(newTheme)
    setTimeout(() => setIsTransitioning(false), transitionDuration)
  }

  // Direction change handler with persistence
  const handleDirectionChange = (newDirection: 'ltr' | 'rtl') => {
    setDirection(newDirection)
    localStorage.setItem('direction', newDirection)
  }

  // Create context value
  const contextValue: ThemeContextType = {
    theme: theme || defaultTheme,
    setTheme: handleThemeChange,
    systemTheme,
    direction,
    setDirection: handleDirectionChange,
    isTransitioning
  }

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  )
}

/**
 * Custom hook to access theme context
 * @throws {Error} When used outside of ThemeProvider
 */
export function useThemeContext(): ThemeContextType {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useThemeContext must be used within a ThemeProvider')
  }
  return context
}

// Export theme context for testing purposes
export { ThemeContext }