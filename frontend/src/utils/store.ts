import { create } from 'zustand';

interface User {
  id: string;
  email: string;
  username: string;
  tier?: string;
  subscription_tier?: string;
  winRate: number;
  totalPredictions: number;
  roi: number;
}

interface AuthStore {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  token: localStorage.getItem('access_token'),
  isAuthenticated: !!localStorage.getItem('access_token'),
  
  setUser: (user) => set({ user }),
  
  setToken: (token) => {
    if (token) {
      localStorage.setItem('access_token', token);
    } else {
      localStorage.removeItem('access_token');
    }
    set({ token, isAuthenticated: !!token });
  },
  
  logout: () => {
    localStorage.removeItem('access_token');
    set({ user: null, token: null, isAuthenticated: false });
  },
}));

interface PredictionStore {
  predictions: any[];
  selectedPrediction: any | null;
  filters: any;
  setPredictions: (predictions: any[]) => void;
  setSelectedPrediction: (prediction: any | null) => void;
  setFilters: (filters: any) => void;
}

export const usePredictionStore = create<PredictionStore>((set) => ({
  predictions: [],
  selectedPrediction: null,
  filters: { sport: null, league: null, minConfidence: 0 },
  
  setPredictions: (predictions) => set({ predictions }),
  setSelectedPrediction: (prediction) => set({ selectedPrediction: prediction }),
  setFilters: (filters) => set({ filters }),
}));
