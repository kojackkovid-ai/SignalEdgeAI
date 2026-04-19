import axios, { AxiosInstance } from 'axios';
import { addRetryInterceptor, logRetryStats } from './retry';

// Use Vite proxy in development for CORS handling
const API_BASE_URL = import.meta.env.DEV 
  ? '/api' 
  : (import.meta.env.VITE_API_URL 
      ? import.meta.env.VITE_API_URL 
      : '/api');

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 160000, // 160 second timeout by default for long-running requests
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add retry interceptor for automatic retries on transient failures
    addRetryInterceptor(this.client, {
      maxRetries: 3,
      retryDelay: 1000, // 1 second initial delay
      retryDelayMultiplier: 2, // exponential backoff: 1s, 2s, 4s
      retryableStatusCodes: [408, 429, 500, 502, 503, 504],
      retryableErrorCodes: [
        'ECONNABORTED',
        'ECONNREFUSED',
        'ENOTFOUND',
        'ENETUNREACH',
        'ETIMEDOUT',
        'ECONNRESET',
      ],
    });

    // Log retry statistics periodically (useful for monitoring)
    logRetryStats(this.client);

    // Add token to requests (but not for auth endpoints)
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('access_token');
      console.log('[API] Request to:', config.url);
      console.log('[API] Token in localStorage:', token ? `${token.substring(0, 20)}...` : 'NONE');
      
      // Don't require token for auth endpoints
      const isAuthEndpoint = config.url?.includes('/auth/');
      
      if (token && !isAuthEndpoint) {
        config.headers.Authorization = `Bearer ${token}`;
        console.log('[API] Authorization header set ✓');
      } else if (!isAuthEndpoint) {
        console.warn('[API] NO TOKEN FOUND - Request will fail auth');
      } else {
        console.log('[API] Auth endpoint - no token required ✓');
      }
      return config;
    });

    // Handle responses
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('access_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth
  async register(email: string, password: string, username: string) {
    const response = await this.client.post('/auth/register', {
      email,
      password,
      username,
    });
    return response.data;
  }

  async login(email: string, password: string) {
    const response = await this.client.post('/auth/login', {
      email,
      password,
    });
    return response.data;
  }

  async logout() {
    return this.client.post('/auth/logout');
  }

  // Users
  async getCurrentUser() {
    const response = await this.client.get('/users/me');
    return response.data;
  }

  async updateProfile(data: any) {
    const response = await this.client.put('/users/me', data);
    return response.data;
  }

  // Predictions
  async getPredictions(filters?: any) {
    try {
      const response = await this.client.get('/predictions/', {
        params: filters,
        timeout: 160000, // 160 second timeout - backend needs time to enrich from 7 sports in parallel
      });
      return response.data;
    } catch (error: any) {
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        console.error('Predictions endpoint timed out after 160 seconds');
        throw new Error('Predictions service is taking too long. Please try again.');
      }
      throw error;
    }
  }

  async getPrediction(id: string) {
    const response = await this.client.get(`/predictions/${id}`);
    return response.data;
  }

  async followPrediction(id: string, predictionData?: any, sportKey?: string, isClub100Pick?: boolean) {
    const config: any = {};
    if (sportKey || isClub100Pick !== undefined) {
      config.params = {};
      if (sportKey) {
        config.params.sport_key = sportKey;
      }
      if (isClub100Pick !== undefined) {
        config.params.is_club_100_pick = isClub100Pick;
      }
    }
    const response = await this.client.post(`/predictions/${id}/follow`, predictionData || {}, config);
    return response.data;
  }

  async unfollowPrediction(id: string) {
    return this.client.post(`/predictions/${id}/unfollow`);
  }

  async getUserStats() {
    const response = await this.client.get('/predictions/stats/user-stats');
    return response.data;
  }

  // Models
  async getModelsStatus() {
    const response = await this.client.get('/models/status');
    return response.data;
  }

  async getModelPerformance(modelName: string) {
    const response = await this.client.get(`/models/performance/${modelName}`);
    return response.data;
  }

  async triggerModelRetrain(modelName: string) {
    return this.client.post(`/models/retrain/${modelName}`);
  }

  async getModelBacktest(modelName: string, startDate: string, endDate: string) {
    const response = await this.client.get(`/models/backtest/${modelName}`, {
      params: { start_date: startDate, end_date: endDate },
    });
    return response.data;
  }

  // Player Props
  async getProps(sportKey: string, eventId: string) {
    const response = await this.client.get('/predictions/player-props', {
      params: {
        sport_key: sportKey,
        event_id: eventId,
      },
    });
    return response.data;
  }

  // Unified props endpoint - returns organized goals/assists/anytime_goal arrays
  async getFullGameProps(sportKey: string, eventId: string) {
    const response = await this.client.get(`/predictions/game/${sportKey}/${eventId}/full`);
    return response.data;
  }

  async getTier() {
    const response = await this.client.get('/users/tier');
    return response.data;
  }

  // Expose client methods for backward compatibility
  get(url: string, config?: any) {
    return this.client.get(url, config);
  }

  post(url: string, data?: any, config?: any) {
    return this.client.post(url, data, config);
  }

  put(url: string, data?: any, config?: any) {
    return this.client.put(url, data, config);
  }

  delete(url: string, config?: any) {
    return this.client.delete(url, config);
  }
}

export default new ApiClient();
