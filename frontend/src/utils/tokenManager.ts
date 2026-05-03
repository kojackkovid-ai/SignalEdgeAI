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
  private monitoringInterval: ReturnType<typeof setInterval> | null = null;
  private onTokenExpired: (() => void) | null = null;
  private onTokenRefreshed: ((token: string) => void) | null = null;

  /**
   * Decode JWT token without verification (client-side only)
   * Note: This is for UI purposes only - actual verification happens on backend
   */
  private decodeToken(token: string): TokenPayload | null {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) return null;

      const decoded = JSON.parse(
        atob(parts[1].replace(/-/g, '+').replace(/_/g, '/'))
      );
      return decoded as TokenPayload;
    } catch {
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

    this.stopMonitoring();

    this.monitoringInterval = setInterval(() => {
      this.checkTokenStatus();
    }, 30000);

    this.checkTokenStatus();
  }

  /**
   * Stop monitoring token expiration
   */
  stopMonitoring(): void {
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }
  }

  /**
   * Check current token status
   */
  private checkTokenStatus(): void {
    const token = localStorage.getItem('access_token');

    if (!token) {
      this.stopMonitoring();
      return;
    }

    const timeLeft = this.getTimeUntilExpiration();
    if (timeLeft === null) return;

    if (timeLeft <= 0) {
      this.stopMonitoring();
      if (this.onTokenExpired) {
        this.onTokenExpired();
      }
      localStorage.removeItem('access_token');
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
  }

  /**
   * Set token
   */
  setToken(token: string): void {
    localStorage.setItem('access_token', token);
    if (this.onTokenRefreshed) {
      this.onTokenRefreshed(token);
    }
  }
}

// Export singleton instance
export const tokenManager = new TokenManager();
