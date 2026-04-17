import React from 'react';
import { ChevronLeft, AlertTriangle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const RiskDisclosure: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <div className="bg-gradient-to-r from-red-900 to-red-800 text-white py-8">
        <div className="max-w-4xl mx-auto px-4">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-red-200 hover:text-white mb-4"
          >
            <ChevronLeft className="w-4 h-4" />
            Back
          </button>
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-8 h-8" />
            <h1 className="text-4xl font-bold">Risk Disclosure</h1>
          </div>
          <p className="text-red-200 mt-2">Last updated: April 1, 2026</p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="space-y-8 text-slate-700">
          <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-8">
            <p className="font-bold text-red-900">
              ⚠️ IMPORTANT: Reading and understanding the risks outlined below is critical before using this Platform.
            </p>
          </div>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">1. No Guaranteed Results</h2>
            <p className="mb-3 font-semibold text-red-600">
              Sports Prediction Platform makes NO GUARANTEE that its predictions will be accurate or that following our recommendations will result in profits.
            </p>
            <p className="mb-3">
              All predictions are provided for entertainment purposes only and are subject to error. Past performance is not indicative of future results. You may lose money by using the Platform.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">2. Model Limitations</h2>
            <p className="mb-3">
              Our machine learning models are based on historical data and statistical analysis. These models have inherent limitations:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4 mb-3">
              <li>Models are trained on historical data and may not adapt well to unprecedented events</li>
              <li>Models may have blind spots or systematic biases</li>
              <li>Changes in league rules, team composition, or other factors may reduce model accuracy</li>
              <li>Model performance can degrade over time as market conditions change</li>
              <li>Unexpected events (injuries, trades, weather) can render predictions inaccurate</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">3. Data Quality Risk</h2>
            <p className="mb-3">
              Our predictions depend on the quality and timeliness of external data sources:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4 mb-3">
              <li>Data may be delayed or contain inaccuracies</li>
              <li>Sports data from ESPN, OddsAPI, and other providers may have errors</li>
              <li>Live odds may differ from historical odds used in our models</li>
              <li>Weather, injury reports, and other real-time factors may not be captured</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">4. Financial Risk</h2>
            <p className="mb-3 font-semibold text-red-600">
              ⚠️ Sports betting carries significant financial risk.
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4 mb-3">
              <li>You could lose your entire betting amount on any single prediction</li>
              <li>Odds change rapidly; predictions may become outdated</li>
              <li>Sportsbooks may reject or cancel bets for various reasons</li>
              <li>Accumulating losses can result in significant debt</li>
              <li>Chasing losses (betting more to recover losses) is a common path to financial ruin</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">5. Market Risk</h2>
            <p className="mb-3">
              The sports betting market is competitive and evolving:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4 mb-3">
              <li>Sportsbooks use sophisticated algorithms to balance odds and reduce sharp bettors</li>
              <li>Betting limits may be reduced or accounts may be closed by sportsbooks</li>
              <li>Odds may not be available when predictions are issued</li>
              <li>Liquidity issues may prevent you from placing or changing bets</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">6. Technical Risk</h2>
            <p className="mb-3">
              The Platform is subject to technical issues:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4 mb-3">
              <li>Platform outages may prevent you from accessing or using predictions</li>
              <li>Data sync failures may result in stale or incorrect information</li>
              <li>Integration failures with sportsbook APIs may affect functionality</li>
              <li>Bugs or unexpected behavior could impact prediction accuracy</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">7. Regulatory Risk</h2>
            <p className="mb-3">
              Sports betting and prediction services operate in a complex regulatory environment:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4 mb-3">
              <li>Laws governing sports betting vary by jurisdiction and may change</li>
              <li>The Platform may become unavailable in your location due to legal restrictions</li>
              <li>Your use of the Platform may violate local laws - it is your responsibility to check</li>
              <li>Payment processors may restrict transactions related to sports betting</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">8. Psychological Risk</h2>
            <p className="mb-3">
              Sports betting can create psychological challenges:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4 mb-3">
              <li>Betting can become compulsive and addictive</li>
              <li>Losses can lead to stress, anxiety, and depression</li>
              <li>The "gambler's fallacy" may lead to poor decision-making</li>
              <li>Overconfidence in prediction models may lead to excessive risk-taking</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">9. Disclaimer of Responsibility</h2>
            <p className="mb-3 font-semibold text-red-600">
              Sports Prediction Platform is NOT responsible for:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4 mb-3">
              <li>Any financial losses you incur from using the Platform</li>
              <li>Inaccurate, delayed, or misleading predictions</li>
              <li>Issues with third-party sportsbooks or payment processors</li>
              <li>Technical failures or service interruptions</li>
              <li>Gambling addiction or other harm related to betting</li>
              <li>Violation of local laws due to your use of the Platform</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">10. Your Responsibilities</h2>
            <p className="mb-3">
              By using the Platform, you acknowledge and accept that:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4 mb-3">
              <li>You are solely responsible for your betting decisions</li>
              <li>You understand the risks outlined in this disclosure</li>
              <li>You have verified that sports betting is legal in your jurisdiction</li>
              <li>You will not use the Platform as a substitute for professional financial or legal advice</li>
              <li>You will seek professional help if you develop gambling addiction symptoms</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">11. Acknowledgment</h2>
            <p className="mb-3">
              By using the Sports Prediction Platform, you acknowledge that you have read and understood this Risk Disclosure and agree to accept the risks outlined herein.
            </p>
          </section>

          <div className="mt-12 p-6 bg-red-50 rounded-lg border border-red-200">
            <p className="text-sm font-semibold text-red-900 mb-2">
              🆘 Need Help?
            </p>
            <p className="text-sm text-red-800 mb-3">
              If you are experiencing difficulties with gambling, please reach out to a gambling helpline:
            </p>
            <ul className="text-sm text-red-800 space-y-1">
              <li><strong>National Problem Gambling Helpline:</strong> 1-800-522-4700</li>
              <li><strong>NCPG Helpline:</strong> 1-800-GAMBLER (1-800-426-2537)</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RiskDisclosure;
