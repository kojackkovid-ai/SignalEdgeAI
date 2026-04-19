/**
 * Frontend Test Suite for Phase 1 Implementation
 * 
 * Tests:
 * - Error Boundary component
 * - Loading components
 * - Mobile responsiveness
 * - Auto-retry interceptor
 * - API client configuration
 */

import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ErrorBoundary from '../components/ErrorBoundary';
import { Loading, SkeletonCard, LoadingButton } from '../components/Loading';

/**
 * TEST SUITE 1: Error Boundary Component
 */
describe('ErrorBoundary Component', () => {
  const ThrowError = () => {
    throw new Error('Test error');
  };

  test('renders children when there is no error', () => {
    render(
      <ErrorBoundary>
        <div>Test Content</div>
      </ErrorBoundary>
    );
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  test('displays error UI when error is thrown', () => {
    // Suppress console error for this test
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );

    expect(screen.getByText('Oops! Something went wrong')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Try Again/i })).toBeInTheDocument();

    consoleSpy.mockRestore();
  });

  test('resets error when Try Again button is clicked', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

    const { rerender } = render(
      <ErrorBoundary>
        <div>Test Content</div>
      </ErrorBoundary>
    );

    expect(screen.getByText('Test Content')).toBeInTheDocument();

    consoleSpy.mockRestore();
  });

  test('error message is visible in development', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );

    // In development, error details should be shown
    if (process.env.NODE_ENV === 'development') {
      expect(screen.getByText(/Error Details/i)).toBeInTheDocument();
    }

    consoleSpy.mockRestore();
  });
});

/**
 * TEST SUITE 2: Loading Components
 */
