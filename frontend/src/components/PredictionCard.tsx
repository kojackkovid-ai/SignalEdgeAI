import React from 'react';
import ConfidenceGauge from './ConfidenceGauge';
import { analyticsTracker } from '../utils/analytics';

interface ReasoningPoint {
  factor: string;
  impact: string;
  weight: number;
  explanation: string;
}

interface ModelEnsemble {
  name: string;
  prediction?: string;
  confidence?: number;
  weight: number;
}

interface PredictionCardProps {
  id?: string;
  sport: string;
  league: string;
  matchup: string;
  game_time?: string;
  prediction: string;
  confidence: number;
  odds?: string;
  prediction_type?: string;
  reasoning?: ReasoningPoint[];
  models?: ModelEnsemble[];
  created_at?: string;
  resolved_at?: string;
  result?: string;
  userTier?: string;
  pickCount?: number;
  maxPicks?: number;
  featured?: boolean;
  is_locked?: boolean;
  onViewDetails?: (prediction: any) => void;
  player?: string;
  season_avg?: number;
  recent_10_avg?: number;
  point?: number;
}

export const PredictionCard: React.FC<PredictionCardProps> = ({
  id,
  sport,
  league,
  matchup,
  game_time,
  prediction,
  confidence,
  odds,
  prediction_type,
  reasoning = [],
  models = [],
  created_at,
  resolved_at,
  result,
  userTier = 'free',
  pickCount = 0,
  maxPicks = 1,
  featured = false,
  is_locked = false,
  onViewDetails,
  player,
  season_avg,
  recent_10_avg,
  point,
}) => {
  // Debug logging
  console.log('[PredictionCard] Rendering with props:', {
    id, sport, league, matchup, prediction, confidence, userTier
  });

  const handleViewDetails = () => {
    // Track prediction view
    if (id) {
      analyticsTracker.trackPredictionView('', sport, id).catch(() => {});
    }
    
    if (onViewDetails) {
      onViewDetails({
        id,
        sport,
        league,
        matchup,
        game_time,
        prediction,
        confidence,
        odds,
        prediction_type,
        reasoning,
        models,
        created_at,
        resolved_at,
        result,
        is_locked,
        player,
        season_avg,
        recent_10_avg,
        point,
      });
    }
  };

  const getPredictionColor = (conf: number) => {
    // Dark colors for readability on white background
    if (conf >= 75) return '#166534'; // Dark green
    if (conf >= 50) return '#92400e'; // Dark amber/brown
    return '#991b1b'; // Dark red
  };

  const getTypeLabel = (t: string) => {
    const labels = {
      player_prop: 'PLAYER PROP',
      team_prop: 'TEAM PROP',
      over_under: 'O/U'
    };
    return labels[t as keyof typeof labels] || t;
  };

  // Tier-based feature gating according to subscription levels
  // Starter (Free): Sport & matchup info, AI prediction, Confidence score, 1 pick/day
  // Basic: Everything in Starter + Live odds data, Reasoning analysis, 10 picks/day
  // Pro: Everything in Basic + Model ensemble breakdown, Individual model predictions, 25 picks/day
  // Ultimate: Everything in Pro + Full reasoning breakdown, All 4 ML models detailed, Unlimited picks
  
  const normalizedTier = userTier?.toLowerCase() || 'starter';
  const isStarter = normalizedTier === 'starter' || normalizedTier === 'free';
  const isBasic = normalizedTier === 'basic';
  const isPro = normalizedTier === 'pro';
  const isUltimate = normalizedTier === 'ultimate';
 
  // Determine if user can pick
  const canPick = isUltimate || pickCount < maxPicks;

  // Safe array handling
  const safeReasoning = Array.isArray(reasoning) ? reasoning : [];
  const safeModels = Array.isArray(models) ? models : [];

  // Debug: Log what will be rendered
  console.log('[PredictionCard] Render state:', {
    normalizedTier, isStarter, isBasic, isPro, isUltimate,
    canPick, pickCount, maxPicks,
    safeReasoningLength: safeReasoning.length,
    safeModelsLength: safeModels.length
  });

  return (
    <div className={`prediction-card bg-white rounded-lg shadow-md p-4 ${featured ? 'featured' : ''} ${is_locked ? 'locked' : ''}`}>
      {/* Header */}
      <div className="flex justify-between items-start mb-3">
        <div>
          <span className="text-xs font-bold text-blue-600 uppercase tracking-wider">
            {sport}
          </span>
          <h3 className="text-lg font-bold text-gray-900 leading-tight mt-1">
            {matchup || 'Unknown Matchup'}
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            {game_time || 'TBD'}
          </p>
        </div>
        {is_locked && (
          <div className="bg-gray-700 rounded-full p-2">
            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
        )}
      </div>

      {/* Prediction Type Badge */}
      {prediction_type && (
        <div className="mb-3">
          <span className="inline-block px-2 py-1 text-xs font-semibold bg-blue-100 text-blue-800 rounded">
            {getTypeLabel(prediction_type)}
          </span>
        </div>
      )}

      {/* Player Info and Stats - for player props */}
      {prediction_type === 'player_prop' && player && (
        <div className="mb-4 p-3 bg-pink-50 border border-pink-200 rounded-lg">
          <p className="text-sm font-bold text-pink-900 mb-2">{player}</p>
          <div className="grid grid-cols-2 gap-3">
            {season_avg !== undefined && season_avg !== null && (
              <div className="text-sm">
                <p className="text-xs text-gray-600 font-medium">Season Avg</p>
                <p className="text-lg font-bold text-pink-700">{season_avg}</p>
              </div>
            )}
            {recent_10_avg !== undefined && recent_10_avg !== null && (
              <div className="text-sm">
                <p className="text-xs text-gray-600 font-medium">Last 10 Avg</p>
                <p className="text-lg font-bold text-pink-700">{recent_10_avg}</p>
              </div>
            )}
            {point !== undefined && point !== null && (
              <div className="text-sm">
                <p className="text-xs text-gray-600 font-medium">Line</p>
                <p className="text-lg font-bold text-blue-700">{point}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Main Prediction - MASKED until unlocked */}
      <div className="mb-4">
        <p className="text-sm text-gray-600 mb-1">AI Prediction</p>
        <p className="text-2xl font-bold" style={{ color: is_locked ? '#6b7280' : getPredictionColor(confidence || 0) }}>
          {is_locked ? '🔒 Unlock to see prediction' : (prediction || 'N/A')}
        </p>
      </div>

      {/* Confidence Gauge */}
      <div className="mb-4">
        <ConfidenceGauge confidence={confidence || 0} />
      </div>

      {/* Odds - Basic tier and above */}
      {!isStarter && odds && (
        <div className="mb-3 p-2 bg-gray-100 rounded">
          <p className="text-xs text-gray-600">Market Odds</p>
          <p className="text-sm font-mono text-green-600">{odds}</p>
        </div>
      )}

      {/* Reasoning - Basic tier and above */}
      {!isStarter && safeReasoning.length > 0 && (
        <div className="mb-4">
          <p className="text-sm font-medium text-gray-700 mb-2">Key Factors:</p>
          <div className="space-y-2">
            {safeReasoning.slice(0, isBasic ? 2 : undefined).map((point, idx) => (
              <div key={idx} className="text-sm">
                <span className="text-blue-600 font-medium">{point.factor}:</span>
                <span className="text-gray-600 ml-1">{point.explanation}</span>
              </div>
            ))}
          </div>
          {isBasic && safeReasoning.length > 2 && (
            <p className="text-xs text-gray-500 mt-2 italic">
              Upgrade to Pro for full analysis
            </p>
          )}
        </div>
      )}

      {/* Model Ensemble - Pro and Ultimate only */}
      {(isPro || isUltimate) && safeModels.length > 0 && (
        <div className="mb-4 p-3 bg-gray-100 rounded-lg">
          <p className="text-sm font-medium text-gray-900 mb-2">Model Consensus</p>
          <div className="space-y-2">
            {safeModels.slice(0, isUltimate ? undefined : 3).map((model, idx) => (
              <div key={idx} className="flex items-center justify-between text-sm">
                <span className="text-gray-800 font-medium">{model.name}</span>
                <div className="flex items-center gap-2">
                  <div className="w-24 h-2 bg-gray-300 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-blue-500"
                      style={{ width: `${(model.weight || 0) * 100}%` }}
                    />
                  </div>
                  <span className="text-blue-800 font-bold font-mono">
                    {((model.weight || 0) * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
          {!isUltimate && safeModels.length > 3 && (
            <p className="text-xs text-gray-600 mt-2 italic">
              Upgrade to Ultimate for all models
            </p>
          )}
        </div>
      )}

      {/* Ultimate Badge */}
      {isUltimate && (
        <div className="mb-3 flex items-center gap-2 text-purple-400">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
          <span className="text-xs font-bold uppercase">Ultimate Access</span>
        </div>
      )}

      {/* Action Button */}
      <button
        onClick={handleViewDetails}
        disabled={!canPick}
        className={`w-full py-2 px-4 rounded font-medium transition-colors ${
          canPick
            ? 'bg-blue-600 hover:bg-blue-500 text-white'
            : 'bg-gray-200 text-gray-500 cursor-not-allowed'
        }`}
      >
        {canPick ? (
          is_locked ? '🔓 Unlock Pick' : '🎯 View Details'
        ) : (
          '⛔ Daily Limit Reached'
        )}
      </button>

      {/* Pick Counter */}
      <div className="mt-3 text-center">
        <p className="text-xs text-gray-500">
          {isUltimate ? (
            '♾️ Unlimited picks'
          ) : (
            `${pickCount} / ${maxPicks} picks used today`
          )}
        </p>
      </div>
    </div>
  );
};

export default PredictionCard;
