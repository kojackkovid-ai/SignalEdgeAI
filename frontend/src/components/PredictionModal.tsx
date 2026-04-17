import React from 'react';
import ConfidenceGauge from './ConfidenceGauge';

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

interface PredictionModalProps {
  isOpen: boolean;
  onClose: () => void;
  sport: string;
  league: string;
  matchup: string;
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
  id?: string;
  onPick?: () => void;
  isPickingLoading?: boolean;
  canPick?: boolean;
}


const PredictionModal: React.FC<PredictionModalProps> = ({
  isOpen,
  onClose,
  sport,
  league,
  matchup,
  prediction,
  confidence,
  odds,
  prediction_type,
  reasoning = [],
  models = [],
  created_at,
  userTier = 'free',
  onPick,
  canPick = true,
}) => {
  if (!isOpen) return null;

  const getPredictionColor = (conf: number) => {
    if (conf >= 75) return '#00ff00';
    if (conf >= 50) return '#ffff00';
    return '#ff0055';
  };

  const getTypeLabel = (t: string) => {
    const labels = {
      player_prop: 'PLAYER PROP',
      team_prop: 'TEAM PROP',
      over_under: 'O/U',
      moneyline: 'MONEYLINE',
    };
    return labels[t as keyof typeof labels] || t;
  };

  const showOdds = userTier === 'basic' || userTier === 'pro' || userTier === 'elite';
  const showReasoning = userTier === 'basic' || userTier === 'pro' || userTier === 'elite';
  const showModels = userTier === 'pro' || userTier === 'elite';

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="glass-tactical max-w-2xl w-full max-h-[90vh] overflow-y-auto p-8">
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div>
            <div className="flex gap-2 items-center mb-2">
              <span className="text-sm uppercase font-bold tracking-wider text-cyan-400">
                {sport} • {league}
              </span>
              <span className="text-sm px-3 py-1 border border-yellow-400 text-yellow-400">
                {getTypeLabel(prediction_type || '')}
              </span>
            </div>
            <h2 className="text-2xl font-bold text-white">{matchup}</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-2xl font-bold"
          >
            ✕
          </button>
        </div>

        {/* Main Prediction */}
        <div className="mb-6 p-4 bg-black bg-opacity-50 border border-gray-600 rounded">
          <div className="grid grid-cols-3 gap-4 items-center">
            <div>
              <span className="text-xs text-gray-400 uppercase">Prediction</span>
              <div
                className="text-2xl font-bold mt-2"
                style={{ color: getPredictionColor(confidence) }}
              >
                {prediction}
              </div>
            </div>
            <div className="text-center">
              <ConfidenceGauge confidence={confidence} size="lg" />
            </div>
            <div>
              <span className="text-xs text-gray-400 uppercase">Confidence</span>
              <div className="text-2xl font-bold text-white mt-2">{confidence.toFixed(1)}%</div>
            </div>
          </div>
          {showOdds && odds && (
            <div className="mt-4 pt-4 border-t border-gray-600">
              <span className="text-xs text-gray-400 uppercase">Implied Odds</span>
              <div className="text-xl font-bold text-cyan-400">{odds}</div>
            </div>
          )}
        </div>

        {/* Reasoning */}
        {showReasoning && reasoning.length > 0 && (
          <div className="mb-6">
            <h3 className="text-lg font-bold text-green-600 mb-4 uppercase tracking-wider">
              $ ANALYSIS_LOG
            </h3>
            <div className="space-y-3">
              {reasoning.map((reason, idx) => (
                <div key={idx} className="p-3 bg-white border border-gray-300 rounded shadow-sm">
                  <div className="flex justify-between items-start mb-2">
                    <span className="font-bold text-cyan-800" style={{ color: '#1e40af', fontWeight: 'bold' }}>{reason.factor}</span>
                    <span className={`text-xs px-2 py-1 rounded ${
                      reason.impact === 'Positive' ? 'bg-green-100 text-green-800 border border-green-200' : 
                      reason.impact === 'Negative' ? 'bg-red-100 text-red-800 border border-red-200' :
                      'bg-gray-100 text-gray-800 border border-gray-200'
                    }`}>
                      {reason.impact}
                    </span>
                  </div>
                  <p className="text-sm text-black mb-2" style={{ color: '#000000' }}>{reason.explanation}</p>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 border border-gray-300 bg-gray-100 rounded">
                      <div
                        className="h-full bg-yellow-500 rounded"
                        style={{ width: `${reason.weight * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-yellow-600 w-8 text-right">
                      {(reason.weight * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Model Ensemble */}
        {showModels && models.length > 0 && (
          <div className="mb-6">
            <h3 className="text-lg font-bold text-blue-600 mb-4 uppercase tracking-wider">
              ◆ ENSEMBLE WEIGHTS
            </h3>
            <div className="space-y-3">
              {models.map((model, idx) => (
                <div key={idx} className="p-3 bg-white border border-gray-300 rounded shadow-sm">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-bold text-blue-900" style={{ color: '#1e3a8a', fontWeight: 'bold' }}>{model.name}</span>
                    {model.prediction && (
                      <span className="text-sm text-blue-700" style={{ color: '#1d4ed8' }}>{model.prediction}</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-3 border border-gray-300 bg-gray-100 rounded">
                      <div
                        className="h-full bg-cyan-500 rounded"
                        style={{ width: `${model.weight * 100}%` }}
                      />
                    </div>
                    <span className="text-sm text-cyan-700" style={{ color: '#0e7490' }}>
                      {(model.weight * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Metadata */}
        <div className="mb-6 p-3 bg-black bg-opacity-50 border border-gray-600 rounded text-xs text-gray-400">
          <span>Created: {created_at ? new Date(created_at).toLocaleString() : 'N/A'}</span>
        </div>

        {/* Actions */}
        <div className="flex gap-3 border-t border-gray-700 pt-4">
          <button
            onClick={onPick}
            disabled={!canPick}
            className="btn btn-sm flex-1 text-sm"
            title={!canPick ? 'Pick limit reached' : ''}
          >
            $ ADD TO PORTFOLIO
          </button>
          <button
            onClick={onClose}
            className="btn btn-sm flex-1 text-sm bg-gray-700 hover:bg-gray-600"
          >
            CLOSE
          </button>
        </div>
      </div>
    </div>
  );
};

export default PredictionModal;
