import React, { useState } from 'react';

interface Club100Status {
  accessible: boolean;
  daily_picks_used: number;
  daily_picks_limit: number;
  club_100_view_cost: number;
  club_100_follow_cost: number;
  reason?: string;
}

interface Club100UnlockModalProps {
  isOpen: boolean;
  onClose: () => void;
  status: Club100Status | null;
}

const Club100UnlockModal: React.FC<Club100UnlockModalProps> = ({
  isOpen,
  onClose,
  status,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full mx-4 overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-amber-500 to-orange-500 px-8 py-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-4xl">🏆</span>
            <h2 className="text-3xl font-black text-white">Club 100</h2>
            <span className="text-4xl">🏆</span>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:bg-white/20 rounded-full p-2 transition-all"
          >
            <span className="text-2xl">✕</span>
          </button>
        </div>

        {/* Content */}
        <div className="p-8">
          {/* Club 100 Always Accessible */}
          <div>
            <div className="mb-8 text-center">
              <div className="text-6xl mb-4">✨</div>
              <h3 className="text-3xl font-bold text-gray-900 mb-2">Club 100 - Elite Players!</h3>
              <p className="text-xl text-gray-600">
                Access exclusive player performance data
              </p>
            </div>

            {/* How It Works */}
            <div className="bg-gradient-to-r from-amber-50 to-orange-50 border-2 border-amber-200 rounded-xl p-6 mb-8">
              <h4 className="text-lg font-bold text-gray-900 mb-4">How Club 100 Works:</h4>
              <div className="space-y-3 text-gray-700">
                <p>🔓 <span className="font-semibold">Always Accessible</span> - View anytime with no restrictions!</p>
                <p>💰 <span className="font-semibold">5 Picks to View</span> - Deducted when you access Club 100 players</p>
                <p>📊 <span className="font-semibold">Browse Player Data</span> - See who's clearing their prop lines</p>
                <p>⚡ <span className="font-semibold">1 Pick to Follow</span> - Follow any player for 1 daily pick (regular cost)</p>
                <p>🎯 <span className="font-semibold">Last 4 & 5 Games</span> - Performance data across all sports</p>
              </div>
            </div>

            {/* Daily Picks Display */}
            <div className="grid grid-cols-2 gap-4 mb-8">
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 border-2 border-blue-200 rounded-lg p-4 text-center">
                <div className="text-3xl mb-2">📈</div>
                <p className="text-sm font-bold text-gray-600">Daily Picks Used</p>
                <p className="text-2xl font-black text-blue-900">
                  {status?.daily_picks_used || 0} / {status?.daily_picks_limit || 1}
                </p>
              </div>
              <div className="bg-gradient-to-br from-orange-50 to-orange-100 border-2 border-orange-200 rounded-lg p-4 text-center">
                <div className="text-3xl mb-2">👁️</div>
                <p className="text-sm font-bold text-gray-600">View Cost</p>
                <p className="text-2xl font-black text-orange-900">
                  {status?.club_100_view_cost || 5} Picks
                </p>
              </div>
            </div>

            {/* Features */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
              <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4">
                <div className="text-2xl mb-2">📊</div>
                <h4 className="font-bold text-gray-900 mb-2">Last 4 Games</h4>
                <p className="text-sm text-gray-600">Short-term performance trends</p>
              </div>
              <div className="bg-purple-50 border-2 border-purple-200 rounded-lg p-4">
                <div className="text-2xl mb-2">⚡</div>
                <h4 className="font-bold text-gray-900 mb-2">Last 5 Games</h4>
                <p className="text-sm text-gray-600">Extended performance analysis</p>
              </div>
              <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4">
                <div className="text-2xl mb-2">🏀</div>
                <h4 className="font-bold text-gray-900 mb-2">All Sports</h4>
                <p className="text-sm text-gray-600">NBA, NFL, MLB, NHL & Soccer</p>
              </div>
              <div className="bg-pink-50 border-2 border-pink-200 rounded-lg p-4">
                <div className="text-2xl mb-2">🎯</div>
                <h4 className="font-bold text-gray-900 mb-2">Smart Organization</h4>
                <p className="text-sm text-gray-600">Filtered by sport & performance</p>
              </div>
            </div>

            {/* Action Button */}
            <button
              onClick={onClose}
              className="w-full py-4 font-bold text-lg rounded-xl transition-all flex items-center justify-center gap-2 bg-gradient-to-r from-amber-500 to-orange-500 text-white hover:shadow-2xl hover:-translate-y-1"
            >
              ✨ View Club 100 Data
            </button>

            <div className="text-center text-sm text-gray-600 mt-4">
              <p className="text-green-600">
                ✅ You can access Club 100! Viewing costs 5 picks. Following players costs 1 pick each.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Club100UnlockModal;
