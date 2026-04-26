/**
 * Token Manager - Handles JWT token lifecycle and automatic refresh
 * Monitors token expiration and triggers refresh before expiry
 */

interface TokenPayload {
  sub: string;
  exp: number;
  iat?: number;
  [key: string]: any;
}

class TokenManager {
  private refreshThresholdMs = 5 * 60 * 1000; // Refresh 5 minutes before expiry
  private monitoringInterval: NodeJS.Timeout | null = null;
  private onTokenExpired: (() => void) | null = null;
  private onTokenRefreshed: ((token: string) => void) | null = null;

  /**
   * Decode JWT token without verification (client-side only)
   * Note: This is for UI purposes only - actual verification happens on backend
   */
  private decodeToken(token: string): TokenPayload | null {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) {
        console.warn('[TokenManager] Invalid token format - not 3 parts');
        return null;
      }

      // Decode the payload (second part)
      const decoded = JSON.parse(
        atob(parts[1].replace(/-/g, '+').replace(/_/g, '/'))
      );
      return decoded as TokenPayload;
    } catch (error) {
      console.error('[TokenManager] Failed to decode token:', error);
      return null;
    }
  }

  /**
   * Get token expiration time in milliseconds
   */
  getTokenExpirationTime(): number | null {
    const token = localStorage.getItem('access_token');
    if (!token) return null;

    const payload = this.decodeToken(token);
    if (!payload || !payload.exp) return null;

    // exp is in seconds, convert to milliseconds
    return payload.exp * 1000;
  }

  /**
   * Get time until token expiration in milliseconds
   */
  getTimeUntilExpiration(): number | null {
    const expirationTime = this.getTokenExpirationTime();
    if (!expirationTime) return null;

    const now = Date.now();
    const timeLeft = expirationTime - now;
    return timeLeft > 0 ? timeLeft : 0;
  }

  /**
   * Check if token exists and is not expired
   */
  isTokenValid(): boolean {
    const token = localStorage.getItem('access_token');
    if (!token) return false;

    const timeLeft = this.getTimeUntilExpiration();
    if (timeLeft === null) return false;

    return timeLeft > 0;
  }

  /**
   * Check if token is about to expire (within threshold)
   */
  isTokenExpiringsoon(): boolean {
    const timeLeft = this.getTimeUntilExpiration();
    if (timeLeft === null) return false;

    return timeLeft < this.refreshThresholdMs;
  }

  /**
   * Start monitoring token expiration
   * Checks token status every 30 seconds
   */
  startMonitoring(
    onExpired?: () => void,
    onRefreshed?: (token: string) => void
  ): void {
    this.onTokenExpired = onExpired || null;
    this.onTokenRefreshed = onRefreshed || null;

    // Clear any existing monitoring
    this.stopMonitoring();

    // Monitor every 30 seconds
    this.monitoringInterval = setInterval(() => {
      this.checkTokenStatus();
    }, 30000);

    console.log('[TokenManager] Started monitoring token expiration');

    // Do immediate check
    this.checkTokenStatus();
  }

  /**
   * Stop monitoring token expiration
   */
  stopMonitoring(): void {
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
      console.log('[TokenManager] Stopped monitoring token expiration');
    }
  }

  /**
   * Check current token status
   */
  private checkTokenStatus(): void {
    const token = localStorage.getItem('access_token');

    if (!token) {
      console.log('[TokenManager] No token found');
      this.stopMonitoring();
      return;
    }

    const timeLeft = this.getTimeUntilExpiration();
    if (timeLeft === null) {
      console.warn('[TokenManager] Could not decode token expiration');
      return;
    }

    const expirationMinutes = Math.round(timeLeft / 60000);
    console.log(
      `[TokenManager] Token expires in ${expirationMinutes} minutes`
    );

    // If token has expired
    if (timeLeft <= 0) {
      console.warn('[TokenManager] ⏰ Token has expired');
      this.stopMonitoring();
      if (this.onTokenExpired) {
        this.onTokenExpired();
      }
      localStorage.removeItem('access_token');
      return;
    }

    // If token is expiring soon
    if (timeLeft < this.refreshThresholdMs) {
      const refreshMinutes = Math.round(
        (this.refreshThresholdMs - timeLeft) / 60000
      );
      console.log(
        `[TokenManager] ⚠️ Token expiring in ${expirationMinutes} minutes - should be refreshed in ~${refreshMinutes} minutes`
      );
    }
  }

  /**
   * Get token info for debugging
   */
  getTokenInfo(): {
    exists: boolean;
    expiresAt: Date | null;
    expiresIn: string | null;
    isValid: boolean;
    isExpiringSoon: boolean;
  } {
    const expirationTime = this.getTokenExpirationTime();
    const timeLeft = this.getTimeUntilExpiration();

    let expiresIn = null;
    if (timeLeft !== null) {
      const minutes = Math.floor(timeLeft / 60000);
      const seconds = Math.floor((timeLeft % 60000) / 1000);
      expiresIn = `${minutes}m ${seconds}s`;
    }

    return {
      exists: !!localStorage.getItem('access_token'),
      expiresAt: expirationTime ? new Date(expirationTime) : null,
      expiresIn,
      isValid: this.isTokenValid(),
      isExpiringSoon: this.isTokenExpiringsoon(),
    };
  }

  /**
   * Clear token
   */
  clearToken(): void {
    localStorage.removeItem('access_token');
    this.stopMonitoring();
    console.log('[TokenManager] Token cleared');
  }

  /**
   * Set token
   */
  setToken(token: string): void {
    localStorage.setItem('access_token', token);
    console.log('[TokenManager] Token set');
    if (this.onTokenRefreshed) {
      this.onTokenRefreshed(token);
    }
  }
}

// Export singleton instance
export const tokenManager = new TokenManager();
