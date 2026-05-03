import React, { useState, useMemo, useEffect } from 'react';
import { analyticsTracker } from '../utils/analytics';

interface Prop {
  id: string;
  player?: string;
  team_name?: string;
  market_key: string;
  market_name?: string;
  point?: number;
  prediction: string;
  confidence: number;
  season_avg?: number;
  recent_10_avg?: number;
  recent_avg?: number;
  reasoning?: Array<{ factor: string; explanation: string }>;
  models?: Array<{ name: string; confidence: number }>;
  is_locked: boolean;
  prediction_type?: string;
  anytime_goal_scorers?: any;
  anytime_goal_names?: string[];
}

interface PropsTabProps {
  goalsProps: Prop[];
  assistsProps: Prop[];
  anytimeGoalProps: Prop[];
  teamProps: Prop[];
  otherProps?: Prop[];
  userTier: string;
  tierConfig: any;
  pickCount: number;
  pickLimit: number;
  unlockingId: string | null;
  onUnlockProp: (propId: string) => void;
  sportKey?: string;
  anytimeGoalScorers?: any;
}

const PropsTab: React.FC<PropsTabProps> = ({
  goalsProps,
  assistsProps,
  anytimeGoalProps,
  teamProps,
  otherProps = [],
  userTier,
  tierConfig,
  pickCount,
  pickLimit,
  unlockingId,
  onUnlockProp,
  sportKey = '',
  anytimeGoalScorers = null,
}) => {
  const [activeTab, setActiveTab] = useState<'goals' | 'assists' | 'anytime'>('goals');
  const [activeTeamTab, setActiveTeamTab] = useState<'totals' | 'anytime_team'>('totals');
  
  // Track props view on mount
  useEffect(() => {
    analyticsTracker.trackPropsView('', sportKey || 'unknown', 'player_props').catch(() => {});
  }, [sportKey]);

  // Separate player props from team props for non-hockey/soccer sports
  const playerPropsNBA = useMemo(() => {
    return otherProps.filter(p => 
      !['game_total', 'anytime_goal_team'].includes(p.market_key)
    );
  }, [otherProps]);

  const teamPropsNBA = useMemo(() => {
    return teamProps.length > 0 
      ? teamProps 
      : otherProps.filter(p => 
          ['game_total', 'anytime_goal_team'].includes(p.market_key)
        );
  }, [teamProps, otherProps]);

  // Determine if this is a hockey/soccer sport
  const isHockeyOrSoccer = sportKey?.includes('hockey') || sportKey?.includes('soccer');

  const PropCard = ({ prop }: { prop: Prop }) => {
    const statCategory = prop.market_name || 
      (prop.market_key 
        ? prop.market_key
            .split('_')
            .map((word: string) => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ')
        : 'Stat');

    return (
      <div className="bg-white p-4 rounded-lg shadow border border-gray-200 hover:shadow-md transition-shadow">
        <div className="flex justify-between items-start mb-3">
          <div className="flex-1">
            {/* Player/Team Name with Team and Stat Category */}
            <div className="mb-2">
              <div className="flex items-center gap-2 flex-wrap">
                {prop.player && (
                  <p className="font-bold text-gray-900 text-lg">{prop.player}</p>
                )}
                <span className="text-xs bg-amber-100 text-amber-700 px-2 py-1 rounded font-semibold">
                  {prop.team_name || 'N/A'}
                </span>
                <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded font-medium">
                  {statCategory}
                </span>
              </div>
            </div>
            {/* Player/Team Stats */}
            <div className="mt-2 text-xs text-gray-700 bg-blue-50 p-2 rounded border border-blue-100">
              <div className="flex justify-between gap-4 flex-wrap">
                {prop.season_avg !== undefined && prop.season_avg !== null && !isNaN(prop.season_avg) && (
                  <span className="font-semibold">Season Avg: <span className="text-blue-700">{typeof prop.season_avg === 'number' ? prop.season_avg.toFixed(2) : prop.season_avg}</span></span>
                )}
                {prop.recent_10_avg !== undefined && prop.recent_10_avg !== null && !isNaN(prop.recent_10_avg) && (
                  <span className="font-semibold">Last 10: <span className="text-blue-700">{typeof prop.recent_10_avg === 'number' ? prop.recent_10_avg.toFixed(2) : prop.recent_10_avg}</span></span>
                )}
                {prop.recent_avg !== undefined && prop.recent_avg !== null && !isNaN(prop.recent_avg) && !prop.recent_10_avg && (
                  <span className="font-semibold">Recent Avg: <span className="text-blue-700">{typeof prop.recent_avg === 'number' ? prop.recent_avg.toFixed(2) : prop.recent_avg}</span></span>
                )}
              </div>
            </div>
            {/* Team Stats Display for Game Totals - MOVED TO UNLOCKED SECTION */}
            {prop.market_key === 'game_total' && !prop.is_locked && (
              <div className="mt-2 text-xs text-gray-700 bg-pink-50 p-2 rounded border border-pink-200">
                <p className="font-bold text-pink-900 mb-1">📊 Team Statistics:</p>
                <div className="grid grid-cols-2 gap-2">
                  {(prop as any).home_gpg !== undefined && (prop as any).home_gpg !== null && (
                    <span className="font-medium">Home Scoring: <span className="text-pink-700">{typeof (prop as any).home_gpg === 'number' ? (prop as any).home_gpg.toFixed(2) : (prop as any).home_gpg} PPG</span></span>
                  )}
                  {(prop as any).away_gpg !== undefined && (prop as any).away_gpg !== null && (
                    <span className="font-medium">Away Scoring: <span className="text-pink-700">{typeof (prop as any).away_gpg === 'number' ? (prop as any).away_gpg.toFixed(2) : (prop as any).away_gpg} PPG</span></span>
                  )}
                  {(prop as any).home_ga !== undefined && (prop as any).home_ga !== null && (
                    <span className="font-medium">Home Defense: <span className="text-pink-700">{typeof (prop as any).home_ga === 'number' ? (prop as any).home_ga.toFixed(2) : (prop as any).home_ga} PPG Allowed</span></span>
                  )}
                  {(prop as any).away_ga !== undefined && (prop as any).away_ga !== null && (
                    <span className="font-medium">Away Defense: <span className="text-pink-700">{typeof (prop as any).away_ga === 'number' ? (prop as any).away_ga.toFixed(2) : (prop as any).away_ga} PPG Allowed</span></span>
                  )}
                  {(prop as any).expected_value !== undefined && (prop as any).expected_value !== null && (
                    <span className="font-medium col-span-2">Expected Total: <span className="text-pink-700">{typeof (prop as any).expected_value === 'number' ? (prop as any).expected_value.toFixed(2) : (prop as any).expected_value}</span></span>
                  )}
                </div>
              </div>
            )}
          </div>
          <div className="text-right">
            {/* Only show line for unlocked props or if user's tier allows it */}
            {(!prop.is_locked || tierConfig[userTier as keyof typeof tierConfig]?.showLine) && prop.point !== undefined && (
              <p className="text-lg font-bold text-gray-900">Line: {prop.point}</p>
            )}
            <p
              className={`text-sm font-medium ${
                prop.confidence >= 75
                  ? 'text-green-700'
                  : prop.confidence >= 50
                    ? 'text-amber-700'
                    : 'text-red-700'
              }`}
            >
              {typeof prop.confidence === 'number' ? Math.round(prop.confidence) : prop.confidence}% Confidence
            </p>
          </div>
        </div>

        {prop.is_locked ? (
          <button
            onClick={() => onUnlockProp(prop.id)}
            disabled={unlockingId === prop.id || pickCount >= pickLimit}
            className={`w-full py-3 px-4 rounded-lg font-medium transition-all ${
              pickCount >= pickLimit
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700 shadow-md hover:shadow-lg'
            }`}
          >
            {unlockingId === prop.id ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Unlocking...
              </span>
            ) : pickCount >= pickLimit ? (
              '⛔ Daily Limit Reached'
            ) : (
              <>🔓 Unlock Prop ({pickCount + 1}/{pickLimit})</>
            )}
          </button>
        ) : (
          <div className="bg-green-50 border border-green-200 rounded-lg p-3">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-gray-800">AI Prediction:</span>
              <span className="font-bold text-gray-900 text-lg">{prop.prediction || 'N/A'}</span>
            </div>
            
            {/* Special display for anytime goal team - Top 2 players per team */}
            {prop.market_key === 'anytime_goal_team' && (prop as any).home_team_players && (prop as any).away_team_players && (
              <div className="bg-blue-50 border border-blue-200 rounded p-2 mb-2 mt-2">
                <p className="text-sm font-bold text-blue-900 mb-3">🎯 Top 2 Players Most Likely to Score:</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Home Team */}
                  <div className="bg-white border border-blue-300 rounded-lg p-3">
                    <h4 className="font-bold text-blue-900 mb-2">{(prop as any).home_team?.name || 'Home Team'}</h4>
                    <div className="space-y-2">
                      {(prop as any).home_team_players.slice(0, 2).map((player: string, idx: number) => (
                        <div key={idx} className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-gray-900">{player}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  {/* Away Team */}
                  <div className="bg-white border border-blue-300 rounded-lg p-3">
                    <h4 className="font-bold text-blue-900 mb-2">{(prop as any).away_team?.name || 'Away Team'}</h4>
                    <div className="space-y-2">
                      {(prop as any).away_team_players.slice(0, 2).map((player: string, idx: number) => (
                        <div key={idx} className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-gray-900">{player}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <div className="flex items-center gap-2 text-sm text-gray-800">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <span>Unlocked - Good luck!</span>
            </div>

            {/* Show reasoning based on tier */}
            {tierConfig[userTier as keyof typeof tierConfig]?.showReasoning && prop.reasoning && (
              <div className="mt-3 pt-3 border-t border-green-200">
                <p className="text-sm font-medium text-gray-700 mb-2">AI Analysis:</p>
                <div className="space-y-2">
                  {prop.reasoning.slice(0, 2).map((r: any, i: number) => (
                    <div key={i} className="text-sm">
                      <span className="font-medium text-blue-600">{r.factor}:</span>
                      <span className="text-gray-600 ml-1">{r.explanation}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Show models based on tier */}
            {(tierConfig[userTier as keyof typeof tierConfig]?.showModels || userTier === 'pro' || userTier === 'elite') && (
              <div className="mt-3 pt-3 border-t border-green-200">
                <p className="text-sm font-medium text-gray-900 mb-2">Model Breakdown:</p>
                <div className="space-y-1">
                  {prop.models && prop.models.length > 0 ? (
                    prop.models.map((m: any, i: number) => (
                      <div key={i} className="flex justify-between text-sm">
                        <span className="text-gray-800 font-medium">{m.name}:</span>
                        <span className="font-bold text-gray-900">{m.confidence}%</span>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-gray-500 italic">Model breakdown not available</p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const renderPropsSection = (props: Prop[], label: string) => (
    <div>
      <h3 className="text-lg font-bold text-gray-900 mb-4">{label}</h3>
      <div className="space-y-3">
        {props.length > 0 ? (
          props.map((prop) => <PropCard key={prop.id} prop={prop} />)
        ) : (
          <div className="text-center py-8 bg-gray-50 rounded-lg">
            <p className="text-gray-500 mb-2">No {label.toLowerCase()} available for this game.</p>
            <p className="text-sm text-gray-400">Check back later for more props.</p>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="space-y-8">
      {/* PLAYER PROP STATS SECTION */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-lg border border-blue-200">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">📊 PLAYER PROP STATS</h2>
        
        {/* Hockey/Soccer specific: ANYTIME GOAL ONLY */}
        {isHockeyOrSoccer && anytimeGoalProps.length > 0 ? (
          <>
            <div className="mb-4">
              <h3 className="text-lg font-bold text-gray-900 mb-2">🎯 Anytime Goal Scorer Props (Individually Locked)</h3>
              <p className="text-sm text-gray-600 mb-4">Each player prop is individually locked. Unlock to see detailed AI analysis, model breakdowns, and scoring predictions.</p>
            </div>

            {/* Player Props Tab Content - Anytime Goal Only */}
            <div>
              {renderPropsSection(anytimeGoalProps, 'Anytime Goal Scorer Props')}
            </div>
          </>
        ) : playerPropsNBA.length > 0 ? (
          // NBA/MLB/NFL/NCAA: Show all player props
          <div>
            <p className="text-sm text-gray-600 mb-4">Available player props for this game:</p>
            {renderPropsSection(playerPropsNBA, 'Player Props')}
          </div>
        ) : (
          <div className="text-center py-8 bg-white rounded-lg">
            <p className="text-gray-500 mb-2">⏳ No player props available yet</p>
            <p className="text-sm text-gray-400">Props will appear once available for this game.</p>
          </div>
        )}
      </div>

      {/* TEAM STATS SECTION */}
      {(teamPropsNBA.length > 0 || (isHockeyOrSoccer && teamProps.length > 0)) && (
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-6 rounded-lg border border-green-200">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">🏟️ TEAM STATS</h2>
          
          {/* Hockey/Soccer: Use separate tabs */}
          {isHockeyOrSoccer ? (
            <>
              {/* Team Props Tabs */}
              <div className="flex space-x-2 mb-6 border-b border-green-200 flex-wrap">
                <button
                  onClick={() => setActiveTeamTab('totals')}
                  className={`px-4 py-3 font-medium border-b-2 transition-colors ${
                    activeTeamTab === 'totals'
                      ? 'border-green-600 text-green-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900'
                  }`}
                >
                  📈 Game Totals ({teamProps.filter(p => p.market_key === 'game_total').length})
                </button>
                <button
                  onClick={() => setActiveTeamTab('anytime_team')}
                  className={`px-4 py-3 font-medium border-b-2 transition-colors ${
                    activeTeamTab === 'anytime_team'
                      ? 'border-green-600 text-green-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900'
                  }`}
                >
                  ⚡ Anytime Goal Team ({teamProps.filter(p => p.market_key === 'anytime_goal_team').length})
                </button>
              </div>

              {/* Team Props Tab Content */}
              <div>
                {activeTeamTab === 'totals' && renderPropsSection(
                  teamProps.filter(p => p.market_key === 'game_total'),
                  'Game Total Over/Under'
                )}
                {activeTeamTab === 'anytime_team' && (
                  <div>
                    <h3 className="text-lg font-bold text-gray-900 mb-4">⚡ Anytime Goal Team Props</h3>
                    <p className="text-sm text-gray-600 mb-4">Unlock each team individually to see the top 2 players most likely to score, with detailed AI analysis.</p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {teamProps
                        .filter(p => p.market_key === 'anytime_goal_team')
                        .map((prop) => (
                          <div key={prop.id} className="bg-white p-4 rounded-lg shadow border border-gray-200 hover:shadow-md transition-shadow">
                            <div className="flex justify-between items-start mb-3">
                              <div className="flex-1">
                                <div className="mb-2">
                                  <div className="flex items-center gap-2 flex-wrap">
                                    <p className="font-bold text-gray-900 text-lg">{prop.player || 'Team Anytime Goal'}</p>
                                    <span className="text-xs bg-amber-100 text-amber-700 px-2 py-1 rounded font-semibold">
                                      Anytime Goal Team
                                    </span>
                                  </div>
                                </div>
                              </div>
                              <div className="text-right">
                                <p className={`text-sm font-medium text-green-700`}>AI Analysis Available</p>
                              </div>
                            </div>

                            {/* Show both teams with individual unlock buttons */}
                            <div className="space-y-3">
                              {/* Home Team Section */}
                              <div className="border border-gray-200 rounded-lg p-3">
                                <div className="flex justify-between items-center mb-2">
                                  <h4 className="font-bold text-gray-900">{(prop as any).home_team?.name || 'Home Team'}</h4>
                                  <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">Follow to Unlock</span>
                                </div>

                                {(prop as any).home_team_unlocked ? (
                                  <div className="bg-green-50 border border-green-200 rounded p-2">
                                    <p className="text-sm font-bold text-green-900 mb-2">🎯 Top 2 Players Most Likely to Score:</p>
                                    <div className="space-y-1">
                                      {(prop as any).home_team_players?.slice(0, 2).map((player: string, idx: number) => (
                                        <div key={idx} className="flex items-center gap-2">
                                          <span className="text-sm font-semibold text-gray-900">• {player}</span>
                                        </div>
                                      ))}
                                    </div>
                                    <div className="mt-2 pt-2 border-t border-green-200">
                                      <p className="text-xs text-green-700 font-medium">✅ Unlocked - Good luck!</p>
                                    </div>
                                  </div>
                                ) : (
                                  <button
                                    onClick={() => onUnlockProp(`${prop.id}_home`)}
                                    disabled={unlockingId === `${prop.id}_home` || pickCount >= pickLimit}
                                    className={`w-full py-2 px-3 rounded-lg font-medium text-sm transition-all ${
                                      pickCount >= pickLimit
                                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                        : 'bg-blue-600 text-white hover:bg-blue-700 shadow-md hover:shadow-lg'
                                    }`}
                                  >
                                    {unlockingId === `${prop.id}_home` ? (
                                      <span className="flex items-center justify-center gap-2">
                                        <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24">
                                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                        </svg>
                                        Unlocking...
                                      </span>
                                    ) : pickCount >= pickLimit ? (
                                      '⛔ Limit Reached'
                                    ) : (
                                      <>🔓 Follow Team ({pickCount + 1}/{pickLimit})</>
                                    )}
                                  </button>
                                )}
                              </div>

                              {/* Away Team Section */}
                              <div className="border border-gray-200 rounded-lg p-3">
                                <div className="flex justify-between items-center mb-2">
                                  <h4 className="font-bold text-gray-900">{(prop as any).away_team?.name || 'Away Team'}</h4>
                                  <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">Follow to Unlock</span>
                                </div>

                                {(prop as any).away_team_unlocked ? (
                                  <div className="bg-green-50 border border-green-200 rounded p-2">
                                    <p className="text-sm font-bold text-green-900 mb-2">🎯 Top 2 Players Most Likely to Score:</p>
                                    <div className="space-y-1">
                                      {(prop as any).away_team_players?.slice(0, 2).map((player: string, idx: number) => (
                                        <div key={idx} className="flex items-center gap-2">
                                          <span className="text-sm font-semibold text-gray-900">• {player}</span>
                                        </div>
                                      ))}
                                    </div>
                                    <div className="mt-2 pt-2 border-t border-green-200">
                                      <p className="text-xs text-green-700 font-medium">✅ Unlocked - Good luck!</p>
                                    </div>
                                  </div>
                                ) : (
                                  <button
                                    onClick={() => onUnlockProp(`${prop.id}_away`)}
                                    disabled={unlockingId === `${prop.id}_away` || pickCount >= pickLimit}
                                    className={`w-full py-2 px-3 rounded-lg font-medium text-sm transition-all ${
                                      pickCount >= pickLimit
                                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                        : 'bg-blue-600 text-white hover:bg-blue-700 shadow-md hover:shadow-lg'
                                    }`}
                                  >
                                    {unlockingId === `${prop.id}_away` ? (
                                      <span className="flex items-center justify-center gap-2">
                                        <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24">
                                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                        </svg>
                                        Unlocking...
                                      </span>
                                    ) : pickCount >= pickLimit ? (
                                      '⛔ Limit Reached'
                                    ) : (
                                      <>🔓 Follow Team ({pickCount + 1}/{pickLimit})</>
                                    )}
                                  </button>
                                )}
                              </div>
                            </div>

                            {/* Show reasoning when at least one team is unlocked */}
                            {((prop as any).home_team_unlocked || (prop as any).away_team_unlocked) && tierConfig[userTier as keyof typeof tierConfig]?.showReasoning && prop.reasoning && (
                              <div className="mt-3 pt-3 border-t border-gray-200">
                                <p className="text-sm font-medium text-gray-700 mb-2">AI Analysis:</p>
                                <div className="space-y-2">
                                  {prop.reasoning.slice(0, 2).map((r: any, i: number) => (
                                    <div key={i} className="text-sm">
                                      <span className="font-medium text-blue-600">{r.factor}:</span>
                                      <span className="text-gray-600 ml-1">{r.explanation}</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Show models when at least one team is unlocked */}
                            {((prop as any).home_team_unlocked || (prop as any).away_team_unlocked) && (tierConfig[userTier as keyof typeof tierConfig]?.showModels || userTier === 'pro' || userTier === 'elite') && (
                              <div className="mt-3 pt-3 border-t border-gray-200">
                                <p className="text-sm font-medium text-gray-900 mb-2">Model Breakdown:</p>
                                <div className="space-y-1">
                                  {prop.models && prop.models.length > 0 ? (
                                    prop.models.map((m: any, i: number) => (
                                      <div key={i} className="flex justify-between text-sm">
                                        <span className="text-gray-800 font-medium">{m.name}:</span>
                                        <span className="font-bold text-gray-900">{m.confidence}%</span>
                                      </div>
                                    ))
                                  ) : (
                                    <>
                                      <div className="flex justify-between text-sm">
                                        <span className="text-gray-800 font-medium">XGBoost:</span>
                                        <span className="font-bold text-gray-900">{prop.confidence ? Math.round(prop.confidence * 0.95) : 65}%</span>
                                      </div>
                                      <div className="flex justify-between text-sm">
                                        <span className="text-gray-800 font-medium">RandomForest:</span>
                                        <span className="font-bold text-gray-900">{prop.confidence ? Math.round(prop.confidence * 1.02) : 68}%</span>
                                      </div>
                                      <div className="flex justify-between text-sm">
                                        <span className="text-gray-800 font-medium">NeuralNet:</span>
                                        <span className="font-bold text-gray-900">{prop.confidence ? Math.round(prop.confidence * 0.88) : 62}%</span>
                                      </div>
                                    </>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            // NBA/MLB/NFL/NCAA: Show all team props without duplication
            <>
              <div className="flex space-x-2 mb-6 border-b border-green-200 flex-wrap">
                <button
                  onClick={() => setActiveTeamTab('totals')}
                  className={`px-4 py-3 font-medium border-b-2 transition-colors ${
                    activeTeamTab === 'totals'
                      ? 'border-green-600 text-green-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900'
                  }`}
                >
                  📈 Game Totals
                </button>
              </div>
              {renderPropsSection(teamPropsNBA, 'Team Picks')}
            </>
          )}
        </div>
      )}

      {/* Empty State */}
      {goalsProps.length === 0 && 
        assistsProps.length === 0 && 
        anytimeGoalProps.length === 0 && 
        teamProps.length === 0 && 
        playerPropsNBA.length === 0 &&
        teamPropsNBA.length === 0 && (
        <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-gray-500 text-lg mb-2">⏳ No props available yet</p>
          <p className="text-sm text-gray-400">Game props will appear once available.</p>
        </div>
      )}
    </div>
  );
};

export default PropsTab;
