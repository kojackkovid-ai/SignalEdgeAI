import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { analyticsTracker } from '../utils/analytics';

interface Prediction {
  type: 'game' | 'player' | 'team';
  title: string;
  label: string;
  confidence: string;
  reasoning: string;
}

const LandingPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'nba' | 'nfl' | 'nhl' | 'mlb'>('nba');
  
  useEffect(() => {
    window.scrollTo(0, 0);
    // Track landing page view (anonymous user, so empty userId)
    analyticsTracker.trackPageView('', 'landing');
  }, []);

  const navigate = useNavigate();
  const handleGetStarted = () => navigate('/register');
  const handleSignIn = () => navigate('/login');
  const handleViewDashboard = () => navigate('/dashboard');

  const samplePredictions: Record<string, Prediction[]> = useMemo(() => ({
    nba: [
      { type: 'game', title: 'Lakers vs Celtics', label: 'Over 228.5', confidence: '89%', reasoning: 'Both teams playing fast-paced offense' },
      { type: 'player', title: 'Luka Doncic', label: 'Points Over 30.5', confidence: '85%', reasoning: 'Avg 34.2 PPG vs defensive matchup' },
      { type: 'team', title: 'Warriors', label: 'Win Moneyline', confidence: '78%', reasoning: 'Strong defensive metrics' }
    ],
    nfl: [
      { type: 'game', title: 'Chiefs vs Bills', label: 'Over 48.5', confidence: '82%', reasoning: 'Explosive offensive capabilities' },
      { type: 'player', title: 'Patrick Mahomes', label: 'Pass Yards Over 285.5', confidence: '87%', reasoning: 'Historical avg 298 YDS' },
      { type: 'team', title: 'Ravens', label: 'Win Moneyline', confidence: '81%', reasoning: 'Run defense efficiency' }
    ],
    nhl: [
      { type: 'game', title: 'Maple Leafs vs Hurricanes', label: 'Over 6.5', confidence: '84%', reasoning: 'Both teams high-scoring' },
      { type: 'player', title: 'Connor McDavid', label: 'Points Over 1.5', confidence: '88%', reasoning: 'Leading scorer with hot streak' },
      { type: 'team', title: 'Oilers', label: 'Win Moneyline', confidence: '79%', reasoning: 'Goalie in peak form' }
    ],
    mlb: [
      { type: 'game', title: 'Yankees vs Red Sox', label: 'Over 8.5', confidence: '81%', reasoning: 'Both offenses firing' },
      { type: 'player', title: 'Shohei Ohtani', label: 'Hits Over 1.5', confidence: '86%', reasoning: 'Batting average 0.312' },
      { type: 'team', title: 'Dodgers', label: 'Win Moneyline', confidence: '80%', reasoning: 'Pitching matchup advantage' }
    ]
  }), []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-white via-blue-50 to-white">
      {/* Optimized Animated Background */}
      <div className="fixed inset-0 -z-10 overflow-hidden top-16 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-400 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-pulse will-change-transform"></div>
        <div className="absolute top-20 right-1/4 w-96 h-96 bg-purple-400 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-pulse will-change-transform" style={{ animationDelay: '2s' }}></div>
        <div className="absolute bottom-0 left-1/3 w-96 h-96 bg-indigo-400 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-pulse will-change-transform" style={{ animationDelay: '4s' }}></div>
      </div>

      {/* ============= HERO SECTION ============= */}
      <section className="pt-20 pb-24 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
        <div className="max-w-6xl mx-auto">
          <div className="flex justify-center mb-8">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-blue-100 to-purple-100 border border-blue-300 backdrop-blur-sm">
              <span className="text-xl">🎯</span>
              <span className="text-sm font-semibold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                #1 AI Sports Prediction Platform
              </span>
            </div>
          </div>

          <div className="text-center mb-8">
            <h1 className="text-6xl sm:text-7xl lg:text-8xl font-black mb-6 leading-tight">
              <span className="block text-gray-900 mb-2">Beat The Odds</span>
              <span className="block bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
                With AI Precision
              </span>
            </h1>
            <p className="text-xl sm:text-2xl text-gray-700 mb-8 max-w-3xl mx-auto leading-relaxed font-light">
              Advanced ML ensemble predictions across NFL, NBA, NHL & MLB with <span className="font-bold">87% accuracy</span>, real-time confidence scores, and transparent AI reasoning.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <button 
              onClick={handleViewDashboard}
              className="group px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold text-lg rounded-xl hover:shadow-2xl hover:shadow-purple-500/30 hover:-translate-y-1 transition-all active:scale-95"
            >
              <span className="flex items-center justify-center gap-2">
                ✨ View Live Predictions
              </span>
            </button>
            <button 
              onClick={handleGetStarted}
              className="px-8 py-4 bg-white text-gray-900 font-bold text-lg rounded-xl border-2 border-gray-300 hover:border-blue-500 hover:shadow-lg transition-all active:scale-95"
            >
              Start Free Today
            </button>
          </div>

          <div className="background-glass rounded-2xl border border-blue-200 bg-white/40 backdrop-blur-md p-8 mb-8 max-w-2xl mx-auto">
            <div className="grid grid-cols-3 gap-8 text-center">
              <div>
                <div className="text-4xl font-black bg-gradient-to-r from-blue-600 to-blue-700 bg-clip-text text-transparent">87%</div>
                <div className="text-sm text-gray-700 font-semibold mt-2">Accuracy Rate</div>
              </div>
              <div>
                <div className="text-4xl font-black bg-gradient-to-r from-purple-600 to-purple-700 bg-clip-text text-transparent">4M+</div>
                <div className="text-sm text-gray-700 font-semibold mt-2">Predictions Made</div>
              </div>
              <div>
                <div className="text-4xl font-black bg-gradient-to-r from-pink-600 to-pink-700 bg-clip-text text-transparent">50K+</div>
                <div className="text-sm text-gray-700 font-semibold mt-2">Active Users</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============= FEATURED PREDICTIONS ============= */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-5xl font-black text-gray-900 mb-4">Live Predictions Across All Major Sports</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">AI-powered analysis for every league, every game, every betting opportunity</p>
          </div>

          <div className="flex flex-wrap justify-center gap-3 mb-12">
            {['nba', 'nfl', 'nhl', 'mlb'].map((sport) => (
              <button
                key={sport}
                onClick={() => setActiveTab(sport as any)}
                className={`px-6 py-3 font-bold rounded-xl transition-all ${
                  activeTab === sport
                    ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-xl'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {sport.toUpperCase()}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            {samplePredictions[activeTab].map((pred, idx) => (
              <div
                key={idx}
                className="group bg-white rounded-xl border-2 border-gray-200 hover:border-blue-400 p-6 transition-all hover:shadow-xl hover:-translate-y-1"
              >
                <div className="mb-4">
                  <div className="text-sm font-bold text-blue-600 mb-1">
                    {pred.type === 'game' && 'GAME PREDICTION'}
                    {pred.type === 'player' && 'PLAYER PROP'}
                    {pred.type === 'team' && 'TEAM PREDICTION'}
                  </div>
                  <div className="text-lg font-bold text-gray-900 break-words">
                    {pred.title}
                  </div>
                </div>
                
                <div className="bg-blue-50 rounded-lg p-4 mb-4 border border-blue-200">
                  <div className="text-lg font-bold text-gray-900 mb-2">
                    {pred.label}
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Confidence</span>
                    <span className={`font-bold text-lg ${
                      parseInt(pred.confidence) >= 85 ? 'text-green-600' : 'text-yellow-600'
                    }`}>
                      {pred.confidence}
                    </span>
                  </div>
                </div>

                <div className="text-sm text-gray-600 border-t pt-4">
                  <span className="font-semibold text-gray-700">Why:</span> {pred.reasoning}
                </div>
              </div>
            ))}
          </div>

          <div className="text-center">
            <button 
              onClick={handleViewDashboard}
              className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 transition-all"
            >
              View All {activeTab.toUpperCase()} Predictions →
            </button>
          </div>
        </div>
      </section>

      {/* ============= PLATFORM FEATURES ============= */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-5xl font-black text-gray-900 mb-4">Why Choose SportsAI?</h2>
            <p className="text-xl text-gray-600">Complete AI prediction ecosystem with features designed for winning</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {[
              { icon: '🤖', title: 'ML Ensemble Models', desc: 'XGBoost, LightGBM, TensorFlow & scikit-learn combined for maximum accuracy', gradient: 'from-blue-500 to-blue-600' },
              { icon: '📊', title: 'Real-Time Confidence', desc: 'Know exactly how confident our AI is in each prediction with transparent scoring', gradient: 'from-purple-500 to-purple-600' },
              { icon: '🧠', title: 'AI Reasoning Breakdown', desc: 'See the exact factors influencing each prediction - no black box analysis', gradient: 'from-pink-500 to-pink-600' },
              { icon: '⚡', title: 'Real-Time Data Stream', desc: 'Live odds, injury reports, player stats updated every minute from ESPN', gradient: 'from-yellow-500 to-yellow-600' },
              { icon: '🏆', title: 'Multi-Sport Coverage', desc: 'NFL, NBA, NHL, MLB, NCAAB, Soccer - all major sports covered daily', gradient: 'from-green-500 to-green-600' },
              { icon: '📈', title: 'Performance Tracking', desc: 'Monitor ROI, hit rates, and profits across all your tracked predictions', gradient: 'from-indigo-500 to-indigo-600' }
            ].map((feature, idx) => (
              <div key={idx} className="group relative bg-white rounded-2xl p-8 border border-gray-200 hover:border-transparent transition-all hover:shadow-xl hover:-translate-y-2 overflow-hidden">
                <div className={`absolute inset-0 bg-gradient-to-br ${feature.gradient} opacity-0 group-hover:opacity-5 transition-opacity`}></div>
                <div className="relative z-10">
                  <div className="text-5xl mb-4 group-hover:scale-125 transition-transform duration-300">{feature.icon}</div>
                  <h3 className="text-xl font-bold text-gray-900 mb-3">{feature.title}</h3>
                  <p className="text-gray-600 leading-relaxed">{feature.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============= PREDICTION TYPES ============= */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-5xl font-black text-gray-900 mb-4">4 Types of AI Predictions</h2>
            <p className="text-xl text-gray-600">Diverse betting markets covered with specialized models</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {[
              {
                icon: '🎯',
                title: 'Player Props',
                desc: 'Individual player stat predictions',
                examples: ['Points', 'Rebounds', 'Assists', 'Receiving Yards', 'Home Runs'],
                bgColor: 'blue',
                tagBg: 'bg-blue-100',
                tagText: 'text-blue-700'
              },
              {
                icon: '📊',
                title: 'Over/Under',
                desc: 'Score and stat line predictions',
                examples: ['Game Totals', 'Team Scores', 'Stat Totals', 'Quarter Spreads'],
                bgColor: 'purple',
                tagBg: 'bg-purple-100',
                tagText: 'text-purple-700'
              },
              {
                icon: '🏆',
                title: 'Team Props',
                desc: 'Team-based statistical predictions',
                examples: ['Team Totals', 'Win Margins', 'Performance Metrics'],
                bgColor: 'pink',
                tagBg: 'bg-pink-100',
                tagText: 'text-pink-700'
              },
              {
                icon: '✨',
                title: 'Moneyline',
                desc: 'Win/loss predictions for games',
                examples: ['Game Winners', 'Series Winners', 'Tournament Outcomes'],
                bgColor: 'green',
                tagBg: 'bg-green-100',
                tagText: 'text-green-700'
              }
            ].map((type, idx) => {
              const bgClass = {
                blue: 'from-blue-50 border-blue-200',
                purple: 'from-purple-50 border-purple-200',
                pink: 'from-pink-50 border-pink-200',
                green: 'from-green-50 border-green-200'
              }[type.bgColor];
              
              return (
                <div key={idx} className={`group bg-gradient-to-br ${bgClass} to-white border-2 rounded-2xl p-8 hover:shadow-xl transition-all hover:-translate-y-1`}>
                  <div className="flex items-start gap-4 mb-6">
                    <span className="text-5xl group-hover:scale-110 transition-transform">{type.icon}</span>
                    <div>
                      <h3 className="text-2xl font-bold text-gray-900">{type.title}</h3>
                      <p className="text-gray-600">{type.desc}</p>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {type.examples.map((example, i) => (
                      <span key={i} className={`px-3 py-1 ${type.tagBg} ${type.tagText} text-sm font-semibold rounded-full`}>
                        {example}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ============= ML TECHNOLOGY ============= */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-r from-gray-900 via-blue-900 to-gray-900">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-5xl font-black text-white mb-4">Enterprise-Grade AI Models</h2>
            <p className="text-xl text-gray-200">Cutting-edge machine learning technology serving millions of predictions</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { name: 'XGBoost', desc: 'Gradient boosting for precise pattern recognition', icon: '⚙️' },
              { name: 'LightGBM', desc: 'Fast, efficient tree-based ensemble learning', icon: '🚀' },
              { name: 'TensorFlow', desc: 'Deep neural networks for complex predictions', icon: '🧠' },
              { name: 'scikit-learn', desc: 'Robust statistical and ML baselines', icon: '📊' }
            ].map((model, idx) => (
              <div key={idx} className="bg-white/10 backdrop-blur border border-white/20 rounded-xl p-6 hover:bg-white/20 transition-all">
                <div className="text-4xl mb-3">{model.icon}</div>
                <h3 className="text-lg font-bold text-white mb-2">{model.name}</h3>
                <p className="text-gray-200 text-sm">{model.desc}</p>
              </div>
            ))}
          </div>

          <div className="mt-12 bg-white/10 backdrop-blur border border-white/20 rounded-2xl p-8">
            <h3 className="text-2xl font-bold text-white mb-4">Continuous Learning Pipeline</h3>
            <p className="text-gray-200 mb-6">
              Our models retrain daily with real sports data, continuously verifying predictions against actual outcomes. This creates a feedback loop that improves accuracy over time.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
              <div>
                <div className="text-3xl font-bold text-blue-300 mb-2">Daily</div>
                <p className="text-gray-300 text-sm">Model Retraining</p>
              </div>
              <div>
                <div className="text-3xl font-bold text-blue-300 mb-2">Real-Time</div>
                <p className="text-gray-300 text-sm">Performance Tracking</p>
              </div>
              <div>
                <div className="text-3xl font-bold text-blue-300 mb-2">Adaptive</div>
                <p className="text-gray-300 text-sm">Model Weighting</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============= PRICING & TIERS ============= */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-5xl font-black text-gray-900 mb-4">Choose Your Tier</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">Select the perfect plan based on your betting style and goals</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
            {[
              {
                icon: '🚀',
                name: 'Starter',
                price: '$0',
                period: 'Forever Free',
                features: [
                  { icon: '✓', text: 'AI Predictions', included: true },
                  { icon: '✓', text: 'Confidence Scores', included: true },
                  { icon: '✓', text: '3 Picks/Day', included: true },
                  { icon: '✗', text: 'Odds Data', included: false },
                  { icon: '✗', text: 'AI Reasoning', included: false }
                ],
                button: 'Get Started',
                buttonColor: 'blue',
                buttonAction: handleSignIn
              },
              {
                icon: '📈',
                name: 'Basic',
                price: '$9',
                period: '/month',
                features: [
                  { icon: '✓', text: 'All Starter Features', included: true },
                  { icon: '✓', text: 'Live Odds Data', included: true },
                  { icon: '✓', text: 'AI Reasoning', included: true },
                  { icon: '✓', text: '10 Picks/Day', included: true },
                  { icon: '✗', text: 'Model Breakdown', included: false }
                ],
                button: 'Upgrade Now',
                buttonColor: 'green',
                buttonAction: handleGetStarted
              },
              {
                icon: '⚡',
                name: 'Pro',
                price: '$29',
                period: '/month',
                badge: 'MOST POPULAR ⭐',
                features: [
                  { icon: '✓', text: 'All Basic Features', included: true },
                  { icon: '✓', text: 'ML Model Breakdown', included: true },
                  { icon: '✓', text: 'Model Comparison', included: true },
                  { icon: '✓', text: '25 Picks/Day', included: true },
                  { icon: '✓', text: 'SMS Alerts', included: true },
                  { icon: '✓', text: 'API Access', included: true }
                ],
                button: 'Go Pro Now',
                buttonColor: 'purple',
                buttonAction: handleGetStarted,
                featured: true
              },
              {
                icon: '👑',
                name: 'Elite',
                price: '$99',
                period: '/month',
                features: [
                  { icon: '✓', text: 'All Pro Features', included: true },
                  { icon: '✓', text: 'Full AI Breakdown', included: true },
                  { icon: '✓', text: 'Unlimited Picks', included: true },
                  { icon: '✓', text: 'Custom Models', included: true },
                  { icon: '✓', text: 'Webhooks API', included: true },
                  { icon: '✓', text: '24/7 Support', included: true }
                ],
                button: 'Become Elite',
                buttonColor: 'pink',
                buttonAction: handleGetStarted
              }
            ].map((tier, idx) => (
              <div key={idx} className={`relative bg-gradient-to-br rounded-2xl p-8 transition-all ${
                tier.featured 
                  ? 'from-purple-50 to-white border-2 border-purple-300 ring-2 ring-purple-400 ring-opacity-30 hover:shadow-2xl hover:-translate-y-2' 
                  : tier.icon === '🚀' 
                    ? 'from-blue-50 to-white border-2 border-blue-200 hover:shadow-lg hover:-translate-y-1'
                    : tier.icon === '📈'
                      ? 'from-green-50 to-white border-2 border-green-200 hover:shadow-lg hover:-translate-y-1'
                      : 'from-pink-50 to-white border-2 border-pink-200 hover:shadow-lg hover:-translate-y-1'
              }`}>
                {tier.badge && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-gradient-to-r from-purple-600 to-purple-500 text-white px-4 py-1 rounded-full text-sm font-bold">
                    {tier.badge}
                  </div>
                )}
                <div className={`flex items-center gap-3 mb-6 ${tier.badge ? 'mt-2' : ''}`}>
                  <span className="text-4xl">{tier.icon}</span>
                  <div>
                    <h3 className="text-2xl font-bold text-gray-900">{tier.name}</h3>
                    <p className="text-gray-600 text-sm">{tier.period}</p>
                  </div>
                </div>
                <div className="text-3xl font-black text-gray-900 mb-6">{tier.price}<span className="text-lg text-gray-600">{tier.period.includes('/') ? '' : ` ${tier.period}`}</span></div>
                <div className="space-y-3 mb-8">
                  {tier.features.map((feature, i) => (
                    <div key={i} className={`flex items-center gap-3 ${feature.included ? 'text-gray-700' : 'text-gray-400'}`}>
                      <span className={`font-bold ${feature.included ? 'text-green-500' : 'text-red-400'}`}>{feature.icon}</span>
                      <span className={feature.included ? 'font-medium' : 'line-through'}>{feature.text}</span>
                    </div>
                  ))}
                </div>
                <button 
                  onClick={tier.buttonAction}
                  className={`w-full py-3 font-bold rounded-xl transition-all ${
                    tier.buttonColor === 'blue' ? 'bg-blue-600 hover:bg-blue-700 text-white' :
                    tier.buttonColor === 'green' ? 'bg-green-600 hover:bg-green-700 text-white' :
                    tier.buttonColor === 'purple' ? 'bg-gradient-to-r from-purple-600 to-purple-700 hover:shadow-lg text-white' :
                    'bg-pink-600 hover:bg-pink-700 text-white'
                  }`}
                >
                  {tier.button}
                </button>
              </div>
            ))}
          </div>

          <div className="text-center bg-gradient-to-r from-blue-50 to-purple-50 border-2 border-blue-200 rounded-2xl p-8">
            <h3 className="text-2xl font-bold text-gray-900 mb-3">Start with Free, Upgrade Anytime</h3>
            <p className="text-gray-700 mb-6 max-w-2xl mx-auto">No credit card required. Instantly upgrade to any tier or downgrade whenever you want.</p>
            <button onClick={handleGetStarted} className="px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold rounded-xl hover:shadow-lg transition-all">
              Start Your Free Account
            </button>
          </div>
        </div>
      </section>

      {/* ============= HOW IT WORKS ============= */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-blue-50 to-white">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-5xl font-black text-gray-900 mb-4">Your Path to Winning</h2>
            <p className="text-xl text-gray-600">Get started in 3 simple steps</p>
          </div>

          <div className="relative mb-12">
            <div className="hidden md:block absolute top-20 left-0 right-0 h-1 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400"></div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {[
                { step: 1, title: 'Create Free Account', desc: 'Sign up instantly, no credit card needed. Get immediate access to AI predictions.', icon: '📝' },
                { step: 2, title: 'View Predictions', desc: 'Explore AI predictions across NFL, NBA, NHL & MLB with confidence scores.', icon: '🎯' },
                { step: 3, title: 'Track & Win', desc: 'Monitor your bets, watch profits grow, and upgrade anytime for more features.', icon: '🏆' }
              ].map((item) => (
                <div key={item.step} className="relative group">
                  <div className="bg-white border-2 border-gray-200 group-hover:border-blue-400 rounded-2xl p-8 text-center relative z-10 transition-all hover:shadow-xl hover:-translate-y-2">
                    <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 w-16 h-16 bg-gradient-to-br from-blue-600 to-purple-600 text-white rounded-full flex items-center justify-center font-bold text-2xl shadow-lg">
                      {item.step}
                    </div>
                    <div className="text-5xl mb-4 mt-4">{item.icon}</div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-3">{item.title}</h3>
                    <p className="text-gray-600 leading-relaxed">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="text-center">
            <button 
              onClick={handleGetStarted}
              className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold text-lg rounded-xl hover:shadow-2xl hover:-translate-y-1 transition-all"
            >
              Get Started for Free →
            </button>
            <p className="text-gray-600 mt-4 text-sm">Takes less than 60 seconds</p>
          </div>
        </div>
      </section>

      {/* ============= SOCIAL PROOF ============= */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-5xl font-black text-gray-900 mb-4">Trusted by Thousands</h2>
            <p className="text-xl text-gray-600">Join the community of sports fans winning with AI</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
            {[
              { stat: '87%', label: 'Accuracy Rate', desc: '4M+ predictions tracked' },
              { stat: '50K+', label: 'Active Users', desc: 'Growing community daily' },
              { stat: '$2.4M+', label: 'Tracked Winnings', desc: 'From our user community' }
            ].map((item, idx) => (
              <div key={idx} className="bg-gradient-to-br from-blue-50 to-purple-50 border-2 border-blue-200 rounded-2xl p-8 text-center hover:shadow-lg transition-all">
                <div className="text-4xl font-black bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-2">
                  {item.stat}
                </div>
                <div className="text-xl font-bold text-gray-900 mb-2">{item.label}</div>
                <div className="text-gray-600">{item.desc}</div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {[
              { name: 'Alex Malone', title: 'Professional Bettor', comment: 'The AI reasoning is incredible. I can understand exactly why each prediction was made. Best tool for serious bettors.', avatar: '👨‍💼', sport: 'NFL' },
              { name: 'Sarah Chen', title: 'Sports Fan', comment: 'Started with the free plan and upgraded to Pro in a week. The confidence scores helped me stay disciplined.', avatar: '👩‍💼', sport: 'NBA' },
              { name: 'Mike Rodriguez', title: 'Data Analyst', comment: 'As a data professional, I appreciate the ensemble ML models. The continuous learning pipeline is genius.', avatar: '👨‍💼', sport: 'MLB' }
            ].map((testimonial, idx) => (
              <div key={idx} className="bg-white border-2 border-gray-200 rounded-xl p-6 hover:shadow-lg transition-all">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="text-2xl mb-2">{testimonial.avatar}</div>
                    <div className="font-bold text-gray-900">{testimonial.name}</div>
                    <div className="text-sm text-gray-600">{testimonial.title}</div>
                  </div>
                  <span className="text-xs font-bold px-3 py-1 bg-blue-100 text-blue-700 rounded-full">{testimonial.sport}</span>
                </div>
                <p className="text-gray-700 italic">"{testimonial.comment}"</p>
                <div className="flex gap-1 mt-4">
                  {[...Array(5)].map((_, i) => (
                    <span key={i} className="text-yellow-400">★</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============= FINAL CTA ============= */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-5xl font-black text-gray-900 mb-6">Ready to Start Winning?</h2>
          <p className="text-xl text-gray-600 mb-8">Join thousands of successful bettors using AI predictions</p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button onClick={handleGetStarted} className="px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-bold text-lg hover:shadow-2xl hover:-translate-y-1 transition-all">
              Get Started Free
            </button>
            <button onClick={handleSignIn} className="px-8 py-4 bg-gray-200 text-gray-900 rounded-xl font-bold text-lg hover:bg-gray-300 transition-all">
              Sign In
            </button>
            <button className="px-8 py-4 bg-gray-100 text-gray-900 rounded-xl font-bold text-lg hover:bg-gray-200 transition-all">
              Schedule Demo
            </button>
          </div>
        </div>
      </section>

      {/* ============= FOOTER ============= */}
      <footer className="bg-gray-900 text-gray-400 py-12 px-4">
        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
            <div>
              <h3 className="text-white font-bold mb-4">Product</h3>
              <ul className="space-y-2 text-sm"><li><a href="#" className="hover:text-white transition">Features</a></li></ul>
            </div>
            <div>
              <h3 className="text-white font-bold mb-4">Company</h3>
              <ul className="space-y-2 text-sm"><li><a href="#" className="hover:text-white transition">About</a></li></ul>
            </div>
            <div>
              <h3 className="text-white font-bold mb-4">Legal</h3>
              <ul className="space-y-2 text-sm"><li><a href="#" className="hover:text-white transition">Privacy</a></li></ul>
            </div>
            <div>
              <h3 className="text-white font-bold mb-4">Social</h3>
              <ul className="space-y-2 text-sm"><li><a href="#" className="hover:text-white transition">Twitter</a></li></ul>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-8 text-center text-sm">
            <p>&copy; 2026 SportsAI. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
