import React, { useState, useEffect } from 'react';
import { TrendingUp, BarChart3, Award, Zap } from 'lucide-react';
import api from '../utils/api';
import { analyticsTracker } from '../utils/analytics';

interface AccuracyStats {
  total: number;
  hits: number;
  misses: number;
  win_rate: number;
  avg_confidence: number;
  roi?: number;
}

interface SportStats {
  [sport: string]: {
    total: number;
    hits: number;
    win_rate: number;
    avg_confidence: number;
  };
}

interface TrendDataPoint {
  date: string;
  accuracy: number;
  predictions_count: number;
}

interface ConfidenceCalibration {
  confidence_bucket: number;
  actual_accuracy: number;
  calibration_error: number;
}

const AccuracyDashboard: React.FC = () => {
  const [overstatsOverall, setStatsOverall] = useState<AccuracyStats | null>(null);
  const [sportStats, setSportStats] = useState<SportStats | null>(null);
  const [trendData, setTrendData] = useState<TrendDataPoint[]>([]);
  const [calibrationData, setCalibrationData] = useState<ConfidenceCalibration[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDays, setSelectedDays] = useState(30);

  useEffect(() => {
    const loadAccuracyData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Track accuracy dashboard view
        analyticsTracker.trackAccuracyDashboardView('').catch(() => {});

        // Fetch overall stats
        const statsResponse = await api.get('/user/predictions/stats');
        setStatsOverall(statsResponse.data);

        // Fetch sport-specific stats
        const sportStatsResponse = await api.get('/user/predictions/stats/by-sport');
        setSportStats(sportStatsResponse.data);

        // Fetch trend data
        const trendsResponse = await api.get('/user/predictions/stats/recent-trends', {
          params: { days: selectedDays }
        });
        setTrendData(trendsResponse.data);

        // Fetch confidence calibration data
        try {
          const calibrationResponse = await api.get('/user/predictions/confidence-calibration');
          setCalibrationData(calibrationResponse.data);
        } catch {
          // Calibration data is optional
          setCalibrationData([]);
        }

      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load accuracy metrics');
        console.error('Error loading accuracy data:', err);
      } finally {
        setLoading(false);
      }
    };

    loadAccuracyData();
  }, [selectedDays]);

  if (loading) {
    return (
      <div className="bg-gradient-to-br from-slate-950 to-slate-900 rounded-lg p-8 border border-cyan-500/20">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin mb-4">
              <TrendingUp className="w-8 h-8 text-cyan-400 mx-auto" />
            </div>
            <p className="text-slate-300">Loading accuracy metrics...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error && !overstatsOverall) {
    return (
      <div className="bg-gradient-to-br from-slate-950 to-slate-900 rounded-lg p-8 border border-red-500/20">
        <p className="text-red-400">{error}</p>
      </div>
    );
  }

  const sportList = sportStats ? Object.entries(sportStats) : [];
  const topSports = sportList.sort((a, b) => b[1].win_rate - a[1].win_rate).slice(0, 5);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <BarChart3 className="w-8 h-8 text-cyan-400" />
          <h1 className="text-3xl font-bold text-white">Accuracy Dashboard</h1>
        </div>
        <div className="flex gap-2">
          {[7, 30, 90].map((days) => (
            <button
              key={days}
              onClick={() => setSelectedDays(days)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                selectedDays === days
                  ? 'bg-cyan-500 text-slate-950'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              {days}D
            </button>
          ))}
        </div>
      </div>

      {/* Overall Stats Cards */}
      {overstatsOverall && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Win Rate Card */}
          <div className="bg-gradient-to-br from-slate-950 to-slate-900 border border-cyan-500/20 rounded-xl p-6 hover:border-cyan-500/40 transition">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-slate-400 text-sm font-medium">Win Rate</p>
                <p className="text-4xl font-bold text-cyan-400 mt-2">
                  {(overstatsOverall.win_rate * 100).toFixed(1)}%
                </p>
                <p className="text-slate-500 text-xs mt-1">
                  {overstatsOverall.hits} / {overstatsOverall.total} predictions
                </p>
              </div>
              <TrendingUp className="w-6 h-6 text-cyan-500/40" />
            </div>
          </div>

          {/* Total Predictions Card */}
          <div className="bg-gradient-to-br from-slate-950 to-slate-900 border border-purple-500/20 rounded-xl p-6 hover:border-purple-500/40 transition">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-slate-400 text-sm font-medium">Total Predictions</p>
                <p className="text-4xl font-bold text-purple-400 mt-2">{overstatsOverall.total}</p>
                <p className="text-slate-500 text-xs mt-1">
                  ~{Math.round(overstatsOverall.total / selectedDays)} per day
                </p>
              </div>
              <Award className="w-6 h-6 text-purple-500/40" />
            </div>
          </div>

          {/* Avg Confidence Card */}
          <div className="bg-gradient-to-br from-slate-950 to-slate-900 border border-green-500/20 rounded-xl p-6 hover:border-green-500/40 transition">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-slate-400 text-sm font-medium">Avg Confidence</p>
                <p className="text-4xl font-bold text-green-400 mt-2">
                  {(overstatsOverall.avg_confidence * 100).toFixed(0)}%
                </p>
                <p className="text-slate-500 text-xs mt-1">
                  {overstatsOverall.avg_confidence >= 0.7 ? '✅ Solid' : '⚠️ Cautious'}
                </p>
              </div>
              <Zap className="w-6 h-6 text-green-500/40" />
            </div>
          </div>

          {/* ROI Card (if available) */}
          {overstatsOverall.roi !== undefined && (
            <div className="bg-gradient-to-br from-slate-950 to-slate-900 border border-amber-500/20 rounded-xl p-6 hover:border-amber-500/40 transition">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-slate-400 text-sm font-medium">ROI</p>
                  <p className={`text-4xl font-bold mt-2 ${overstatsOverall.roi >= 0 ? 'text-yellow-400' : 'text-red-400'}`}>
                    {overstatsOverall.roi > 0 ? '+' : ''}{overstatsOverall.roi.toFixed(1)}%
                  </p>
                  <p className="text-slate-500 text-xs mt-1">Return on investment</p>
                </div>
                <Award className="w-6 h-6 text-amber-500/40" />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Top Sports Performance */}
      {topSports.length > 0 && (
        <div className="bg-gradient-to-br from-slate-950 to-slate-900 border border-slate-700 rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-cyan-400" />
            Top Sports Performance
          </h2>
          <div className="space-y-3">
            {topSports.map(([sport, stats]) => (
              <div key={sport} className="flex items-end justify-between bg-slate-800/50 p-4 rounded-lg">
                <div className="flex-1">
                  <p className="text-white font-medium capitalize mb-2">
                    {sport.replace('_', ' ').toUpperCase()}
                  </p>
                  <div className="flex gap-4 text-sm text-slate-400">
                    <span>Predictions: {stats.total}</span>
                    <span>Wins: {stats.hits}</span>
                    <span>Avg Confidence: {(stats.avg_confidence * 100).toFixed(0)}%</span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-cyan-400">
                    {(stats.win_rate * 100).toFixed(1)}%
                  </p>
                  <div
                    className="w-32 h-2 bg-slate-700 rounded-full overflow-hidden mt-2"
                    title={`${(stats.win_rate * 100).toFixed(1)}% accuracy`}
                  >
                    <div
                      className="h-full bg-gradient-to-r from-cyan-500 to-cyan-400 rounded-full"
                      style={{ width: `${Math.max(stats.win_rate * 100, 5)}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Trend Chart */}
      {trendData.length > 0 && (
        <div className="bg-gradient-to-br from-slate-950 to-slate-900 border border-slate-700 rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-cyan-400" />
            Accuracy Trend ({selectedDays} days)
          </h2>
          <div className="space-y-3">
            {trendData.slice(-7).reverse().map((point) => (
              <div key={point.date} className="flex items-end justify-between">
                <p className="text-sm text-slate-400 w-24">{point.date}</p>
                <div className="flex-1 mx-4">
                  <div className="w-full h-6 bg-slate-800 rounded-lg overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 flex items-center justify-center text-white text-xs font-bold relative"
                      style={{ width: `${Math.max(point.accuracy * 100, 5)}%` }}
                    >
                      {point.accuracy > 0.3 && <span>{(point.accuracy * 100).toFixed(0)}%</span>}
                    </div>
                  </div>
                </div>
                <p className="text-sm text-slate-400 w-20 text-right">
                  {point.predictions_count} picks
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Calibration Data */}
      {calibrationData.length > 0 && (
        <div className="bg-gradient-to-br from-slate-950 to-slate-900 border border-slate-700 rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5 text-cyan-400" />
            Confidence Calibration
          </h2>
          <p className="text-slate-400 text-sm mb-4">
            Shows if predicted confidence matches actual accuracy. Lower error = better calibration.
          </p>
          <div className="space-y-3">
            {calibrationData.map((item) => (
              <div key={item.confidence_bucket} className="bg-slate-800/50 p-4 rounded-lg">
                <div className="flex items-end justify-between mb-2">
                  <p className="text-white font-medium">
                    {(item.confidence_bucket * 100).toFixed(0)}% Confidence Predictions
                  </p>
                  <p className="text-sm text-slate-400">
                    Actual: {(item.actual_accuracy * 100).toFixed(1)}%
                  </p>
                </div>
                <div className="w-full h-3 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      item.calibration_error < 0.1
                        ? 'bg-green-500'
                        : item.calibration_error < 0.2
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                    }`}
                    style={{ width: `${Math.max((1 - item.calibration_error) * 100, 10)}%` }}
                  />
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Error: {(item.calibration_error * 100).toFixed(1)}%
                  {item.calibration_error < 0.1 && ' ✅ Well calibrated'}
                  {item.calibration_error >= 0.1 && item.calibration_error < 0.2 && ' ⚠️ Slightly off'}
                  {item.calibration_error >= 0.2 && ' ❌ Overconfident'}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Info Row */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 text-sm text-black">
        <p>
          📊 <strong className="text-cyan-300">Metrics automatically update</strong> as predictions resolve. Accuracy is calculated from resolved
          predictions only (hit/miss/push). ROI is estimated based on win rate.
        </p>
      </div>
    </div>
  );
};

export default AccuracyDashboard;
