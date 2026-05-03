import React, { useEffect, useState } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';

interface ModelPerf { sport: string; accuracy: number; total_predictions: number; correct_predictions: number; }

const AdminDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'analytics' | 'models' | 'health' | 'settings'>('overview');
  const [stats, setStats] = useState({
    totalUsers: 0,
    activeUsers: 0,
    monthlyRevenue: 0,
    activeSubscriptions: 0,
    predictions: 0,
    accuracy: 0
  });
  const [tierData, setTierData] = useState<{ name: string; value: number }[]>([]);
  const [modelPerf, setModelPerf] = useState<ModelPerf[]>([]);
  const [statsLoading, setStatsLoading] = useState(true);

  useEffect(() => {
    fetchAdminStats();
  }, []);

  const fetchAdminStats = async () => {
    setStatsLoading(true);
    try {
      const [statsRes, tiersRes, modelsRes] = await Promise.allSettled([
        api.get('/admin/stats'),
        api.get('/admin/tiers'),
        api.get('/admin/models/performance'),
      ]);

      if (statsRes.status === 'fulfilled') {
        const s = statsRes.value.data;
        setStats({
          totalUsers: s.total_users ?? 0,
          activeUsers: s.active_users ?? 0,
          monthlyRevenue: s.monthly_revenue ?? 0,
          activeSubscriptions: s.active_subscriptions ?? 0,
          predictions: s.total_predictions ?? 0,
          accuracy: s.platform_accuracy ?? 0,
        });
      }

      if (tiersRes.status === 'fulfilled') {
        const t = tiersRes.value.data as Record<string, number>;
        setTierData(Object.entries(t).map(([name, value]) => ({ name, value })));
      }

      if (modelsRes.status === 'fulfilled') {
        setModelPerf(modelsRes.value.data as ModelPerf[]);
      }
    } catch (err) {
      // Stats unavailable — keep zeros shown
    } finally {
      setStatsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
            <button 
              onClick={() => navigate('/dashboard')}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
            >
              ← Back to Dashboard
            </button>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {[
              { id: 'overview', label: '📊 Overview', icon: '📊' },
              { id: 'users', label: '👥 Users', icon: '👥' },
              { id: 'analytics', label: '💰 Analytics', icon: '💰' },
              { id: 'models', label: '🤖 Models', icon: '🤖' },
              { id: 'health', label: '❤️ Health', icon: '❤️' },
              { id: 'settings', label: '⚙️ Settings', icon: '⚙️' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-4 py-3 border-b-2 font-medium text-sm whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="bg-white rounded-lg shadow p-6">
                <p className="text-sm text-gray-600">Total Users</p>
                <p className="text-3xl font-bold text-blue-600 mt-2">{statsLoading ? '—' : stats.totalUsers.toLocaleString()}</p>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <p className="text-sm text-gray-600">Monthly Revenue</p>
                <p className="text-3xl font-bold text-green-600 mt-2">{statsLoading ? '—' : `$${stats.monthlyRevenue.toLocaleString()}`}</p>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <p className="text-sm text-gray-600">Active Subscriptions</p>
                <p className="text-3xl font-bold text-purple-600 mt-2">{statsLoading ? '—' : stats.activeSubscriptions.toLocaleString()}</p>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <p className="text-sm text-gray-600">Platform Accuracy</p>
                <p className="text-3xl font-bold text-orange-600 mt-2">{statsLoading ? '—' : `${stats.accuracy.toFixed(1)}%`}</p>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <p className="text-sm text-gray-600">Total Predictions</p>
                <p className="text-3xl font-bold text-indigo-600 mt-2">{statsLoading ? '—' : stats.predictions.toLocaleString()}</p>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <p className="text-sm text-gray-600">Active Users</p>
                <p className="text-3xl font-bold text-pink-600 mt-2">{statsLoading ? '—' : stats.activeUsers.toLocaleString()}</p>
              </div>
            </div>

            {/* Revenue Chart */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-bold mb-4">Monthly Revenue Trend</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={[
                  { month: 'Jan', revenue: 12000 },
                  { month: 'Feb', revenue: 15000 },
                  { month: 'Mar', revenue: 18000 },
                  { month: 'Apr', revenue: 24500 }
                ]}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip formatter={(value) => `$${value}`} />
                  <Legend />
                  <Line type="monotone" dataKey="revenue" stroke="#2563eb" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Subscription Distribution */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-bold mb-4">Subscription Tier Distribution</h3>
              {tierData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={tierData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, value }) => `${name}: ${value}`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {tierData.map((_, i) => (
                        <Cell key={i} fill={['#3b82f6','#10b981','#8b5cf6','#f59e0b','#ef4444'][i % 5]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <p className="text-center text-gray-400 py-12">{statsLoading ? 'Loading…' : 'No tier data available'}</p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'users' && (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-bold">User Management</h3>
              <input 
                type="text" 
                placeholder="Search users..."
                className="px-4 py-2 border rounded-lg"
              />
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4">Email</th>
                    <th className="text-left py-3 px-4">Tier</th>
                    <th className="text-left py-3 px-4">Joined</th>
                    <th className="text-left py-3 px-4">Status</th>
                    <th className="text-left py-3 px-4">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4">user@example.com</td>
                    <td className="py-3 px-4"><span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">Basic</span></td>
                    <td className="py-3 px-4">2026-04-01</td>
                    <td className="py-3 px-4"><span className="px-2 py-1 bg-green-100 text-green-800 rounded text-sm">Active</span></td>
                    <td className="py-3 px-4">
                      <button className="text-blue-600 hover:text-blue-800 text-sm">Edit</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-bold mb-4">Payment Analytics</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={[
                { tier: 'Free', users: 400, revenue: 0 },
                { tier: 'Basic', users: 250, revenue: 3000 },
                { tier: 'Pro', users: 180, revenue: 5220 },
                { tier: 'Pro Plus', users: 50, revenue: 2450 },
                { tier: 'Elite', users: 20, revenue: 1980 }
              ]}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="tier" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="users" fill="#3b82f6" />
                <Bar dataKey="revenue" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {activeTab === 'models' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-bold mb-4">ML Model Performance</h3>
            <div className="space-y-4">
              {modelPerf.length > 0 ? modelPerf.map((m) => (
                <div key={m.sport} className="p-4 border rounded-lg">
                  <div className="flex justify-between items-center">
                    <span className="font-medium">{m.sport}</span>
                    <span className={`font-semibold ${m.accuracy >= 55 ? 'text-green-600' : m.accuracy >= 50 ? 'text-yellow-600' : 'text-gray-400'}`}>
                      {m.total_predictions > 0 ? `${m.accuracy.toFixed(1)}%` : 'No data yet'}
                    </span>
                  </div>
                  {m.total_predictions > 0 && (
                    <>
                      <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                        <div className="bg-green-500 h-2 rounded-full" style={{ width: `${Math.min(m.accuracy, 100)}%` }} />
                      </div>
                      <p className="text-xs text-gray-500 mt-1">{m.correct_predictions} / {m.total_predictions} resolved predictions</p>
                    </>
                  )}
                </div>
              )) : (
                <p className="text-center text-gray-400 py-8">{statsLoading ? 'Loading…' : 'No model performance data available'}</p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'health' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { name: 'API Server', status: 'healthy', uptime: '99.9%' },
              { name: 'Database', status: 'healthy', uptime: '99.95%' },
              { name: 'Cache Layer', status: 'healthy', uptime: '99.8%' },
              { name: 'ML Worker', status: 'healthy', uptime: '98.5%' }
            ].map((service) => (
              <div key={service.name} className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium">{service.name}</h4>
                  <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">✓ {service.status}</span>
                </div>
                <p className="text-sm text-gray-600 mt-2">Uptime: {service.uptime}</p>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-bold mb-4">Tier Configuration</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Basic Tier Daily Picks</label>
                  <input type="number" defaultValue={10} className="w-full px-4 py-2 border rounded-lg" />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Pro Tier Daily Picks</label>
                  <input type="number" defaultValue={25} className="w-full px-4 py-2 border rounded-lg" />
                </div>
                <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  Save Changes
                </button>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-bold mb-4">Feature Flags</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span>Club 100 Feature</span>
                  <input type="checkbox" defaultChecked className="w-5 h-5" />
                </div>
                <div className="flex items-center justify-between">
                  <span>Referral Program</span>
                  <input type="checkbox" className="w-5 h-5" />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;
