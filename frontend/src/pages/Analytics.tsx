/**
 * Analytics Dashboard Page
 * Shows prediction accuracy, calibration, and performance metrics
 */

import React, { useEffect, useState } from 'react';
import { BarChart, Bar, LineChart, Line, ComposedChart, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import axios from 'axios';

interface AccuracyMetrics {
  total_predictions: number;
  win_rate: number;
  roi: number;
  calibration_error: number;
  by_sport: Record<string, { accuracy: number; count: number; roi: number }>;
  confidence_bins: Record<string, { accuracy: number; count: number; expected: number }>;
  generated_at: string;
}

interface CalibrationPoint {
  confidence: number;
  actual_accuracy: number;
  count: number;
}

interface Prediction {
  id: number;
  sport_key: string;
  market_type: string;
  prediction: string;
  confidence: number;
  created_at: string;
  resolved_at: string | null;
  result: string | null;
}

interface PredictionListResponse {
  total: number;
  offset: number;
  limit: number;
  predictions: Prediction[];
}

interface Summary {
  summary: Record<string, { total: number; accuracy: number; roi: number; calibration: number }>;
}

const AnalyticsDashboard: React.FC = () => {
  const [timeRange, setTimeRange] = useState('30');
  const [metrics, setMetrics] = useState<AccuracyMetrics | null>(null);
  const [calibrationData, setCalibrationData] = useState<CalibrationPoint[]>([]);
  const [perfectCalibration, setPerfectCalibration] = useState<{ confidence: number; actual_accuracy: number }[]>([]);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sportFilter, setSportFilter] = useState<string>('');

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange, sportFilter]);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = { days: parseInt(timeRange) };
      if (sportFilter) Object.assign(params, { sport_key: sportFilter });

      const [metricsRes, calibrationRes, predictionsRes, summaryRes] = await Promise.all([
        axios.get('/api/analytics/accuracy', { params }),
        axios.get('/api/analytics/calibration', { params: { days: parseInt(timeRange) } }),
        axios.get('/api/analytics/predictions', { params: { ...params, limit: 50 } }),
        axios.get('/api/analytics/summary'),
      ]);

      setMetrics(metricsRes.data);
      setCalibrationData(calibrationRes.data.calibration_data);
      setPerfectCalibration(calibrationRes.data.perfect_calibration);
      setPredictions(predictionsRes.data.predictions);
      setSummary(summaryRes.data);
    } catch (err: any) {
      console.error('Error fetching analytics:', err);
      setError('Failed to load analytics data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400 mb-4"></div>
          <p className="text-slate-400 text-lg">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-center max-w-md mx-auto px-6">
          <div className="text-5xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-white mb-2">Analytics Unavailable</h2>
          <p className="text-slate-400 mb-6">{error}</p>
          <button
            onClick={fetchAnalytics}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  const sportData = metrics?.by_sport ? Object.entries(metrics.by_sport).map(([sport, data]) => ({
    name: sport.replace('_', ' ').toUpperCase(),
    accuracy: Math.round(data.accuracy * 100),
    predictions: data.count,
    roi: Math.round(data.roi * 100),
  })) : [];

  const confidenceData = metrics?.confidence_bins ? Object.entries(metrics.confidence_bins).map(([range, data]) => ({
    range,
    expected: Math.round(data.expected * 100),
    actual: Math.round(data.accuracy * 100),
    count: data.count,
  })) : [];

  const thresholdColor = (value: number) => {
    if (value >= 55) return '#10b981'; // green
    if (value >= 52) return '#f59e0b'; // amber
    return '#ef4444'; // red
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Prediction Analytics</h1>
          <p className="text-slate-400">Track accuracy, confidence calibration, and ROI</p>
        </div>

        {/* Filters */}
        <div className="flex gap-4 mb-8">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-40 bg-slate-800 border-slate-700 text-white">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-slate-800 border-slate-700">
              <SelectItem value="7">Last 7 Days</SelectItem>
              <SelectItem value="14">Last 14 Days</SelectItem>
              <SelectItem value="30">Last 30 Days</SelectItem>
              <SelectItem value="90">Last 90 Days</SelectItem>
            </SelectContent>
          </Select>

          <Button onClick={fetchAnalytics} className="bg-blue-600 hover:bg-blue-700">
            Refresh
          </Button>
        </div>

        {/* Key Metrics */}
        {metrics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-slate-400">Win Rate</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-white">
                  {(metrics.win_rate * 100).toFixed(1)}%
                </div>
                <p className={`text-sm mt-2 ${metrics.win_rate >= 0.55 ? 'text-green-400' : metrics.win_rate >= 0.52 ? 'text-yellow-400' : 'text-red-400'}`}>
                  {metrics.win_rate >= 0.55 ? '✓ Excellent' : metrics.win_rate >= 0.52 ? '⚠ Acceptable' : '✗ Below Expected'}
                </p>
              </CardContent>
            </Card>

            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-slate-400">ROI</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-white">
                  {(metrics.roi * 100).toFixed(1)}%
                </div>
                <p className={`text-sm mt-2 ${metrics.roi > 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {metrics.roi > 0 ? '↑ Profitable' : '↓ Loss'}
                </p>
              </CardContent>
            </Card>

            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-slate-400">Calibration Error</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-white">
                  {(metrics.calibration_error * 100).toFixed(1)}%
                </div>
                <p className={`text-sm mt-2 ${metrics.calibration_error < 0.10 ? 'text-green-400' : metrics.calibration_error < 0.15 ? 'text-yellow-400' : 'text-red-400'}`}>
                  {metrics.calibration_error < 0.10 ? '✓ Excellent' : metrics.calibration_error < 0.15 ? '⚠ Good' : '✗ Needs Work'}
                </p>
              </CardContent>
            </Card>

            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-slate-400">Predictions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-white">
                  {metrics.total_predictions}
                </div>
                <p className="text-sm text-slate-400 mt-2">
                  Last {timeRange} days
                </p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Tabs */}
        <Tabs defaultValue="calibration" className="space-y-4">
          <TabsList className="bg-slate-800 border-slate-700">
            <TabsTrigger value="calibration">Calibration</TabsTrigger>
            <TabsTrigger value="by-sport">By Sport</TabsTrigger>
            <TabsTrigger value="confidence">Confidence Bins</TabsTrigger>
            <TabsTrigger value="predictions">Recent Predictions</TabsTrigger>
          </TabsList>

          {/* Calibration Tab */}
          <TabsContent value="calibration">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Confidence Calibration</CardTitle>
                <CardDescription className="text-slate-400">
                  Expected vs Actual accuracy: predictions should lie on the diagonal
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="confidence" name="Predicted Confidence" stroke="#94a3b8" type="number" domain={[0.5, 1]} />
                    <YAxis dataKey="actual_accuracy" name="Actual Accuracy" stroke="#94a3b8" type="number" domain={[0.5, 1]} />
                    <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                    <Legend />
                    {/* Perfect Calibration Line */}
                    <Scatter name="Perfect Calibration" data={perfectCalibration} stroke="#10b981" line />
                    {/* Actual Calibration Points */}
                    <Scatter name="Actual Results" data={calibrationData} fill="#3b82f6" />
                  </ScatterChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          {/* By Sport Tab */}
          <TabsContent value="by-sport">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Performance by Sport</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart data={sportData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="name" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                      formatter={(value: any) => `${value}%`}
                    />
                    <Legend />
                    <Bar dataKey="accuracy" fill="#3b82f6" name="Accuracy %" radius={[8, 8, 0, 0]}>
                      {sportData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={thresholdColor(entry.accuracy)} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Confidence Bins Tab */}
          <TabsContent value="confidence">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Accuracy by Confidence Level</CardTitle>
                <CardDescription className="text-slate-400">
                  How well confidence aligns with actual results
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <ComposedChart data={confidenceData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="range" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                      formatter={(value: any) => `${value}%`}
                    />
                    <Legend />
                    <Bar dataKey="expected" fill="#10b981" name="Expected %" radius={[8, 8, 0, 0]} />
                    <Bar dataKey="actual" fill="#3b82f6" name="Actual %" radius={[8, 8, 0, 0]} />
                  </ComposedChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Recent Predictions Tab */}
          <TabsContent value="predictions">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Recent Predictions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm text-slate-300">
                    <thead className="border-b border-slate-700">
                      <tr>
                        <th className="text-left py-3 px-4 font-medium">Sport</th>
                        <th className="text-left py-3 px-4 font-medium">Market</th>
                        <th className="text-left py-3 px-4 font-medium">Prediction</th>
                        <th className="text-left py-3 px-4 font-medium">Confidence</th>
                        <th className="text-left py-3 px-4 font-medium">Result</th>
                        <th className="text-left py-3 px-4 font-medium">Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {predictions.map((pred) => (
                        <tr key={pred.id} className="border-b border-slate-700 hover:bg-slate-700/30">
                          <td className="py-3 px-4">{pred.sport_key}</td>
                          <td className="py-3 px-4">{pred.market_type}</td>
                          <td className="py-3 px-4">{pred.prediction}</td>
                          <td className="py-3 px-4">
                            <span className={`font-medium ${
                              pred.confidence >= 60 ? 'text-green-400' :
                              pred.confidence >= 55 ? 'text-yellow-400' :
                              'text-red-400'
                            }`}>
                              {pred.confidence}%
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            {pred.result ? (
                              <span className={pred.result === 'Win' ? 'text-green-400 font-medium' : 'text-red-400 font-medium'}>
                                {pred.result}
                              </span>
                            ) : (
                              <span className="text-slate-500">Pending</span>
                            )}
                          </td>
                          <td className="py-3 px-4 text-slate-500">
                            {new Date(pred.created_at).toLocaleDateString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Time Range Summary (Optional Footer) */}
        {summary && (
          <Card className="mt-8 bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">30/14/7 Day Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                {Object.entries(summary.summary || {}).map(([period, data]) => (
                  <div key={period} className="bg-slate-700/50 p-4 rounded">
                    <h4 className="text-slate-300 font-medium mb-2">{period.replace('_', ' ').toUpperCase()}</h4>
                    <div className="space-y-1 text-sm">
                      <p className="text-slate-400">Predictions: <span className="text-white font-medium">{data.total}</span></p>
                      <p className="text-slate-400">Accuracy: <span className="text-white font-medium">{(data.accuracy * 100).toFixed(1)}%</span></p>
                      <p className="text-slate-400">ROI: <span className={`font-medium ${data.roi > 0 ? 'text-green-400' : 'text-red-400'}`}>{(data.roi * 100).toFixed(1)}%</span></p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
