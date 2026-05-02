import { AxiosError, AxiosInstance } from 'axios';

export interface RetryConfig {
  maxRetries?: number;
  retryDelay?: number; // milliseconds
  retryDelayMultiplier?: number; // exponential backoff
  retryableStatusCodes?: number[];
  retryableErrorCodes?: string[];
  excludeUrls?: string[]; // URL substrings that should never be retried
}

/**
 * Default retry configuration
 */
export const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  retryDelay: 1000, // 1 second
  retryDelayMultiplier: 2, // exponential backoff: 1s, 2s, 4s
  retryableStatusCodes: [408, 500, 502, 503, 504], // Network and server errors (NOT 429 - don't retry rate limits)
  retryableErrorCodes: [
    'ECONNABORTED', // Connection aborted
    'ECONNREFUSED', // Connection refused
    'ENOTFOUND',    // DNS lookup failed
    'ENETUNREACH',  // Network unreachable
    'ETIMEDOUT',    // Connection timeout
    'ECONNRESET',   // Connection reset
  ],
};

/**
 * Check if an error is retryable
 */
export function isRetryableError(
  error: AxiosError,
  config: RetryConfig = DEFAULT_RETRY_CONFIG
): boolean {
  const { retryableStatusCodes = [], retryableErrorCodes = [] } = config;

  // Check HTTP status code
  if (error.response?.status) {
    if (retryableStatusCodes.includes(error.response.status)) {
      return true;
    }
  }

  // Check network error codes
  if (error.code && retryableErrorCodes.includes(error.code)) {
    return true;
  }

  // Check for timeout errors
  if (error.message?.includes('timeout')) {
    return true;
  }

  return false;
}

/**
 * Calculate delay for exponential backoff
 */
export function calculateRetryDelay(
  retryCount: number,
  baseDelay: number = DEFAULT_RETRY_CONFIG.retryDelay || 1000,
  multiplier: number = DEFAULT_RETRY_CONFIG.retryDelayMultiplier || 2
): number {
  return baseDelay * Math.pow(multiplier, retryCount);
}

/**
 * Add retry interceptor to axios instance
 * Automatically retries failed requests with exponential backoff
 */
export function addRetryInterceptor(
  axiosInstance: AxiosInstance,
  config: RetryConfig = DEFAULT_RETRY_CONFIG
): void {
  const {
    maxRetries = DEFAULT_RETRY_CONFIG.maxRetries || 3,
    retryDelay = DEFAULT_RETRY_CONFIG.retryDelay || 1000,
    retryDelayMultiplier = DEFAULT_RETRY_CONFIG.retryDelayMultiplier || 2,
    excludeUrls = [],
  } = config;

  // Add response interceptor for retries
  axiosInstance.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
      const axiosConfig = error.config as any;

      // Initialize retry count
      if (!axiosConfig._retryCount) {
        axiosConfig._retryCount = 0;
      }

      // Skip retry for excluded URLs (e.g. analytics events)
      const requestUrl = axiosConfig.url || '';
      const isExcluded = excludeUrls.some((pattern) => requestUrl.includes(pattern));

      // Check if we should retry
      if (
        !isExcluded &&
        axiosConfig._retryCount < maxRetries &&
        isRetryableError(error, config)
      ) {
        axiosConfig._retryCount += 1;

        // Calculate delay with exponential backoff
        const delay = calculateRetryDelay(
          axiosConfig._retryCount - 1,
          retryDelay,
          retryDelayMultiplier
        );

        // Log retry attempt
        const endpoint = axiosConfig.url || 'unknown endpoint';
        const statusCode = error.response?.status || 'N/A';
        const errorCode = error.code || 'unknown error';

        console.warn(
          `🔄 Retry attempt ${axiosConfig._retryCount}/${maxRetries} for ${endpoint} ` +
          `(${statusCode}/${errorCode}) - waiting ${delay}ms...`
        );

        // Wait before retrying
        await new Promise((resolve) => setTimeout(resolve, delay));

        // Retry the request
        try {
          return await axiosInstance(axiosConfig);
        } catch (retryError) {
          console.error(
            `❌ Retry ${axiosConfig._retryCount} failed for ${endpoint}`,
            retryError
          );
          return Promise.reject(retryError);
        }
      }

      // Max retries exceeded or not retryable
      if (axiosConfig._retryCount > 0) {
        const endpoint = axiosConfig.url || 'unknown endpoint';
        console.error(
          `❌ Failed after ${axiosConfig._retryCount} retries for ${endpoint}`
        );
      }

      return Promise.reject(error);
    }
  );
}

