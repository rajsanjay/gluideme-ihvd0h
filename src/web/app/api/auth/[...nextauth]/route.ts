/**
 * @fileoverview Next.js API route handler for NextAuth.js authentication
 * Implements secure JWT-based authentication with comprehensive security controls
 * @version 1.0.0
 */

import NextAuth, { NextAuthOptions } from 'next-auth'; // ^4.22.1
import CredentialsProvider from 'next-auth/providers/credentials'; // ^4.22.1
import { JWT } from 'next-auth/jwt'; // ^4.22.1
import { Ratelimit } from '@upstash/ratelimit'; // ^0.4.3
import { CloudWatch } from '@aws-sdk/client-cloudwatch'; // ^3.370.0
import { LoginCredentials, AuthResponse } from '../../../../types/auth';
import { AUTH_CONFIG } from '../../../../config/auth';
import { login } from '../../../../lib/api/auth';

// Initialize CloudWatch for security monitoring
const cloudWatch = new CloudWatch({
  region: process.env.AWS_REGION || 'us-west-2',
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!
  }
});

// Initialize rate limiter
const rateLimiter = new Ratelimit({
  redis: {
    url: process.env.REDIS_URL!
  },
  limiter: Ratelimit.slidingWindow(10, '5m') // 10 requests per 5 minutes
});

/**
 * Security monitoring function to track authentication events
 * @param event - Authentication event details
 */
const monitorAuthEvent = async (event: {
  type: string;
  success: boolean;
  email?: string;
  error?: string;
}) => {
  try {
    await cloudWatch.putMetricData({
      Namespace: 'TRMS/Authentication',
      MetricData: [
        {
          MetricName: 'AuthenticationAttempt',
          Value: 1,
          Unit: 'Count',
          Dimensions: [
            { Name: 'EventType', Value: event.type },
            { Name: 'Success', Value: event.success.toString() }
          ],
          Timestamp: new Date()
        }
      ]
    });
  } catch (error) {
    console.error('Failed to log authentication metric:', error);
  }
};

/**
 * NextAuth configuration options with enhanced security
 */
export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      id: 'credentials',
      name: 'Credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' }
      },
      async authorize(credentials) {
        try {
          if (!credentials?.email || !credentials?.password) {
            throw new Error('Invalid credentials');
          }

          const loginData: LoginCredentials = {
            email: credentials.email,
            password: credentials.password
          };

          const response: AuthResponse = await login(loginData);
          
          if (!response.user) {
            throw new Error('Authentication failed');
          }

          await monitorAuthEvent({
            type: 'login',
            success: true,
            email: credentials.email
          });

          return {
            id: response.user.id,
            email: response.user.email,
            role: response.user.role,
            accessToken: response.tokens.accessToken,
            refreshToken: response.tokens.refreshToken
          };
        } catch (error) {
          await monitorAuthEvent({
            type: 'login',
            success: false,
            email: credentials?.email,
            error: (error as Error).message
          });
          throw error;
        }
      }
    })
  ],
  session: {
    strategy: 'jwt',
    maxAge: AUTH_CONFIG.ACCESS_TOKEN_DURATION
  },
  jwt: {
    secret: process.env.JWT_SECRET,
    maxAge: AUTH_CONFIG.ACCESS_TOKEN_DURATION
  },
  pages: {
    signIn: '/auth/login',
    error: '/auth/error'
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.role = user.role;
        token.accessToken = user.accessToken;
        token.refreshToken = user.refreshToken;
      }
      return token;
    },
    async session({ session, token }) {
      if (token && session.user) {
        session.user.role = token.role as string;
        session.user.accessToken = token.accessToken as string;
      }
      return session;
    }
  },
  events: {
    async signIn({ user }) {
      await monitorAuthEvent({
        type: 'signIn',
        success: true,
        email: user.email
      });
    },
    async signOut({ token }) {
      await monitorAuthEvent({
        type: 'signOut',
        success: true,
        email: token.email as string
      });
    }
  }
};

/**
 * Rate limiting middleware for authentication requests
 */
const rateLimit = async (request: Request) => {
  const ip = request.headers.get('x-forwarded-for') || 'unknown';
  const { success } = await rateLimiter.limit(ip);
  
  if (!success) {
    await monitorAuthEvent({
      type: 'rateLimit',
      success: false,
      error: 'Rate limit exceeded'
    });
    return new Response('Too Many Requests', { status: 429 });
  }
};

/**
 * Enhanced GET request handler with security controls
 */
export async function GET(request: Request) {
  const rateLimitResponse = await rateLimit(request);
  if (rateLimitResponse) return rateLimitResponse;

  return NextAuth(authOptions)(request);
}

/**
 * Enhanced POST request handler with security controls
 */
export async function POST(request: Request) {
  const rateLimitResponse = await rateLimit(request);
  if (rateLimitResponse) return rateLimitResponse;

  // Validate CSRF token
  const csrfToken = request.headers.get('x-csrf-token');
  if (!csrfToken || csrfToken !== request.cookies.get('csrf_token')?.value) {
    await monitorAuthEvent({
      type: 'csrfValidation',
      success: false,
      error: 'CSRF validation failed'
    });
    return new Response('Invalid CSRF token', { status: 403 });
  }

  return NextAuth(authOptions)(request);
}