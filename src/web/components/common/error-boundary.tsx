/**
 * @fileoverview Production-ready React Error Boundary component with CloudWatch integration
 * Provides comprehensive error handling, monitoring, and recovery options
 * @version 1.0.0
 */

import * as React from 'react';
import { CloudWatchClient, PutMetricDataCommand } from '@aws-sdk/client-cloudwatch'; // v3.0.0
import { Toast } from './toast';

/**
 * Enum defining different types of errors that can be handled
 */
export enum ErrorType {
  RUNTIME = 'RUNTIME',
  NETWORK = 'NETWORK',
  RESOURCE = 'RESOURCE',
  UNKNOWN = 'UNKNOWN'
}

/**
 * Props interface for the ErrorBoundary component
 */
export interface ErrorBoundaryProps {
  /** Child components to be rendered */
  children: React.ReactNode;
  /** Custom fallback UI to display when an error occurs */
  fallback: React.ReactNode;
  /** Optional callback for custom error handling */
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  /** Whether to enable automatic recovery attempts */
  enableRecovery?: boolean;
}

/**
 * State interface for the ErrorBoundary component
 */
interface ErrorBoundaryState {
  /** Whether an error has occurred */
  hasError: boolean;
  /** The error object if one exists */
  error: Error | null;
  /** Classification of the error type */
  errorType: ErrorType;
  /** Number of recovery attempts made */
  recoveryAttempts: number;
}

/**
 * A production-ready error boundary component that catches JavaScript errors,
 * logs them to CloudWatch, and provides recovery options.
 */
export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private readonly cloudWatchClient: CloudWatchClient;
  private readonly MAX_RECOVERY_ATTEMPTS = 3;

  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorType: ErrorType.UNKNOWN,
      recoveryAttempts: 0
    };

    // Initialize CloudWatch client
    this.cloudWatchClient = new CloudWatchClient({
      region: process.env.NEXT_PUBLIC_AWS_REGION || 'us-west-2'
    });

    // Bind methods
    this.attemptRecovery = this.attemptRecovery.bind(this);
    this.logErrorToCloudWatch = this.logErrorToCloudWatch.bind(this);
  }

  /**
   * Static method to derive error state from caught errors
   */
  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    // Classify error type based on error properties and message
    let errorType = ErrorType.UNKNOWN;
    
    if (error instanceof TypeError || error instanceof ReferenceError) {
      errorType = ErrorType.RUNTIME;
    } else if (error.message.toLowerCase().includes('network')) {
      errorType = ErrorType.NETWORK;
    } else if (error.message.toLowerCase().includes('resource')) {
      errorType = ErrorType.RESOURCE;
    }

    return {
      hasError: true,
      error,
      errorType
    };
  }

  /**
   * Lifecycle method called when an error occurs
   */
  async componentDidCatch(error: Error, errorInfo: React.ErrorInfo): Promise<void> {
    // Log error to CloudWatch
    await this.logErrorToCloudWatch(error, errorInfo);

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Show error toast to user
    Toast.show({
      type: 'error',
      title: 'An error occurred',
      message: 'We encountered an unexpected error. Our team has been notified.',
      duration: 5000
    });
  }

  /**
   * Logs error details to CloudWatch for monitoring
   */
  private async logErrorToCloudWatch(error: Error, errorInfo: React.ErrorInfo): Promise<void> {
    try {
      const command = new PutMetricDataCommand({
        Namespace: 'TransferRequirements/Errors',
        MetricData: [
          {
            MetricName: 'ClientError',
            Value: 1,
            Unit: 'Count',
            Dimensions: [
              {
                Name: 'ErrorType',
                Value: this.state.errorType
              },
              {
                Name: 'Component',
                Value: errorInfo.componentStack.split('\n')[1].trim()
              }
            ],
            Timestamp: new Date()
          }
        ]
      });

      await this.cloudWatchClient.send(command);
    } catch (cloudWatchError) {
      console.error('Failed to log error to CloudWatch:', cloudWatchError);
    }
  }

  /**
   * Attempts to recover from the error state
   */
  public attemptRecovery(): void {
    if (!this.props.enableRecovery || this.state.recoveryAttempts >= this.MAX_RECOVERY_ATTEMPTS) {
      return;
    }

    this.setState(prevState => ({
      hasError: false,
      error: null,
      errorType: ErrorType.UNKNOWN,
      recoveryAttempts: prevState.recoveryAttempts + 1
    }));

    // Log recovery attempt
    this.logErrorToCloudWatch(
      new Error('Recovery Attempt'),
      { componentStack: 'Recovery' } as React.ErrorInfo
    );
  }

  render(): React.ReactNode {
    if (this.state.hasError) {
      // Clone fallback element and inject error context and recovery handler
      return React.cloneElement(this.props.fallback as React.ReactElement, {
        error: this.state.error,
        errorType: this.state.errorType,
        onRetry: this.props.enableRecovery ? this.attemptRecovery : undefined,
        recoveryAttempts: this.state.recoveryAttempts,
        maxRecoveryAttempts: this.MAX_RECOVERY_ATTEMPTS
      });
    }

    return this.props.children;
  }
}

/**
 * Example usage:
 * 
 * <ErrorBoundary
 *   fallback={<ErrorFallback />}
 *   onError={(error, errorInfo) => {
 *     // Custom error handling
 *   }}
 *   enableRecovery={true}
 * >
 *   <YourComponent />
 * </ErrorBoundary>
 */