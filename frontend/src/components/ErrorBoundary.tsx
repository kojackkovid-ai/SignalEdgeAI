import React, { ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

/**
 * Error Boundary Component
 * Catches React errors and prevents app crashes
 * Shows a fallback UI when errors occur
 */
class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log error details for debugging
    console.error('ErrorBoundary caught an error:', error);
    console.error('Error Info:', errorInfo);

    // Update state with error details
    this.setState({
      error,
      errorInfo,
    });

    // Optionally send error to monitoring service
    this.logErrorToService(error, errorInfo);
  }

  logErrorToService = (error: Error, errorInfo: React.ErrorInfo) => {
    // Send error to your monitoring service (e.g., Sentry, LogRocket)
    // This is a placeholder - implement based on your monitoring solution
    try {
      const errorData = {
        message: error.toString(),
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
      };

      // Log to console in development
      if (process.env.NODE_ENV === 'development') {
        console.group('📋 Error Details for Monitoring');
        console.table(errorData);
        console.groupEnd();
      }

      // Optional: Send to monitoring service
      // await fetch('/api/errors/log', { method: 'POST', body: JSON.stringify(errorData) });
    } catch (logError) {
      console.error('Failed to log error:', logError);
    }
  };

  resetError = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          className="min-h-screen bg-gradient-to-br from-red-50 to-red-100 flex items-center justify-center p-4"
          role="alert"
          aria-live="assertive"
        >
          <div className="max-w-md w-full bg-white rounded-lg shadow-2xl p-8">
            {/* Error Icon */}
            <div className="text-center mb-6">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4">
                <svg
                  className="w-8 h-8 text-red-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4v2m0 -10V9m0 0H9m3 0h3m-6 0a9 9 0 1 1 0 18 9 9 0 0 1 0-18z"
                  />
                </svg>
              </div>

              {/* Error Heading */}
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                Oops! Something went wrong
              </h1>
              <p className="text-gray-600 text-sm mb-4">
                We're sorry for the inconvenience. The application encountered an unexpected error.
              </p>
            </div>

            {/* Error Details (Development Only) */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div className="mb-6 p-4 bg-gray-50 rounded border border-gray-200">
                <details className="text-xs text-gray-600">
                  <summary className="cursor-pointer font-semibold mb-2 text-gray-700">
                    ℹ️ Error Details (Development Only)
                  </summary>
                  <div className="space-y-2 mt-2">
                    <div>
                      <strong>Error:</strong>
                      <pre className="bg-gray-100 p-2 rounded mt-1 overflow-auto max-h-32 text-gray-700">
                        {this.state.error.toString()}
                      </pre>
                    </div>
                    {this.state.errorInfo && (
                      <div>
                        <strong>Component Stack:</strong>
                        <pre className="bg-gray-100 p-2 rounded mt-1 overflow-auto max-h-32 text-gray-700">
                          {this.state.errorInfo.componentStack}
                        </pre>
                      </div>
                    )}
                  </div>
                </details>
              </div>
            )}

            {/* Action Buttons */}
            <div className="space-y-3">
              <button
                onClick={this.resetError}
                className="w-full px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
              >
                Try Again
              </button>
              <button
                onClick={() => (window.location.href = '/')}
                className="w-full px-4 py-2 bg-gray-200 text-gray-800 font-medium rounded-lg hover:bg-gray-300 transition-colors"
              >
                Go to Home
              </button>
            </div>

            {/* Help Text */}
            <p className="text-center text-xs text-gray-500 mt-6">
              If this problem persists, please contact our support team.
            </p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
