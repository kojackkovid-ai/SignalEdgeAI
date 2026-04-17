import React from 'react';
import { ChevronLeft, AlertTriangle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const ResponsibleGambling: React.FC = () => {
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
            <h1 className="text-4xl font-bold">Responsible Gambling</h1>
          </div>
          <p className="text-red-200 mt-2">Last updated: April 1, 2026</p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="space-y-8 text-slate-700">
          <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-8">
            <p className="font-bold text-red-900">
              ⚠️ IMPORTANT: Sports betting and gambling can be addictive. Please gamble responsibly.
            </p>
          </div>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">1. Our Commitment</h2>
            <p className="mb-3">
              Sports Prediction Platform is committed to promoting responsible gambling and supporting the wellbeing of our users. While we provide predictions for entertainment purposes, we recognize the potential risks associated with sports betting and are dedicated to fostering safe and enjoyable wagering practices.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">2. Entertainment Only</h2>
            <p className="mb-3 font-bold text-red-600">
              ⚠️ All predictions provided are for entertainment purposes only and do not guarantee future results.
            </p>
            <p className="mb-3">
              Our machine learning models are based on historical data and patterns but cannot predict future outcomes with certainty. Past performance is not indicative of future results. You could lose money. Never bet more than you can afford to lose.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">3. Set Limits</h2>
            <p className="mb-3">
              We strongly recommend that you:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4 mb-3">
              <li>Set a budget for your betting and stick to it</li>
              <li>Never chase losses by betting more than planned</li>
              <li>Take regular breaks from betting</li>
              <li>Keep track of your wins and losses</li>
              <li>Never use borrowed money to place bets</li>
              <li>Set time limits for your gaming sessions</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">4. Warning Signs of Problem Gambling</h2>
            <p className="mb-3">
              Seek help if you experience any of the following:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4 mb-3">
              <li>Gambling more frequently or with larger amounts</li>
              <li>Inability to stop or reduce gambling</li>
              <li>Neglecting family, work, or other responsibilities</li>
              <li>Lying about the extent of your gambling</li>
              <li>Gambling to escape problems or negative emotions</li>
              <li>Experiencing financial difficulties due to gambling</li>
              <li>Feeling anxious or irritable when not gambling</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">5. Resources and Support</h2>
            <p className="mb-3">
              If you or someone you know is struggling with gambling addiction, help is available:
            </p>
            <ul className="list-none space-y-3 ml-4 mb-3">
              <li>
                <strong>National Council on Problem Gambling</strong><br />
                1-800-GAMBLER (1-800-426-2537)<br />
                www.ncpg.org
              </li>
              <li>
                <strong>Gamblers Anonymous</strong><br />
                www.gamblersanonymous.org
              </li>
              <li>
                <strong>National Problem Gambling Helpline</strong><br />
                1-800-522-4700
              </li>
              <li>
                <strong>SAMHSA National Helpline</strong><br />
                1-800-662-4357
              </li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">6. Self-Exclusion</h2>
            <p className="mb-3">
              If you would like to self-exclude from our Platform, please contact us at support@sportspredictionplatform.com with a request to close your account.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">7. Age Verification</h2>
            <p className="mb-3">
              The Platform is restricted to users 18 years of age or older. We use identity verification to enforce this requirement. Any account found to be in violation of this policy will be immediately terminated.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">8. Prohibition on Credit Betting</h2>
            <p className="mb-3">
              We do not promote betting on credit. We strongly advise against using credit cards or borrowed funds for gambling activities.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">9. Fair Play</h2>
            <p className="mb-3">
              All of our predictions are generated using the same machine learning models and algorithms for all users. No predictions are manually adjusted for specific users. We do not engage in any form of fraud, collusion, or market manipulation.
            </p>
          </section>

          <div className="mt-12 p-6 bg-red-50 rounded-lg border border-red-200">
            <p className="text-sm font-semibold text-red-900 mb-2">
              Questions or Concerns?
            </p>
            <p className="text-sm text-red-800">
              If you have concerns about your gambling habits or need support, please reach out to our support team at support@sportspredictionplatform.com or contact one of the helplines above.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResponsibleGambling;
