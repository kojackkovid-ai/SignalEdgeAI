import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';

interface GamePerformance {
  games_analyzed: number;
  coverage_count: number;
  coverage_percent: number;
}

interface PlayerData {
  player_id: string;
  name: string;
  team: string;
  sport: string;
  prop_line?: string;  // Optional - hidden until unlocked
  consecutive_games: number;
  last_4_games?: GamePerformance | null;
  last_5_games?: GamePerformance | null;
}

interface Club100Data {
  [key: string]: PlayerData[] | string[] | string | undefined;
  unlocked_picks?: string[];
  warning?: string;
}

interface Club100DisplayProps {
  onBack?: () => void;
  club100Status?: {
    daily_picks_used: number;
    daily_picks_limit: number;
  } | null;
}

const Club100Display: React.FC<Club100DisplayProps> = ({ onBack, club100Status }) => {
  const navigate = useNavigate();
  const [club100Data, setClub100Data] = useState<Club100Data | null>(null);
  const [unlockedPicks, setUnlockedPicks] = useState<Set<string>>(new Set());
  const [selectedSport, setSelectedSport] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [unlockedPlayerId, setUnlockedPlayerId] = useState<string | null>(null);
  const [sortColumn, setSortColumn] = useState<string>('consecutive_games');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchClub100Data();
  }, []);

  const fetchClub100Data = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await api.get('/predictions/club-100/data', { timeout: 15000 });

      if (response.data && response.data.success) {
        const data = response.data.data;

        // Extract unlocked picks list
        const unlockedList = data.unlocked_picks || [];
        setUnlockedPicks(new Set(unlockedList));

        if (response.data.warning) {
          setError(response.data.warning);
        }

        setClub100Data(data);

        const availableSports = Object.keys(data).filter(
          (sport) => sport !== 'unlocked_picks' && sport !== 'warning' && data[sport] && Array.isArray(data[sport]) && data[sport].length > 0
        );

        if (availableSports.length > 0) {
          setSelectedSport(availableSports[0]);
        } else {
          setSelectedSport('nba');
        }
      } else {
        setError('Invalid response from server');
      }
    } catch (err: any) {
      console.error('[Club100Display] Error fetching Club 100 data:', err);
      if (err.response?.status === 403) {
        // Use the backend's detailed error message if available
        const backendMessage = err.response?.data?.detail || 'Club 100 access required';
        setError(backendMessage);
      } else if (err.code === 'ECONNABORTED') {
        setError('Request timeout - Club 100 data took too long to load. Please try again.');
      } else if (err.message === 'Network Error') {
        setError('Network error - Cannot connect to server. Please check your connection.');
      } else {
        setError(`Failed to load Club 100 data: ${err.message || 'Unknown error'}`);
      }
      console.error('Error details:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (error) {
    // Format markdown-style message from backend
    const formatErrorMessage = (msg: string) => {
      // Convert markdown formatting to React elements
      return msg.split('\n').map((line, idx) => {
        // Handle markdown bold: **text**
        if (line.includes('**')) {
          const parts = line.split(/\*\*(.*?)\*\*/g);
          return (
            <div key={idx} className="mb-2">
              {parts.map((part, i) => 
                i % 2 === 1 ? <strong key={i} className="font-bold text-gray-900">{part}</strong> : part
              )}
            </div>
          );
        }
        // Handle markdown italic: _text_
        if (line.includes('_') && line.split('_').length >= 3) {
          const parts = line.split(/_(.*?)_/g);
          return (
            <div key={idx} className="mb-2">
              {parts.map((part, i) => 
                i % 2 === 1 ? <em key={i} className="italic text-gray-700">{part}</em> : part
              )}
            </div>
          );
        }
        return line ? <div key={idx} className="mb-2">{line}</div> : null;
      });
    };

    return (
      <div className="w-full min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="bg-white rounded-2xl shadow-xl border-2 border-purple-200 p-10">
            {/* Premium badge */}
            <div className="text-center mb-6">
              <span className="inline-block px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-full text-sm font-bold mb-4">
                ✨ PREMIUM FEATURE
              </span>
            </div>

            {/* Main message */}
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-6">
                Unlock Your Elite Predictions
              </h2>
              
              {/* Formatted backend message */}
              <div className="text-gray-700 text-left bg-gray-50 rounded-lg p-6 mb-6 space-y-3">
                {formatErrorMessage(error)}
              </div>
            </div>

            {/* Benefits highlight */}
            <div className="grid grid-cols-2 gap-4 mb-8">
              <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                <div className="text-2xl mb-2">🎯</div>
                <p className="font-semibold text-purple-900">Elite Picks</p>
                <p className="text-sm text-purple-700">Top performers only</p>
              </div>
              <div className="bg-pink-50 rounded-lg p-4 border border-pink-200">
                <div className="text-2xl mb-2">📈</div>
                <p className="font-semibold text-pink-900">Higher Win Rate</p>
                <p className="text-sm text-pink-700">Premium accuracy</p>
              </div>
            </div>

            {/* Call to action */}
            <div className="flex gap-3 justify-center">
              <button 
                type="button"
                onClick={(e) => {
                  e.preventDefault();
                  navigate('/pricing');
                }}
                className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-bold hover:shadow-lg hover:scale-105 transition transform cursor-pointer"
              >
                💳 Upgrade Now
              </button>
              <button 
                type="button"
                onClick={(e) => {
                  e.preventDefault();
                  if (onBack) {
                    onBack();
                  } else {
                    window.history.back();
                  }
                }}
                className="px-6 py-3 bg-gray-200 text-gray-800 rounded-lg font-bold hover:bg-gray-300 transition cursor-pointer"
              >
                ← Go Back
              </button>
            </div>
          </div>

          {/* Additional info */}
          <div className="text-center mt-8 text-gray-600 text-sm">
            <p>Limited time offer - Get instant access to Club 100 predictions</p>
          </div>
        </div>
      </div>
    );
  }

  if (isLoading || !club100Data) {
    return (
      <div className="w-full min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="flex items-center justify-center py-24">
            <div className="text-center">
              <div className="text-6xl mb-4 animate-pulse">🏆</div>
              <p className="text-gray-600 text-lg">Loading Club 100 data...</p>
              <p className="text-gray-500 text-sm mt-2">This may take a moment</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const allSports = ['nba', 'nfl', 'mlb', 'nhl', 'soccer'];
  const sportDisplayNames: Record<string, string> = {
    nba: '🏀 NBA',
    nfl: '🏈 NFL',
    mlb: '⚾ MLB',
    nhl: '🏒 NHL',
    soccer: '⚽ Soccer',
  };

  const warningText = typeof club100Data.warning === 'string' ? club100Data.warning : null;

  /** Safely extract the PlayerData[] for a given sport key, filtering out meta-fields. */
  const getPlayers = (sport: string): PlayerData[] => {
    const raw = club100Data[sport];
    if (!Array.isArray(raw) || raw.length === 0) return [];
    if (typeof raw[0] === 'string') return [];
    return raw as PlayerData[];
  };

  let currentPlayers: PlayerData[] = getPlayers(selectedSport);

  // Sorting logic
  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('desc');
    }
  };

  currentPlayers = [...currentPlayers].sort((a, b) => {
    let aVal: any = a[sortColumn as keyof PlayerData];
    let bVal: any = b[sortColumn as keyof PlayerData];

    if (sortColumn === 'consecutive_games') {
      aVal = a.consecutive_games;
      bVal = b.consecutive_games;
    } else if (sortColumn === 'last_4_games') {
      aVal = a.last_4_games?.coverage_percent || 0;
      bVal = b.last_4_games?.coverage_percent || 0;
    } else if (sortColumn === 'last_5_games') {
      aVal = a.last_5_games?.coverage_percent || 0;
      bVal = b.last_5_games?.coverage_percent || 0;
    }

    if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
    return 0;
  });

  const SortArrow = ({ column }: { column: string }) => {
    if (sortColumn !== column) return <span className="text-gray-300">↕</span>;
    return sortDirection === 'asc' ? <span>↑</span> : <span>↓</span>;
  };

  const handleUnlockClub100Player = async (player: PlayerData) => {
    try {
      setUnlockedPlayerId(player.player_id);
      setSuccessMessage(null);
      
      const response = await api.post(
        `/predictions/club-100/follow/${player.player_id}`,
        {},
        { timeout: 15000 }
      );
      
      if (response.data && response.data.success) {
        // Add to unlocked picks
        const newUnlocked = new Set(unlockedPicks);
        newUnlocked.add(player.player_id);
        setUnlockedPicks(newUnlocked);
        
        // Update player data with the returned prop_line
        const sportPlayers = getPlayers(player.sport);
        if (sportPlayers.length > 0) {
          const updatedPlayers = sportPlayers.map(p =>
            p.player_id === player.player_id
              ? { ...p, prop_line: response.data.prop_line }
              : p
          );
          setClub100Data({
            ...club100Data,
            [player.sport]: updatedPlayers
          });
        }
        
        setSuccessMessage(`✓ Unlocked ${player.name}! Prop line: ${response.data.prop_line}`);
        setTimeout(() => setSuccessMessage(null), 3000);
        
      } else {
        throw new Error(response.data?.detail || 'Failed to unlock this player');
      }
    } catch (err: any) {
      console.error('Error unlocking Club 100 player:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to unlock this player';
      alert(`⚠️ ${errorMsg}`);
    } finally {
      setUnlockedPlayerId(null);
    }
  };

  return (
    <div className="w-full">
      {/* Success Message */}
      {successMessage && (
        <div className="mb-6 bg-green-50 border-2 border-green-200 rounded-lg p-4 text-green-700 font-semibold">
          {successMessage}
        </div>
      )}

      {/* Header */}
      <div className="bg-gradient-to-r from-amber-500 to-orange-500 rounded-xl p-8 mb-8 text-white">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <span className="text-4xl">🏆</span>
            <h2 className="text-3xl font-black">Club 100 Elite Players</h2>
          </div>
          {onBack && (
            <button
              onClick={onBack}
              className="px-4 py-2 bg-white/20 hover:bg-white/30 text-white font-bold rounded-lg transition-all flex items-center gap-2"
              title="Back to Predictions"
            >
              ← Back to Predictions
            </button>
          )}
        </div>
        <p className="text-lg text-white/90">
          Players who cleared their prop lines 100% in their last 4 & 5 games
        </p>
        <p className="text-sm text-white/80 mt-2">
          🔒 Click "Unlock" to reveal the prop line (costs 1 pick per player)
        </p>
      </div>

      {/* Sport Selector */}
      <div className="flex flex-wrap gap-2 mb-8">
        {allSports.map((sport) => (
          <button
            key={sport}
            onClick={() => setSelectedSport(sport)}
            className={`px-6 py-3 font-bold rounded-xl transition-all ${
              selectedSport === sport
                ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {sportDisplayNames[sport] || sport.toUpperCase()}
            <span className="ml-2 text-sm">({club100Data[sport]?.length || 0})</span>
          </button>
        ))}
      </div>

      {/* Spreadsheet Table */}
      {currentPlayers.length > 0 ? (
        <div className="overflow-x-auto rounded-lg border-2 border-gray-300 shadow-lg">
          <table className="w-full">
            <thead>
              <tr className="bg-gradient-to-r from-gray-900 to-gray-800 text-white">
                <th className="px-4 py-4 text-left font-bold border-b-2 border-gray-700 cursor-pointer hover:bg-gray-700/50" onClick={() => handleSort('name')} onKeyDown={(e) => e.key === 'Enter' && handleSort('name')} tabIndex={0} role="button" aria-label="Sort by player name">
                  <div className="flex items-center gap-2">
                    Player Name
                    <SortArrow column="name" />
                  </div>
                </th>
                <th className="px-4 py-4 text-center font-bold border-b-2 border-gray-700">Team</th>
                <th className="px-4 py-4 text-left font-bold border-b-2 border-gray-700">
                  Prop Line
                </th>
                <th className="px-4 py-4 text-center font-bold border-b-2 border-gray-700 cursor-pointer hover:bg-gray-700/50" onClick={() => handleSort('consecutive_games')} onKeyDown={(e) => e.key === 'Enter' && handleSort('consecutive_games')} tabIndex={0} role="button" aria-label="Sort by streak">
                  <div className="flex items-center justify-center gap-1">
                    Streak
                    <SortArrow column="consecutive_games" />
                  </div>
                </th>
                <th className="px-4 py-4 text-center font-bold border-b-2 border-gray-700 cursor-pointer hover:bg-gray-700/50" onClick={() => handleSort('last_4_games')} onKeyDown={(e) => e.key === 'Enter' && handleSort('last_4_games')} tabIndex={0} role="button" aria-label="Sort by last 4 games">
                  <div className="flex items-center justify-center gap-1">
                    Last 4 <SortArrow column="last_4_games" />
                  </div>
                </th>
                <th className="px-4 py-4 text-center font-bold border-b-2 border-gray-700 cursor-pointer hover:bg-gray-700/50" onClick={() => handleSort('last_5_games')} onKeyDown={(e) => e.key === 'Enter' && handleSort('last_5_games')} tabIndex={0} role="button" aria-label="Sort by last 5 games">
                  <div className="flex items-center justify-center gap-1">
                    Last 5 <SortArrow column="last_5_games" />
                  </div>
                </th>
                <th className="px-4 py-4 text-center font-bold border-b-2 border-gray-700">Action</th>
              </tr>
            </thead>
            <tbody>
              {currentPlayers.map((player, index) => {
                const isUnlocked = unlockedPicks.has(player.player_id);
                return (
                  <tr 
                    key={player.player_id} 
                    className={`border-b border-gray-200 hover:bg-blue-50 transition-colors ${
                      index % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                    }`}
                  >
                    <td className="px-4 py-4 text-left font-semibold text-gray-900">{player.name}</td>
                    <td className="px-4 py-4 text-center font-bold text-gray-700 bg-blue-100 text-blue-800 w-16">
                      {player.team}
                    </td>
                    <td className="px-4 py-4 text-left">
                      {isUnlocked && player.prop_line ? (
                        <span className="text-gray-700 font-semibold">{player.prop_line}</span>
                      ) : isUnlocked ? (
                        <span className="text-gray-700 font-semibold">{player.prop_line || '🔓 Unlocked'}</span>
                      ) : (
                        <span className="text-gray-400 italic flex items-center gap-2">
                          🔒 Click to Unlock
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-4 text-center">
                      <span className="inline-block px-3 py-1 bg-orange-100 text-orange-800 font-bold rounded-full text-sm">
                        {player.consecutive_games} games
                      </span>
                    </td>
                    <td className="px-4 py-4 text-center">
                      {player.last_4_games ? (
                        <div className="flex flex-col items-center gap-1">
                          <span className="text-lg font-bold text-green-600">{player.last_4_games.coverage_percent.toFixed(0)}%</span>
                          <span className="text-xs text-gray-600">{player.last_4_games.coverage_count}/{player.last_4_games.games_analyzed}</span>
                        </div>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-4 py-4 text-center">
                      {player.last_5_games ? (
                        <div className="flex flex-col items-center gap-1">
                          <span className="text-lg font-bold text-green-600">{player.last_5_games.coverage_percent.toFixed(0)}%</span>
                          <span className="text-xs text-gray-600">{player.last_5_games.coverage_count}/{player.last_5_games.games_analyzed}</span>
                        </div>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-4 py-4 text-center">
                      {isUnlocked ? (
                        <span className="inline-block px-3 py-2 bg-green-100 text-green-700 rounded-lg font-bold text-sm">
                          ✓ Following
                        </span>
                      ) : (
                        <button
                          onClick={() => handleUnlockClub100Player(player)}
                          disabled={unlockedPlayerId === player.player_id}
                          className={`px-3 py-2 rounded-lg font-bold text-sm transition-all ${
                            unlockedPlayerId === player.player_id
                              ? 'bg-gray-300 text-gray-600 cursor-not-allowed'
                              : 'bg-gradient-to-r from-purple-500 to-pink-600 text-white hover:shadow-lg active:scale-95'
                          }`}
                        >
                          {unlockedPlayerId === player.player_id ? '⏳ Unlocking...' : '🔓 Unlock (1 pick)'}
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="bg-gray-50 border-2 border-gray-200 rounded-xl p-12 text-center">
          <p className="text-gray-600 text-lg">
            No players found for {sportDisplayNames[selectedSport] || selectedSport.toUpperCase()} in Club 100 data
          </p>
        </div>
      )}

      {/* Stats Summary */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 border-2 border-blue-300 rounded-lg p-6">
          <div className="text-4xl font-bold text-blue-600">{currentPlayers.length}</div>
          <p className="text-gray-700 font-semibold mt-2">Players This Sport</p>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-green-100 border-2 border-green-300 rounded-lg p-6">
          <div className="text-4xl font-bold text-green-600">{unlockedPicks.size}</div>
          <p className="text-gray-700 font-semibold mt-2">Players Unlocked</p>
        </div>
        <div className="bg-gradient-to-br from-orange-50 to-orange-100 border-2 border-orange-300 rounded-lg p-6">
          <div className="text-4xl font-bold text-orange-600">{currentPlayers.length > 0 ? Math.max(...currentPlayers.map(p => p.consecutive_games)) : 0}</div>
          <p className="text-gray-700 font-semibold mt-2">Longest Active Streak</p>
        </div>
      </div>
    </div>
  );
};

export default Club100Display;
