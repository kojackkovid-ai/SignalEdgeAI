import axios, { AxiosInstance } from 'axios';
import { addRetryInterceptor } from './retry';
import { useAuthStore } from './store';

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
      timeout: 160000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add retry interceptor — skip analytics/event endpoint to avoid spam
    addRetryInterceptor(this.client, {
      maxRetries: 3,
      retryDelay: 1000,
      retryDelayMultiplier: 2,
      retryableStatusCodes: [408, 502, 503, 504],
      retryableErrorCodes: [
        'ECONNABORTED',
        'ECONNREFUSED',
        'ENOTFOUND',
        'ENETUNREACH',
        'ETIMEDOUT',
        'ECONNRESET',
      ],
      excludeUrls: ['/analytics/event'],
    });

    // Add token to requests (but not for auth endpoints)
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('access_token');
      const isAuthEndpoint = config.url?.includes('/auth/');

      if (token && !isAuthEndpoint) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Handle responses with automatic token refresh on 401
    let isRefreshing = false;
    let refreshSubscribers: Array<(token: string) => void> = [];

    const onRefreshed = (token: string) => {
      refreshSubscribers.forEach(callback => callback(token));
      refreshSubscribers = [];
    };

    const addRefreshSubscriber = (callback: (token: string) => void) => {
      refreshSubscribers.push(callback);
    };

    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        // Handle 401 Unauthorized - attempt token refresh
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          if (!isRefreshing) {
            isRefreshing = true;

            try {
              const refreshClient = axios.create({
                baseURL: API_BASE_URL,
                timeout: 10000,
                headers: { 'Content-Type': 'application/json' },
              });

              const token = localStorage.getItem('access_token');
              if (token) {
                refreshClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
              }

              const response = await refreshClient.post('/auth/refresh');
              const newToken = response.data.access_token;

              localStorage.setItem('access_token', newToken);
              this.client.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
              useAuthStore.getState().setToken(newToken);
              onRefreshed(newToken);
              isRefreshing = false;

              originalRequest.headers.Authorization = `Bearer ${newToken}`;
              return this.client(originalRequest);
            } catch (refreshError) {
              console.warn('[Auth] Session expired — please log in again');
              localStorage.removeItem('access_token');
              isRefreshing = false;
              refreshSubscribers = [];
              window.location.href = '/login';
              return Promise.reject(refreshError);
            }
          } else {
            return new Promise((resolve) => {
              addRefreshSubscriber((token: string) => {
                originalRequest.headers.Authorization = `Bearer ${token}`;
                resolve(this.client(originalRequest));
              });
            });
          }
        }

        // For other 401 errors without retry attempt
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
        timeout: 160000,
      });
      return response.data;
    } catch (error: any) {
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
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
