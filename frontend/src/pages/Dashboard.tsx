import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';
import { useAuthStore } from '../utils/store';
import { analyticsTracker } from '../utils/analytics';
import PredictionCard from '../components/PredictionCard';
import PropsTab from '../components/PropsTab';
import Club100UnlockModal from '../components/Club100UnlockModal';
import Club100Display from '../components/Club100Display';
import AccuracyDashboard from '../components/AccuracyDashboard';

const Dashboard = (): JSX.Element | null => {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuthStore();
  
  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isAuthenticated || !user) {
      navigate('/login');
    }
  }, [isAuthenticated, user, navigate]);

  // Dashboard Sport Key Union Type
  type SportKey = 
    | 'basketball_nba'
    | 'americanfootball_nfl'
    | 'baseball_mlb'
    | 'icehockey_nhl'
    | 'basketball_ncaa'
    | 'soccer_epl'
    | 'soccer_usa_mls'
    | 'soccer_esp.1'
    | 'soccer_ita.1'
    | 'soccer_ger.1'
    | 'soccer_fra.1';

  // Debug: Log authentication status on mount
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    console.log('[Dashboard] Mount - Token in storage:', token ? `${token.substring(0, 20)}...` : 'NONE');
    console.log('[Dashboard] isAuthenticated:', isAuthenticated);
    console.log('[Dashboard] user:', user?.id);
    
    // Track dashboard page view
    if (user?.id) {
      analyticsTracker.trackPageView(user.id, 'dashboard').catch(() => {});
    }
  }, [user?.id]);

  const sportTabOptions: { key: SportKey | 'soccer' | 'ncaab'; label: string }[] = [
    { key: 'basketball_nba', label: 'NBA' },
    { key: 'americanfootball_nfl', label: 'NFL' },
    { key: 'baseball_mlb', label: 'MLB' },
    { key: 'icehockey_nhl', label: 'NHL' },
    { key: 'basketball_ncaa', label: 'NCAAB' }
  ];

  const soccerTabOptions: { key: SportKey; label: string }[] = [
    { key: 'soccer_epl', label: '⚽ EPL' },
    { key: 'soccer_usa_mls', label: '⚽ MLS' },
    { key: 'soccer_esp.1', label: '⚽ La Liga' },
    { key: 'soccer_ita.1', label: '⚽ Serie A' },
    { key: 'soccer_ger.1', label: '⚽ Bundesliga' },
    { key: 'soccer_fra.1', label: '⚽ Ligue 1' }
  ];

  const [stats, setStats] = useState({ winRate: 0, predictions: 0, avgConfidence: 0, roi: 0 });
  const [activeTab, setActiveTab] = useState<SportKey>('basketball_nba');
  const [propsViewMode, setPropsViewMode] = useState<'player' | 'team'>('player');
  const [currentPage, setCurrentPage] = useState<'predictions' | 'accuracy'>('predictions');

  // Sport key map fallback for compatibility with older legacy 'short keys'
  const legacySportKeyMap: Record<string, SportKey> = {
    mlb: 'baseball_mlb',
    nfl: 'americanfootball_nfl',
    nba: 'basketball_nba',
    ncaab: 'basketball_ncaa',
    nhl: 'icehockey_nhl',
    soccer: 'soccer_epl'
  };
  
  const [predictions, setPredictions] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [pickCount, setPickCount] = useState(0);
  const [pickLimit, setPickLimit] = useState(1);
  const [userTier, setUserTier] = useState('starter');
  const [loading, setLoading] = useState(false);
  
  // Drill-down state
  const [viewMode, setViewMode] = useState<'list' | 'detail'>('list');
  const [selectedGame, setSelectedGame] = useState<any | null>(null);
  const [gameProps, setGameProps] = useState<any[]>([]);

  const [unlockingId, setUnlockingId] = useState<string | null>(null);
  
  // Club 100 Feature State
  const [club100Status, setClub100Status] = useState<any | null>(null);
  const [club100PlatformMetrics, setClub100PlatformMetrics] = useState<any | null>(null);
  const [showClub100Modal, setShowClub100Modal] = useState(false);
  const [showClub100Display, setShowClub100Display] = useState(false);
  const [_club100Loading, setClub100Loading] = useState(false);
  
  // New unified props state
  const [goalsProps, setGoalsProps] = useState<any[]>([]);
  const [assistsProps, setAssistsProps] = useState<any[]>([]);
  const [anytimeGoalProps, setAnytimeGoalProps] = useState<any[]>([]);
  const [teamProps, setTeamProps] = useState<any[]>([]);  // Game totals + anytime goal team
  const [otherProps, setOtherProps] = useState<any[]>([]);  // NBA/MLB other market types
  const [anytimeGoalScorers, setAnytimeGoalScorers] = useState<any>(null);  // Anytime goal scorers with player names
  
  // Cache for predictions with timestamp to enable stale-while-revalidate pattern
  // Cache structure: { sportKey: { data: any[], timestamp: number } }
  const predictionsCache = React.useRef<Record<string, { data: any[], timestamp: number }>>({});
  
  // Cache expiration time: 30 minutes (1800000 ms) - shows cached data instantly, background refreshes frequently
  const CACHE_EXPIRATION_MS = 30 * 60 * 1000;
  
  // Background refresh time: 5 minutes - fetches fresh data in background without blocking UI
  const BACKGROUND_REFRESH_MS = 5 * 60 * 1000;
  
  // Initialize cache from localStorage on mount
  React.useEffect(() => {
    try {
      const storedCache = localStorage.getItem('predictionsCache');
      if (storedCache) {
        const parsed = JSON.parse(storedCache);
        // Check if cache uses old sport key format (short keys like 'nba')
        const hasOldKeys = Object.keys(parsed).some(key => !key.includes('_'));
        if (hasOldKeys) {
          console.log('[Dashboard] Detected old cache format, clearing cache');
          localStorage.removeItem('predictionsCache');
          predictionsCache.current = {};
        } else {
          predictionsCache.current = parsed;
          console.log('[Dashboard] Loaded cache from localStorage:', Object.keys(parsed));
        }
      }
    } catch (e) {
      console.error('[Dashboard] Error loading cache from localStorage:', e);
      // Clear corrupted cache
      localStorage.removeItem('predictionsCache');
      predictionsCache.current = {};
    }
  }, []);
  
  // Helper to check if cache is valid (not expired)
  const isCacheValid = (sportKey: string): boolean => {
    const cached = predictionsCache.current[sportKey];
    if (!cached) return false;
    return Date.now() - cached.timestamp < CACHE_EXPIRATION_MS;
  };
  
  // Helper to check if cache needs background refresh
  const needsBackgroundRefresh = (sportKey: string): boolean => {
    const cached = predictionsCache.current[sportKey];
    if (!cached) return true;
    return Date.now() - cached.timestamp > BACKGROUND_REFRESH_MS;
  };
  
  // Helper to save cache to localStorage
  const saveCacheToStorage = () => {
    try {
      localStorage.setItem('predictionsCache', JSON.stringify(predictionsCache.current));
    } catch (e) {
      console.error('[Dashboard] Error saving cache to localStorage:', e);
    }
  };

  // Tier configuration with correct daily limits
  const tierConfig = {
    starter: { name: 'Starter', dailyLimit: 1, color: 'gray', showOdds: false, showReasoning: false, showModels: false, showLine: false },
    basic: { name: 'Basic', dailyLimit: 50, color: 'blue', showOdds: true, showReasoning: true, showModels: false, showLine: true },
    pro: { name: 'Pro', dailyLimit: 9999, color: 'purple', showOdds: true, showReasoning: true, showModels: true, showLine: true },
    pro_plus: { name: 'Pro Plus', dailyLimit: 9999, color: 'orange', showOdds: true, showReasoning: true, showModels: true, showLine: true },
    elite: { name: 'Elite', dailyLimit: 9999, color: 'gold', showOdds: true, showReasoning: true, showModels: true, showLine: true }
  };

  useEffect(() => {
    // Only fetch predictions if user is authenticated
    if (!isAuthenticated || !user) {
      return;
    }

    const fetchData = async (forceRefresh = false) => {
      // Check if we have valid cached data
      if (!forceRefresh && isCacheValid(activeTab)) {
        const cacheAge = Math.round((Date.now() - predictionsCache.current[activeTab].timestamp) / 60000);
        console.log('[Dashboard] Using cached predictions for', activeTab, '- Count:', predictionsCache.current[activeTab].data.length, '- Age:', cacheAge + ' minutes');
        setPredictions(predictionsCache.current[activeTab].data);
        setLoading(false);
        
        // Trigger background refresh if cache is getting stale
        if (needsBackgroundRefresh(activeTab)) {
          console.log('[Dashboard] Background refresh triggered for', activeTab);
          fetchData(true); // Force refresh without blocking UI
        }
        return;
      }
      
      setLoading(!isCacheValid(activeTab)); // Only show loading spinner if no cached data
      try {
        const canonicalSportKey = legacySportKeyMap[activeTab] || activeTab;
        console.log('[Dashboard] Fetching predictions for sport:', canonicalSportKey);
        
        // Use the api utility which properly attaches auth tokens
        const data = await api.getPredictions({ sport: canonicalSportKey, limit: 20 });
        
        console.log('[Dashboard] Raw API response:', data);
        console.log('[Dashboard] Response type:', typeof data);
        console.log('[Dashboard] Is array:', Array.isArray(data));
        
        // Handle both array response and object with predictions key
        let predictionsList = [];
        if (Array.isArray(data)) {
          predictionsList = data;
        } else if (data && data.predictions) {
          predictionsList = data.predictions;
        } else if (data && Array.isArray(data.predictions)) {
          predictionsList = data.predictions;
        }
        
        console.log('[Dashboard] Processed predictions list:', predictionsList.length, predictionsList);
        
        if (predictionsList.length > 0) {
          // Cache the predictions with timestamp
          predictionsCache.current[activeTab] = {
            data: predictionsList,
            timestamp: Date.now()
          };
          saveCacheToStorage(); // Persist to localStorage
          setPredictions(predictionsList);
          console.log('[Dashboard] Cached and displayed predictions for:', activeTab);
        } else {
          console.log('[Dashboard] No predictions found, setting empty array');
          setPredictions([]);
        }
      } catch (err: any) {
        console.error('[Dashboard] Error fetching predictions:', err);
        console.error('[Dashboard] Error details:', err.message);
        
        // If fetch fails but we have cached data, use it
        if (isCacheValid(activeTab)) {
          console.log('[Dashboard] Fetch failed, using cached data fallback');
          setPredictions(predictionsCache.current[activeTab].data);
        } else {
          setError(`Failed to load predictions: ${err.message}`);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [activeTab, isAuthenticated, user]);

  // Fetch user stats
  useEffect(() => {
    if (!isAuthenticated || !user) return;
    
    const fetchStats = async () => {
      try {
        const response = await api.get('/users/stats');
        if (response.data) {
          // Map backend response to component state
          const mappedStats = {
            winRate: response.data.win_rate || 0,
            predictions: response.data.total_predictions || 0,
            avgConfidence: response.data.avg_confidence || 0,  // Changed from profit to avgConfidence
            roi: response.data.roi || 0
          };
          setStats(mappedStats);
        }
      } catch (err) {
        console.error('Error fetching stats:', err);
      }
    };

    fetchStats();
  }, [isAuthenticated, user]);

  // Fetch user tier info
  useEffect(() => {
    if (!isAuthenticated || !user) return;
    
    const fetchTierInfo = async () => {
      try {
        console.log('[Dashboard] Fetching tier info from /users/tier');
        const response = await api.getTier();
        console.log('[Dashboard] Full tier response:', response);
        console.log('[Dashboard] Response.data:', response);
        
        // Handle tier data - response is already the data object from getTier()
        if (response && typeof response === 'object') {
          const tierValue = response.tier || 'starter';
          const dailyLimitValue = response.daily_limit;
          const picksUsedValue = response.picks_used_today || 0;
          const isUnlimited = response.is_unlimited || tierValue === 'elite' || tierValue === 'pro_plus';
          
          console.log('[Dashboard] Extracted tier:', tierValue, 'limit:', dailyLimitValue, 'used:', picksUsedValue, 'unlimited:', isUnlimited);
          console.log('[Dashboard] Tier "' + tierValue + '" should have limit:', tierConfig[tierValue as keyof typeof tierConfig]?.dailyLimit);
          
          setUserTier(tierValue);
          // Update auth store with new tier
          if (user) {
            const updatedUser = { ...user, tier: tierValue, subscription_tier: tierValue };
            // Note: We don't modify the global store here to avoid side effects
            // The main auth store tier is updated via Payment component
          }
          
          // Use the tier config limit (now has correct unlimited values for pro, pro_plus, and elite)
          const limitToSet = tierConfig[tierValue as keyof typeof tierConfig]?.dailyLimit || 1;
          
          console.log('[Dashboard] Applied tier limit for "' + tierValue + '":', limitToSet);
          setPickLimit(limitToSet);
          setPickCount(picksUsedValue);
        } else {
          console.warn('[Dashboard] Unexpected tier response format:', response);
        }
      } catch (err: any) {
        console.error('[Dashboard] Error fetching tier info:', err);
        console.error('[Dashboard] Error response:', err.response?.data);
        // Fallback to starter tier
        setUserTier('starter');
        setPickLimit(1);
      }
    };

    // Always fetch fresh tier info when component mounts or when user changes
    fetchTierInfo();
  }, [isAuthenticated, user, tierConfig]);

  const handleTabChange = (tab: SportKey) => {
    // DO NOT clear cache - just switch tab, cache will be used if valid
    setActiveTab(tab);
    setViewMode('list');
    setSelectedGame(null);
  };

  const handleGameClick = async (game: any) => {
    setSelectedGame(game);
    setViewMode('detail');
    setPropsViewMode('player');  // Reset to player props when selecting a new game
    setLoading(true);
    
    try {
      // Fetch unified props for this game
      console.log('[Dashboard] Fetching unified props for:', game.sport_key, game.event_id);
      const fullProps = await api.getFullGameProps(game.sport_key, game.event_id);
      console.log('[Dashboard] Full game props response:', fullProps);
      
      // Parse the response
      if (fullProps && typeof fullProps === 'object') {
        setGoalsProps(fullProps.goals || []);
        setAssistsProps(fullProps.assists || []);
        setAnytimeGoalProps(fullProps.anytime_goal || []);
        setTeamProps(fullProps.team_props || []);  // Game totals + anytime goal team
        setOtherProps(fullProps.other_props || []);  // NBA/MLB other market types
        setAnytimeGoalScorers(fullProps.anytime_goal_scorers || null);  // 2 scorers per team with names
        
        // Also keep gameProps for backward compatibility with the old view
        // Include both player and team props and other props
        const allProps = [
          ...(fullProps.goals || []), 
          ...(fullProps.assists || []), 
          ...(fullProps.anytime_goal || []),
          ...(fullProps.team_props || []),
          ...(fullProps.other_props || [])
        ];
        setGameProps(allProps);
        
        console.log('[Dashboard] Organized props - Goals:', fullProps.goals?.length || 0, 
                    'Assists:', fullProps.assists?.length || 0, 
                    'Anytime Goal:', fullProps.anytime_goal?.length || 0,
                    'Team Props:', fullProps.team_props?.length || 0,
                    'Other Props:', fullProps.other_props?.length || 0);
      } else {
        console.log('[Dashboard] Unexpected response format:', fullProps);
        setGoalsProps([]);
        setAssistsProps([]);
        setAnytimeGoalProps([]);
        setTeamProps([]);
        setOtherProps([]);
        setAnytimeGoalScorers(null);
        setGameProps([]);
      }
    } catch (err) {
      console.error('Error fetching full game props:', err);
      // Fallback to empty props
      setGoalsProps([]);
      setAssistsProps([]);
      setAnytimeGoalProps([]);
      setTeamProps([]);
      setOtherProps([]);
      setGameProps([]);
    } finally {
      setLoading(false);
    }
  };

  const handleBackToList = () => {
    setViewMode('list');
    setSelectedGame(null);
    setGameProps([]);
    setGoalsProps([]);
    setAssistsProps([]);
    setAnytimeGoalProps([]);
    setTeamProps([]);
    setOtherProps([]);
  };

  const handleUnlockGame = async (gameId: string) => {
    if (pickCount >= pickLimit) {
      alert(`You've reached your daily limit of ${pickLimit} picks. Upgrade your tier for more picks.`);
      return;
    }

    if (!selectedGame) {
      alert('Error: Game data not found. Please refresh and try again.');
      return;
    }

    try {
      // Pass the complete game data to the API
      const predictionData = {
        id: gameId,
        sport_key: selectedGame.sport_key,
        event_id: selectedGame.event_id,
        prediction: selectedGame.prediction,
        prediction_type: selectedGame.prediction_type || 'moneyline',
        confidence: selectedGame.confidence,
        matchup: selectedGame.matchup,
        game_time: selectedGame.game_time,
        reasoning: selectedGame.reasoning,
        models: selectedGame.models
      };
      
      console.log('[Dashboard] Unlocking game with data:', predictionData);
      
      const response = await api.followPrediction(gameId, predictionData, selectedGame.sport_key);
      if (response) {
        // Update the selected game state
        setSelectedGame((prev: any) => ({ ...prev, is_locked: false }));
        setPickCount((prev: number) => prev + 1);
        
        // CRITICAL: Update the cached predictions list so the prediction shows as unlocked everywhere
        const updatedPredictions = predictions.map((pred: any) => {
          if (pred.id === gameId) {
            console.log('[Dashboard] Updated prediction in cache - marked as unlocked:', gameId);
            return { ...pred, is_locked: false };
          }
          return pred;
        });
        
        // Update both state and cache
        setPredictions(updatedPredictions);
        predictionsCache.current[activeTab] = {
          data: updatedPredictions,
          timestamp: predictionsCache.current[activeTab]?.timestamp || Date.now()
        };
        saveCacheToStorage(); // Persist to localStorage
        
        console.log('[Dashboard] Successfully unlocked prediction:', gameId);
        alert('Pick unlocked! You now have access to this prediction.');
      }
    } catch (err: any) {
      console.error('[Dashboard] Error unlocking game:', err);
      console.error('[Dashboard] Error details:', {
        message: err.message,
        response: err.response,
        status: err.response?.status,
        statusText: err.response?.statusText,
        data: err.response?.data
      });
      
      // More specific error message
      let errorMsg = 'Failed to unlock game pick. ';
      if (err.response?.status === 404) {
        errorMsg += 'Endpoint not found. Please refresh the page.';
      } else if (err.response?.status === 401) {
        errorMsg += 'Session expired. Please log in again.';
      } else if (err.response?.status === 403) {
        errorMsg += 'Daily limit reached. Upgrade your tier for more picks.';
      } else if (err.response?.data?.detail) {
        errorMsg += err.response.data.detail;
      } else {
        errorMsg += 'Please try again.';
      }
      alert(errorMsg);
    }
  };


  const handleUnlockProp = async (propId: string) => {
    if (pickCount >= pickLimit) {
      alert(`You've reached your daily limit of ${pickLimit} picks. Upgrade your tier for more picks.`);
      return;
    }

    // Find the full prop data from gameProps
    const propData = gameProps.find((p: any) => p.id === propId);
    if (!propData) {
      console.error('[Dashboard] Prop not found:', propId);
      console.error('[Dashboard] Available props:', gameProps.map((p: any) => p?.id));
      alert('Error: Prop data not found. Please refresh and try again.');
      return;
    }

    console.log('[Dashboard] Starting unlock for prop:', propId, propData);
    setUnlockingId(propId);
    
    try {
      // Pass the complete prop data to the API
      const predictionData = {
        id: propId,
        sport_key: selectedGame?.sport_key,
        event_id: selectedGame?.event_id,
        player: propData.player,
        market_key: propData.market_key,
        point: propData.point,
        prediction: propData.prediction,
        prediction_type: propData.prediction_type || 'player_prop',
        confidence: propData.confidence,
        odds: propData.odds,
        matchup: propData.matchup || selectedGame?.matchup,
        reasoning: propData.reasoning,
        models: propData.models
      };
      
      console.log('[Dashboard] Unlocking prop with data:', predictionData);
      
      // Use the follow endpoint with complete prop data
      const response = await api.followPrediction(propId, predictionData, selectedGame?.sport_key);
      console.log('[Dashboard] Unlock prop raw response:', response);
      console.log('[Dashboard] Unlock prop response type:', typeof response);
      console.log('[Dashboard] Unlock prop response keys:', response ? Object.keys(response) : 'none');
      console.log('[Dashboard] Anytime goal names in response:', response?.anytime_goal_names);
      console.log('[Dashboard] Anytime goal scorers in response:', response?.anytime_goal_scorers);
      
      if (response && typeof response === 'object') {
        // Update the prop to show it's unlocked
        // CRITICAL: Must update all the separated arrays since PropsTab uses them directly
        
        // Create the updated prop object
        const createUpdatedProp = (p: any) => {
          const updatedProp = { 
            ...p, 
            // Force unlock state - these are critical!
            is_locked: false, 
            unlocked: true,
            // Use response data to update prediction, confidence, etc.
            prediction: response.prediction || p.prediction,
            confidence: response.confidence !== undefined ? response.confidence : p.confidence,
            odds: response.odds !== undefined ? response.odds : p.odds,
            reasoning: response.reasoning || p.reasoning,
            models: response.models || p.models,
          };
          
          // Spread any additional response fields
          Object.keys(response).forEach(key => {
            if (!['id', 'prediction', 'confidence', 'odds', 'reasoning', 'models', 'is_locked', 'unlocked'].includes(key)) {
              updatedProp[key] = response[key];
            }
          });
          
          return updatedProp;
        };
        
        // Update ALL the separated arrays that PropsTab uses
        console.log('[Dashboard] Updating all prop arrays for ID:', propId);
        
        setGoalsProps((prev: any[]) => {
          const updated = prev.map((p: any) => p && p.id === propId ? createUpdatedProp(p) : p);
          if (updated.some((p: any) => p?.id === propId && !p.is_locked)) {
            console.log('[Dashboard] ✅ Updated goalsProps - prop now unlocked');
          }
          return updated;
        });
        
        setAssistsProps((prev: any[]) => {
          const updated = prev.map((p: any) => p && p.id === propId ? createUpdatedProp(p) : p);
          if (updated.some((p: any) => p?.id === propId && !p.is_locked)) {
            console.log('[Dashboard] ✅ Updated assistsProps - prop now unlocked');
          }
          return updated;
        });
        
        setAnytimeGoalProps((prev: any[]) => {
          const updated = prev.map((p: any) => p && p.id === propId ? createUpdatedProp(p) : p);
          if (updated.some((p: any) => p?.id === propId && !p.is_locked)) {
            console.log('[Dashboard] ✅ Updated anytimeGoalProps - prop now unlocked');
          }
          return updated;
        });
        
        setTeamProps((prev: any[]) => {
          const updated = prev.map((p: any) => p && p.id === propId ? createUpdatedProp(p) : p);
          if (updated.some((p: any) => p?.id === propId && !p.is_locked)) {
            console.log('[Dashboard] ✅ Updated teamProps - prop now unlocked');
          }
          return updated;
        });
        
        setOtherProps((prev: any[]) => {
          const updated = prev.map((p: any) => p && p.id === propId ? createUpdatedProp(p) : p);
          if (updated.some((p: any) => p?.id === propId && !p.is_locked)) {
            console.log('[Dashboard] ✅ Updated otherProps - prop now unlocked');
          }
          return updated;
        });
        
        setGameProps((prev: any[]) => {
          const updated = prev.map((p: any) => p && p.id === propId ? createUpdatedProp(p) : p);
          console.log('[Dashboard] ✅ Updated gameProps - total props:', updated.length);
          return updated;
        });
        
        setPickCount((prev: number) => {
          const newCount = prev + 1;
          console.log('[Dashboard] Pick count updated:', prev, '->', newCount);
          return newCount;
        });
        console.log('[Dashboard] 🎉 Prop unlocked successfully - all arrays updated');
      } else {
        console.warn('[Dashboard] No valid response from unlock API');
        alert('Failed to unlock prediction. Please try again.');
      }
    } catch (err: any) {
      console.error('[Dashboard] Error unlocking prop:', err);
      console.error('[Dashboard] Error details:', {
        message: err.message,
        response: err.response,
        status: err.response?.status,
        statusText: err.response?.statusText,
        data: err.response?.data
      });
      
      // More specific error message
      let errorMsg = 'Failed to unlock prediction. ';
      if (err.response?.status === 404) {
        errorMsg += 'Endpoint not found. Please refresh the page.';
      } else if (err.response?.status === 401) {
        errorMsg += 'Session expired. Please log in again.';
      } else if (err.response?.status === 403) {
        errorMsg += 'Daily limit reached. Upgrade your tier for more picks.';
      } else if (err.response?.data?.detail) {
        errorMsg += err.response.data.detail;
      } else {
        errorMsg += 'Please try again.';
      }
      alert(errorMsg);
    } finally {
      setUnlockingId(null);
    }
  };

  // Club 100 Functions
  const fetchClub100Status = async () => {
    try {
      const response = await api.get('/predictions/club-100/status');
      setClub100Status(response.data);
    } catch (error: any) {
      if (error.response?.status === 401) {
        console.warn('Authentication required for Club 100 status');
      } else {
        console.error('Error fetching Club 100 status:', error);
      }
    }
  };

  const fetchClub100PlatformMetrics = async () => {
    try {
      const response = await api.get('/predictions/club-100/platform-metrics');
      if (response.data && response.data.success) {
        setClub100PlatformMetrics(response.data);
      }
    } catch (error: any) {
      console.warn('Error fetching Club 100 platform metrics:', error);
      // Non-critical error, continue without metrics
    }
  };

  const handleUnlockClub100 = async () => {
    try {
      setClub100Loading(true);
      const response = await api.post('/predictions/club-100/unlock');
      if (response.data.success) {
        setShowClub100Modal(false);
        setShowClub100Display(true);
        await fetchClub100Status();
      }
    } catch (error: any) {
      console.error('Full error response:', error.response);
      if (error.response?.status === 401) {
        alert('Authentication failed. Please log in again.');
        window.location.href = '/login';
      } else if (error.response?.status === 400) {
        alert(error.response.data.detail || 'Not enough picks to unlock Club 100');
      } else if (error.response) {
        alert(`Error: ${error.response.data.detail || error.response.statusText || 'Failed to unlock Club 100'}`);
      } else {
        alert('Failed to unlock Club 100. Please check your connection.');
      }
      console.error('Error unlocking Club 100:', error);
    } finally {
      setClub100Loading(false);
    }
  };

  const handleClub100ButtonClick = async () => {
    // Club 100 is ALWAYS accessible - just toggle the display
    setShowClub100Display(!showClub100Display);
  };

  // Fetch Club 100 status on mount
  React.useEffect(() => {
    if (isAuthenticated && user) {
      fetchClub100Status();
      fetchClub100PlatformMetrics();
    }
  }, [isAuthenticated, user]);

  if (!isAuthenticated || !user) {
    return null; // Will redirect to login
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Club 100 Modal - Not used since Club 100 is always accessible */}
      {/* Keeping for future reference but not displayed */}

      {/* Club 100 Display - Always available when toggled on */}
      {showClub100Display ? (
        <div className="min-h-screen bg-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <Club100Display
              onBack={() => setShowClub100Display(false)}
              club100Status={club100Status}
            />
          </div>
        </div>
      ) : (
        <div className="min-h-screen bg-gray-50">
          {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Sports Predictions Dashboard</h1>
              <p className="text-sm text-gray-600">Welcome back, {user?.email}</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">Tier: {tierConfig[userTier as keyof typeof tierConfig]?.name || 'Starter'}</p>
                <p className="text-xs text-gray-600">Picks: {pickCount} / {pickLimit}</p>
              </div>
              <button
                onClick={() => navigate('/upgrade')}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Upgrade
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Club 100 Banner - Always Visible - Shows Platform-Wide Metrics */}
      <div className="bg-gradient-to-r from-amber-50 to-orange-50 border-b-2 border-amber-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="mb-6">
            <div className="flex items-center justify-between gap-4 mb-4">
              <div className="flex-1">
                <h3 className="text-base font-bold text-amber-900 flex items-center gap-2">
                  <span className="text-xl">🏆</span>
                  Club 100: Elite Player Performance
                </h3>
                <p className="text-xs text-amber-800 mt-1">
                  BASIC, PRO, ELITE tiers only. Exclusive data on players hitting 100% success rates.
                </p>
              </div>
              <button
                onClick={handleClub100ButtonClick}
                className={`px-4 py-2 rounded-lg hover:shadow-lg hover:-translate-y-0.5 transition-all font-semibold text-sm whitespace-nowrap ${
                  club100Status?.tier_restricted 
                    ? 'bg-gray-400 text-gray-700 cursor-not-allowed' 
                    : 'bg-gradient-to-r from-amber-500 to-orange-500 text-white'
                }`}
                disabled={club100Status?.tier_restricted}
                title={club100Status?.tier_restricted ? 'Upgrade to unlock' : 'View Club 100 data'}
              >
                {club100Status?.tier_restricted 
                  ? '🔐 Upgrade to Unlock' 
                  : '✨ Club 100'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-600">Win Rate</p>
            <p className="text-2xl font-bold text-green-600">{(stats.winRate * 100).toFixed(1)}%</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-600">Total Predictions</p>
            <p className="text-2xl font-bold text-blue-600">{stats.predictions}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-600">Avg Confidence</p>
            <p className="text-2xl font-bold text-purple-600">{(stats.avgConfidence * 100).toFixed(0)}%</p>
          </div>
        </div>

        {/* Sport Tabs */}
        <div className="bg-white rounded-lg shadow mb-6">
          {/* Main Sport Tabs */}
          <div className="border-b overflow-x-auto">
            <nav className="flex space-x-3 px-4 py-2">
              {/* Predictions Tab */}
              <button
                onClick={() => setCurrentPage('predictions')}
                className={`py-3 px-4 border-b-2 font-medium text-sm whitespace-nowrap ${
                  currentPage === 'predictions'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                🎯 Predictions
              </button>
              
              {/* Accuracy Dashboard Tab */}
              <button
                onClick={() => setCurrentPage('accuracy')}
                className={`py-3 px-4 border-b-2 font-medium text-sm whitespace-nowrap ${
                  currentPage === 'accuracy'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                📊 Accuracy Dashboard
              </button>
              
              {/* Main Sport Tabs - only show when on predictions page */}
              {currentPage === 'predictions' && sportTabOptions.map((option) => (
                <button
                  key={option.key}
                  onClick={() => handleTabChange(option.key as SportKey)}
                  className={`py-3 px-4 border-b-2 font-medium text-sm whitespace-nowrap ${
                    activeTab === option.key
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Soccer Leagues Sub-Tabs - only show when on predictions page */}
          {currentPage === 'predictions' && (
            <div className="border-b bg-gradient-to-r from-blue-50 to-purple-50 overflow-x-auto">
              <nav className="flex space-x-2 px-4 py-2">
                <span className="text-xs font-semibold text-gray-600 py-3 px-2 whitespace-nowrap">Soccer Leagues:</span>
                {soccerTabOptions.map((option) => (
                  <button
                    key={option.key}
                    onClick={() => handleTabChange(option.key as SportKey)}
                    className={`py-2 px-3 border-b-2 font-medium text-xs whitespace-nowrap transition-colors ${
                      activeTab === option.key
                        ? 'border-orange-500 text-orange-600 bg-white rounded-t'
                        : 'border-transparent text-gray-600 hover:text-gray-800'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </nav>
            </div>
          )}

          {/* Content */}
          <div className="p-6">
            {currentPage === 'accuracy' ? (
              <AccuracyDashboard />
            ) : loading ? (
              <div className="flex flex-col justify-center items-center h-96 bg-gradient-to-br from-blue-50 via-purple-50 to-blue-50 rounded-2xl shadow-inner">
                <div className="relative">
                  <div className="animate-spin rounded-full h-20 w-20 border-4 border-blue-500 border-t-transparent"></div>
                  <div className="absolute inset-0 animate-ping rounded-full h-20 w-20 border-4 border-purple-400 opacity-20"></div>
                </div>
                <div className="mt-8 text-center px-8">
                  <p className="text-4xl font-extrabold bg-gradient-to-r from-blue-600 via-purple-600 to-blue-600 bg-clip-text text-transparent animate-pulse text-center leading-tight">
                    Hang tight
                  </p>
                  <p className="text-2xl font-bold text-blue-700 mt-3 animate-pulse text-center">
                    our systems are generating
                  </p>
                  <p className="text-3xl font-black text-purple-600 mt-2 animate-bounce text-center">
                    fresh & to the minute
                  </p>
                  <p className="text-4xl font-extrabold bg-gradient-to-r from-purple-600 via-blue-600 to-purple-600 bg-clip-text text-transparent mt-2 animate-pulse text-center">
                    PREDICTIONS
                  </p>
                </div>
                <div className="mt-6 flex items-center space-x-2">
                  <span className="text-2xl animate-bounce">⚡</span>
                  <span className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-yellow-500 to-orange-500 animate-pulse">
                    Powered by Advanced AI
                  </span>
                  <span className="text-2xl animate-bounce" style={{ animationDelay: '0.2s' }}>⚡</span>
                </div>
                <div className="mt-4 flex space-x-1">
                  <span className="w-3 h-3 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></span>
                  <span className="w-3 h-3 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></span>
                  <span className="w-3 h-3 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                  <span className="w-3 h-3 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }}></span>
                  <span className="w-3 h-3 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></span>
                </div>
              </div>
            ) : error ? (
              <div className="text-center py-8 text-red-600">
                <p>{error}</p>
                <button 
                  onClick={() => window.location.reload()}
                  className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Retry
                </button>
              </div>
            ) : viewMode === 'list' ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {predictions.length > 0 ? (
                  predictions.filter(p => p).map((prediction, index) => (
                    <div 
                      key={prediction?.id || index}
                      onClick={() => handleGameClick(prediction)}
                      className="cursor-pointer hover:shadow-lg transition-shadow"
                    >
                      <PredictionCard 
                        {...prediction} 
                        userTier={userTier} 
                        is_locked={prediction.is_locked}
                        pickCount={pickCount}
                        maxPicks={pickLimit}
                      />
                    </div>
                  ))
                ) : (
                  <div className="col-span-full text-center py-8 text-gray-500">
                    No predictions available for this sport at the moment.
                  </div>
                )}
              </div>
            ) : (
              <div>
                {/* Detail View */}
                <button
                  onClick={handleBackToList}
                  className="mb-4 px-4 py-2 text-blue-600 hover:text-blue-800 flex items-center"
                >
                  ← Back to predictions
                </button>

                {selectedGame && (
                  <div className="bg-gray-50 rounded-lg p-6 mb-6">
                    <h2 className="text-xl font-bold mb-2">{selectedGame.matchup}</h2>
                    <p className="text-gray-600 mb-4">{selectedGame.game_time}</p>
                    
                    {/* Main Prediction Display - MASKED until unlocked */}
                    <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-6 mb-6 text-center">
                      <p className="text-sm text-blue-600 font-semibold uppercase tracking-wider mb-2">
                        AI Prediction - {selectedGame.prediction_type?.toUpperCase() || 'MONEYLINE'}
                      </p>
                      <p className="text-3xl font-bold text-gray-900 mb-2">
                        {!selectedGame.is_locked ? selectedGame.prediction : '🔒 Unlock to see prediction'}
                      </p>
                      {/* Only show confidence for unlocked predictions or if user has basic+ tier */}
                      {(!selectedGame.is_locked || tierConfig[userTier as keyof typeof tierConfig]?.showOdds) && (
                      <div className="flex items-center justify-center gap-2">
                        <span className="text-sm text-gray-600">Confidence:</span>
                        <span className={`text-lg font-bold ${
                          selectedGame.confidence >= 75 ? 'text-green-700' : 
                          selectedGame.confidence >= 50 ? 'text-amber-700' : 'text-red-700'
                        }`}>
                          {typeof selectedGame.confidence === 'number' 
                            ? Math.round(selectedGame.confidence) 
                            : selectedGame.confidence}%
                        </span>
                      </div>
                      )}
                      {selectedGame.is_locked && (
                        <button
                          onClick={() => handleUnlockGame(selectedGame.id)}
                          disabled={pickCount >= pickLimit}
                          className={`mt-4 px-6 py-2 rounded-lg font-medium ${
                            pickCount >= pickLimit
                              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                              : 'bg-blue-600 text-white hover:bg-blue-700'
                          }`}
                        >
                          {pickCount >= pickLimit ? '⛔ Daily Limit Reached' : `🔓 Unlock Game Pick (${pickCount + 1}/${pickLimit})`}
                        </button>
                      )}
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div className="bg-white p-4 rounded shadow">
                        <p className="text-sm text-gray-600">Market</p>
                        <p className="text-lg font-bold text-blue-600 capitalize">
                          {selectedGame.prediction_type || 'Moneyline'}
                        </p>
                      </div>
                      <div className="bg-white p-4 rounded shadow">
                        <p className="text-sm text-gray-600">Confidence Score</p>
                        <p className={`text-lg font-bold ${
                          selectedGame.confidence >= 75 ? 'text-green-700' : 
                          selectedGame.confidence >= 50 ? 'text-amber-700' : 'text-red-700'
                        }`}>
                          {typeof selectedGame.confidence === 'number' 
                            ? Math.round(selectedGame.confidence) 
                            : selectedGame.confidence}%
                        </p>
                      </div>
                    </div>

                    {/* Team Pick Reasoning - Show for all users */}
                    {selectedGame.reasoning && selectedGame.reasoning.length > 0 && (
                      <div className="bg-white p-4 rounded shadow mb-4">
                        <p className="text-sm font-medium text-gray-700 mb-2">AI Analysis & Reasoning:</p>
                        <div className="space-y-2">
                          {selectedGame.reasoning.map((r: any, i: number) => (
                            <div key={i} className="text-sm">
                              <span className="font-medium text-blue-600">{r.factor}:</span>
                              <span className="text-gray-600 ml-1">{r.explanation}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Unlock Section */}
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
                      <h3 className="font-bold text-amber-800 mb-2">🔓 Unlock Detailed Picks</h3>
                      <p className="text-sm text-amber-700 mb-3">
                        Choose from player props or team picks below. Each unlock uses 1 daily pick.
                      </p>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Daily picks used:</span>
                        <span className="font-bold text-blue-600">
                          {pickCount} / {pickLimit}
                        </span>
                      </div>
                    </div>

                    {/* Props Category Toggle */}
                    {/* Player Props vs Team Stats Button Layout */}
                    <div className="mb-6 flex gap-4 border-b">
                      <button
                        onClick={() => setPropsViewMode('player')}
                        className={`px-6 py-3 font-semibold transition-colors ${
                          propsViewMode === 'player'
                            ? 'text-blue-600 border-b-2 border-blue-600'
                            : 'text-gray-600 hover:text-gray-900 border-b-2 border-transparent'
                        }`}
                      >
                        👤 Player Props
                      </button>
                      <button
                        onClick={() => setPropsViewMode('team')}
                        className={`px-6 py-3 font-semibold transition-colors ${
                          propsViewMode === 'team'
                            ? 'text-blue-600 border-b-2 border-blue-600'
                            : 'text-gray-600 hover:text-gray-900 border-b-2 border-transparent'
                        }`}
                      >
                        🏀 Team Stats
                      </button>
                    </div>

                    {/* Use unified PropsTab for ALL sports */}
                    {propsViewMode === 'player' ? (
                      <PropsTab
                        goalsProps={goalsProps}
                        assistsProps={assistsProps}
                        anytimeGoalProps={anytimeGoalProps}
                        teamProps={[]}
                        otherProps={otherProps}
                        userTier={userTier}
                        tierConfig={tierConfig}
                        pickCount={pickCount}
                        pickLimit={pickLimit}
                        unlockingId={unlockingId}
                        onUnlockProp={handleUnlockProp}
                        sportKey={selectedGame?.sport_key}
                        anytimeGoalScorers={anytimeGoalScorers}
                      />
                    ) : (
                      <PropsTab
                        goalsProps={[]}
                        assistsProps={[]}
                        anytimeGoalProps={[]}
                        teamProps={teamProps}
                        otherProps={[]}
                        userTier={userTier}
                        tierConfig={tierConfig}
                        pickCount={pickCount}
                        pickLimit={pickLimit}
                        unlockingId={unlockingId}
                        onUnlockProp={handleUnlockProp}
                        sportKey={selectedGame?.sport_key}
                      />
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
