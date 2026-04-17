/**
 * Analytics Tracker - Frontend event logging
 * Sends events to backend for tracking user behavior
 */

import api from './api';

export interface AnalyticsEventData {
  [key: string]: any;
}

class AnalyticsTracker {
  private sessionId: string;

  constructor() {
    // Generate or retrieve session ID
    this.sessionId = this.getOrCreateSessionId();
  }

  /**
   * Get or create a session ID stored in localStorage
   */
  private getOrCreateSessionId(): string {
    const stored = localStorage.getItem('analytics_session_id');
    if (stored) {
      return stored;
    }
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('analytics_session_id', newSessionId);
    return newSessionId;
  }

  /**
   * Track an event
   */
  async trackEvent(
    eventType: string,
    eventData?: AnalyticsEventData,
    userId?: string
  ): Promise<void> {
    try {
      // Get user ID from localStorage if not provided
      const userStorageId = userId || localStorage.getItem('user_id');

      // Get device info
      const userAgent = navigator.userAgent;
      const requestDurationMs = performance.now();

      // Send to backend (non-blocking)
      api.post('/analytics/event', {
        event_type: eventType,
        event_data: eventData || {},
        session_id: this.sessionId,
        user_id: userStorageId,
        user_agent: userAgent,
        request_duration_ms: requestDurationMs,
      }).catch((error) => {
        // Silently log errors - don't interrupt user experience
        console.debug('Analytics event failed:', error);
      });
    } catch (error) {
      console.debug('Error tracking event:', error);
    }
  }

  // === Convenience Methods ===

  async trackSignup(email: string): Promise<void> {
    await this.trackEvent('signup', { email });
  }

  async trackLogin(userId: string): Promise<void> {
    await this.trackEvent('login', { user_id: userId }, userId);
  }

  async trackLogout(userId: string): Promise<void> {
    await this.trackEvent('logout', { user_id: userId }, userId);
  }

  async trackPredictionView(
    userId: string,
    sportKey: string,
    predictionId: string
  ): Promise<void> {
    await this.trackEvent(
      'prediction_view',
      { sport_key: sportKey, prediction_id: predictionId },
      userId
    );
  }

  async trackPredictionUnlock(
    userId: string,
    predictionId: string,
    cost: number
  ): Promise<void> {
    await this.trackEvent(
      'prediction_unlock',
      { prediction_id: predictionId, cost },
      userId
    );
  }

  async trackTierUpgrade(
    userId: string,
    newTier: string,
    price: number
  ): Promise<void> {
    await this.trackEvent(
      'tier_upgrade',
      { new_tier: newTier, price },
      userId
    );
  }

  async trackPaymentAttempt(
    userId: string,
    amount: number,
    tier: string
  ): Promise<void> {
    await this.trackEvent(
      'payment_attempt',
      { amount, tier },
      userId
    );
  }

  async trackPaymentComplete(
    userId: string,
    amount: number,
    tier: string,
    transactionId: string
  ): Promise<void> {
    await this.trackEvent(
      'payment_complete',
      { amount, tier, transaction_id: transactionId },
      userId
    );
  }

  async trackPaymentFailed(
    userId: string,
    amount: number,
    error: string
  ): Promise<void> {
    await this.trackEvent(
      'payment_failed',
      { amount, error },
      userId
    );
  }

  async trackPropsView(
    userId: string,
    sportKey: string,
    propType: string
  ): Promise<void> {
    await this.trackEvent(
      'props_view',
      { sport_key: sportKey, prop_type: propType },
      userId
    );
  }

  async trackAccuracyDashboardView(userId: string): Promise<void> {
    await this.trackEvent(
      'accuracy_dashboard_view',
      {},
      userId
    );
  }

  async trackChurn(
    userId: string,
    reason?: string
  ): Promise<void> {
    await this.trackEvent(
      'churn',
      { reason },
      userId
    );
  }

  async trackPageView(
    userId: string,
    page: string,
    props?: AnalyticsEventData
  ): Promise<void> {
    await this.trackEvent(
      'page_view',
      { page, ...props },
      userId
    );
  }
}

// Export singleton instance
export const analyticsTracker = new AnalyticsTracker();

export default AnalyticsTracker;