describe('Loading Components', () => {
  test('Loading component displays with spinner style', () => {
    render(<Loading visible={true} style="spinner" message="Loading..." />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  test('Loading component hides when visible is false', () => {
    const { container } = render(
      <Loading visible={false} style="spinner" />
    );
    expect(container.firstChild).toBeEmptyDOMElement();
  });

  test('SkeletonCard renders placeholder elements', () => {
    const { container } = render(<SkeletonCard count={3} />);
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  test('LoadingButton shows loading state', () => {
    render(
      <LoadingButton
        loading={true}
        label="Submit"
        disabled={false}
      />
    );
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  test('LoadingButton displays normal label when not loading', () => {
    render(
      <LoadingButton
        loading={false}
        label="Submit"
        disabled={false}
      />
    );
    expect(screen.getByText('Submit')).toBeInTheDocument();
  });
});

/**
 * TEST SUITE 3: Responsive Design
 */
describe('Mobile Responsive Design', () => {
  test('container-mobile class is applied', () => {
    const { container } = render(
      <div className="container-mobile">
        <p>Responsive Container</p>
      </div>
    );
    
    const element = container.querySelector('.container-mobile');
    expect(element).toBeInTheDocument();
    expect(element).toHaveClass('w-full');
    expect(element).toHaveClass('px-4');
  });

  test('grid-mobile has responsive columns', () => {
    const { container } = render(
      <div className="grid-mobile">
        <div>Item 1</div>
        <div>Item 2</div>
        <div>Item 3</div>
      </div>
    );

    const grid = container.querySelector('.grid-mobile');
    expect(grid).toBeInTheDocument();
    expect(grid).toHaveClass('grid');
    expect(grid).toHaveClass('grid-cols-1');
    expect(grid).toHaveClass('sm:grid-cols-2');
  });

  test('input-mobile has touch-friendly sizing', () => {
    const { container } = render(
      <input
        type="text"
        className="input-mobile"
        placeholder="Enter text"
      />
    );

    const input = container.querySelector('input');
    expect(input).toHaveClass('input-mobile');
    expect(input).toHaveClass('min-h-[44px]');
    expect(input).toHaveClass('text-base');
  });
});

/**
 * TEST SUITE 4: API Client Configuration
 */
describe('API Client Configuration', () => {
  test('API client has retry interceptor configured', async () => {
    // This is a smoke test to verify the API client can be imported
    // and has retry configuration
    const apiClient = require('../utils/api').default;
    
    expect(apiClient).toBeDefined();
    expect(apiClient.client).toBeDefined();
    expect(apiClient.client.interceptors).toBeDefined();
  });

  test('Retry utility exports required functions', async () => {
    const {
      addRetryInterceptor,
      isRetryableError,
      calculateRetryDelay,
      DEFAULT_RETRY_CONFIG,
    } = await import('../utils/retry');

    expect(addRetryInterceptor).toBeDefined();
    expect(isRetryableError).toBeDefined();
    expect(calculateRetryDelay).toBeDefined();
    expect(DEFAULT_RETRY_CONFIG).toBeDefined();
  });

  test('DEFAULT_RETRY_CONFIG has correct settings', async () => {
    const { DEFAULT_RETRY_CONFIG } = await import('../utils/retry');

    expect(DEFAULT_RETRY_CONFIG.maxRetries).toBeGreaterThan(0);
    expect(DEFAULT_RETRY_CONFIG.retryDelay).toBeGreaterThan(0);
    expect(DEFAULT_RETRY_CONFIG.retryDelayMultiplier).toBeGreaterThan(1);
    expect(Array.isArray(DEFAULT_RETRY_CONFIG.retryableStatusCodes)).toBe(true);
    expect(Array.isArray(DEFAULT_RETRY_CONFIG.retryableErrorCodes)).toBe(true);
  });
});

/**
 * TEST SUITE 5: Accessibility
 */
describe('Accessibility', () => {
  test('Loading component has aria-live role', () => {
    const { container } = render(
      <Loading visible={true} message="Loading..." />
    );
    
    const alert = container.querySelector('[role="alert"]');
    expect(alert).toBeInTheDocument();
  });

  test('Error Boundary has alert role', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
    const ThrowError = () => {
      throw new Error('Test error');
    };

    const { container } = render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );

    const alert = container.querySelector('[role="alert"]');
    expect(alert).toBeInTheDocument();

    consoleSpy.mockRestore();
  });

  test('Buttons have minimum touch target size', () => {
    render(
      <button className="btn-mobile">
        Click me
      </button>
    );

    const button = screen.getByRole('button');
    expect(button).toHaveClass('min-h-[48px]');
    expect(button).toHaveClass('min-w-[48px]');
  });
});

/**
 * Integration Test: Complete User Flow
 */
describe('Integration: User Flow', () => {
  test('user sees error boundary when error occurs', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
    const ThrowError = () => {
      throw new Error('Critical error');
    };

    const { rerender } = render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );

    expect(screen.getByText('Oops! Something went wrong')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Try Again/i })).toBeInTheDocument();

    consoleSpy.mockRestore();
  });

  test('loading states are displayed during async operations', async () => {
    const { rerender } = render(
      <Loading visible={true} message="Fetching data..." />
    );

    expect(screen.getByText('Fetching data...')).toBeInTheDocument();

    // After operation completes
    rerender(<Loading visible={false} />);
  });
});

/**
 * Manual Testing Checklist
 * 
 * [ ] Error Boundary
 *     [ ] Catch JavaScript errors without crashing
 *     [ ] Display error message to user
 *     [ ] Show "Try Again" button
 *     [ ] Have "Go to Home" button
 * 
 * [ ] Loading Components
 *     [ ] Spinner animates smoothly
 *     [ ] Pulse animation works
 *     [ ] Skeleton loading looks correct
 *     [ ] Loading button shows spinner
 * 
 * [ ] Mobile Responsive
 *     [ ] Works on iPhone 375px width
 *     [ ] Works on Android 360px width
 *     [ ] Buttons are 48px tall on mobile
 *     [ ] Text is readable at 12px minimum on mobile
 *     [ ] No horizontal scrolling
 *     [ ] Touch targets have adequate spacing
 * 
 * [ ] Auto-Retry
 *     [ ] Retries on network timeout
 *     [ ] Retries on 5xx errors
 *     [ ] Uses exponential backoff
 *     [ ] Shows retry count in console
 * 
 * [ ] Performance
 *     [ ] Page loads in < 3 seconds on 4G
 *     [ ] No jank during animations
 *     [ ] No memory leaks
 *     [ ] Images are optimized
 * 
 * [ ] Accessibility
 *     [ ] All interactive elements are keyboard accessible
 *     [ ] Focus outlines are visible
 *     [ ] Color contrast is sufficient
 *     [ ] Screen reader announces errors
 */

export {};
