import React from 'react';

/**
 * Loading Component
 * Displays loading indicators with various styles and sizes
 * Replaces spinners and skeleton screens throughout the app
 */

export type LoadingSize = 'sm' | 'md' | 'lg' | 'xl';
export type LoadingStyle = 'spinner' | 'pulse' | 'skeleton' | 'progress';

interface LoadingProps {
  visible?: boolean;
  size?: LoadingSize;
  style?: LoadingStyle;
  message?: string;
  fullScreen?: boolean;
  overlay?: boolean;
}

const sizeClasses: Record<LoadingSize, string> = {
  sm: 'w-4 h-4',
  md: 'w-8 h-8',
  lg: 'w-12 h-12',
  xl: 'w-16 h-16',
};

/**
 * Spinner Loader - Rotating circular spinner
 */
export const SpinnerLoader: React.FC<{ size: LoadingSize }> = ({ size }) => {
  return (
    <div className={`${sizeClasses[size]} animate-spin`}>
      <svg
        className="w-full h-full text-blue-600"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
    </div>
  );
};

/**
 * Pulse Loader - Pulsing circle (subtle, modern)
 */
export const PulseLoader: React.FC<{ size: LoadingSize }> = ({ size }) => {
  return (
    <div className="flex items-center justify-center gap-1">
      <div
        className={`${sizeClasses[size]} rounded-full bg-blue-600 animate-pulse`}
      />
      <div
        className={`${sizeClasses[size]} rounded-full bg-blue-500 animate-pulse`}
        style={{ animationDelay: '0.2s' }}
      />
      <div
        className={`${sizeClasses[size]} rounded-full bg-blue-400 animate-pulse`}
        style={{ animationDelay: '0.4s' }}
      />
    </div>
  );
};

/**
 * Skeleton Loader - Placeholder shimmer effect
 */
export const SkeletonLoader: React.FC<{
  count?: number;
  circle?: boolean;
}> = ({ count = 3, circle = false }) => {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, idx) => (
        <div
          key={idx}
          className={`
            h-4 bg-gray-200 dark:bg-gray-700 animate-pulse
            ${circle ? 'rounded-full w-10' : 'rounded w-full'}
          `}
        />
      ))}
    </div>
  );
};

/**
 * Progress Bar - Linear progress indicator
 */
export const ProgressBar: React.FC<{ progress?: number; animated?: boolean }> = ({
  progress = 0,
  animated = true,
}) => {
  const normalizedProgress = Math.min(Math.max(progress, 0), 100);

  return (
    <div className="w-full h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
      <div
        className={`
          h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-all duration-500
          ${animated ? 'animate-pulse' : ''}
        `}
        style={{ width: `${normalizedProgress}%` }}
      />
    </div>
  );
};

/**
 * Main Loading Component
 * Unified interface for all loading states
 */
export const Loading: React.FC<LoadingProps> = ({
  visible = true,
  size = 'md',
  style = 'spinner',
  message,
  fullScreen = false,
  overlay = true,
}) => {
  if (!visible) return null;

  const loadingContent = (
    <div
      className={`
        flex flex-col items-center justify-center gap-4
        ${fullScreen ? 'min-h-screen' : 'p-8'}
      `}
    >
      {/* Loading Indicator */}
      {style === 'spinner' && <SpinnerLoader size={size} />}
      {style === 'pulse' && <PulseLoader size={size} />}
      {style === 'skeleton' && <SkeletonLoader count={5} />}

      {/* Loading Message */}
      {message && (
        <p
          className="
            text-center
            text-sm md:text-base
            text-gray-600 dark:text-gray-400
            animate-pulse
          "
        >
          {message}
        </p>
      )}

      {/* Default Message if not provided */}
      {!message && (style === 'spinner' || style === 'pulse') && (
        <p className="text-center text-sm md:text-base text-gray-600 dark:text-gray-400">
          Loading...
        </p>
      )}
    </div>
  );

  // Full screen overlay version
  if (fullScreen) {
    return (
      <div
        className={`
          fixed inset-0 z-50
          flex items-center justify-center
          ${overlay ? 'bg-black bg-opacity-30' : 'bg-transparent'}
          backdrop-blur-sm
        `}
      >
        {loadingContent}
      </div>
    );
  }

  // Inline version
  return <div className="flex justify-center">{loadingContent}</div>;
};

/**
 * Loading Skeleton Card - For skeleton loading of cards
 */
export const SkeletonCard: React.FC<{ count?: number }> = ({ count = 1 }) => {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, idx) => (
        <div
          key={idx}
          className="
            bg-gray-200 dark:bg-gray-700 animate-pulse
            rounded-lg p-4 md:p-6
            space-y-3
          "
        >
          {/* Title skeleton */}
          <div className="h-6 bg-gray-300 dark:bg-gray-600 rounded w-3/4" />

          {/* Content skeleton */}
          <div className="space-y-2">
            <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded" />
            <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-5/6" />
          </div>

          {/* Footer skeleton */}
          <div className="flex gap-2 pt-2">
            <div className="h-8 bg-gray-300 dark:bg-gray-600 rounded w-20" />
            <div className="h-8 bg-gray-300 dark:bg-gray-600 rounded w-20" />
          </div>
        </div>
      ))}
    </div>
  );
};

/**
 * Loading Button - Button with loading state
 */
export const LoadingButton: React.FC<{
  loading?: boolean;
  label: string;
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
}> = ({ loading = false, label, onClick, disabled = false, className = '' }) => {
  return (
    <button
      onClick={onClick}
      disabled={loading || disabled}
      className={`
        px-4 py-2 md:px-6 md:py-3
        min-h-[48px] md:min-h-auto
        bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400
        text-white font-medium
        rounded-lg
        flex items-center justify-center gap-2
        transition-colors duration-200
        disabled:cursor-not-allowed
        ${className}
      `}
    >
      {loading && <SpinnerLoader size="sm" />}
      <span>{loading ? 'Loading...' : label}</span>
    </button>
  );
};

/**
 * Loading Overlay - For wrapping content that's loading
 */
export const LoadingOverlay: React.FC<{
  loading: boolean;
  children: React.ReactNode;
  message?: string;
}> = ({ loading, children, message = 'Loading...' }) => {
  return (
    <div className="relative">
      {children}

      {loading && (
        <div
          className="
            absolute inset-0
            bg-white dark:bg-gray-900 bg-opacity-50 dark:bg-opacity-50
            backdrop-blur-sm
            flex items-center justify-center
            rounded-lg
            z-40
          "
        >
          <div className="flex flex-col items-center gap-3">
            <SpinnerLoader size="md" />
            <p className="text-sm md:text-base text-gray-700 dark:text-gray-300">
              {message}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Shimmer Animation CSS
 * Add to your CSS file for shimmer effect:
 * 
 * @keyframes shimmer {
 *   0% {
 *     background-position: -1000px 0;
 *   }
 *   100% {
 *     background-position: 1000px 0;
 *   }
 * }
 * 
 * .shimmer {
 *   animation: shimmer 2s infinite;
 *   background: linear-gradient(
 *     to right,
 *     #f6f7f8 0%,
 *     #edeef1 20%,
 *     #f6f7f8 40%,
 *     #f6f7f8 100%
 *   );
 *   background-size: 1000px 100%;
 * }
 */

export default Loading;
