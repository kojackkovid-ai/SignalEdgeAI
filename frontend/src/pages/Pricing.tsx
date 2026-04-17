import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../utils/store';
import { analyticsTracker } from '../utils/analytics';

const Pricing: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual'>('monthly');

  const plans = [
    {
      name: 'Starter',
      price: 0,
      description: 'Try for free',
      icon: '🚀',
      features: [
        '1 free pick per day',
        'Basic confidence scores',
        'Community access',
        'Email support'
      ],
      color: 'from-blue-500 to-blue-600',
      highlighted: false,
      cta: 'Get Started Free'
    },
    {
      name: 'Basic',
      price: billingCycle === 'monthly' ? 12 : 120,
      priceAnnual: 120,
      savings: billingCycle === 'annual' ? 24 : 0,
      description: 'For casual bettors',
      icon: '📈',
      features: [
        '10 picks per day',
        'Standard confidence analysis',
        'All sports coverage',
        'Basic analytics',
        'Email support'
      ],
      color: 'from-green-500 to-green-600',
      highlighted: false,
      cta: 'Start Basic'
    },
    {
      name: 'Pro',
      price: billingCycle === 'monthly' ? 29 : 290,
      priceAnnual: 290,
      savings: billingCycle === 'annual' ? 58 : 0,
      description: 'For serious bettors',
      icon: '⚡',
      features: [
        '25 picks per day',
        'Advanced confidence analysis',
        'Real-time alerts (SMS/Email)',
        'All sports coverage',
        'Advanced analytics',
        'Priority support',
        'API access'
      ],
      color: 'from-purple-500 to-purple-600',
      highlighted: true,
      cta: 'Start Free Trial'
    },
    {
      name: 'Pro Plus',
      price: billingCycle === 'monthly' ? 49 : 490,
      priceAnnual: 490,
      savings: billingCycle === 'annual' ? 98 : 0,
      description: 'For advanced bettors',
      icon: '🎯',
      features: [
        'Everything in Pro',
        'Full AI Breakdown',
        'Unlimited Picks',
        'Advanced confidence analysis',
        'Real-time alerts (SMS/Email)',
        'All sports coverage',
        'Advanced analytics',
        'Priority support',
        'API access'
      ],
      color: 'from-orange-500 to-orange-600',
      highlighted: false,
      cta: 'Start Pro Plus'
    },
    {
      name: 'Elite',
      price: billingCycle === 'monthly' ? 99 : 990,
      priceAnnual: 990,
      savings: billingCycle === 'annual' ? 198 : 0,
      description: 'For professionals',
      icon: '👑',
      features: [
        'Everything in Pro',
        'Custom model training',
        'Dedicated account manager',
        'White-label options',
        'Enterprise API',
        'Custom alerts',
        '24/7 phone support',
        'Advanced backtesting'
      ],
      color: 'from-pink-500 to-pink-600',
      highlighted: false,
      cta: 'Contact Sales'
    }
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <section className="px-4 sm:px-6 lg:px-8 py-16 text-center pt-28">
        <h1 className="text-6xl font-black text-gray-900 mb-6">Simple, Transparent Pricing</h1>
        <p className="text-2xl text-gray-600 mb-12 max-w-2xl mx-auto">Choose the plan that fits your betting style</p>

        {/* Billing Toggle */}
        <div className="flex items-center justify-center gap-6 mb-16">
          <span className={`text-lg font-semibold ${billingCycle === 'monthly' ? 'text-gray-900' : 'text-gray-500'}`}>
            Monthly
          </span>
          <button
            onClick={() => setBillingCycle(billingCycle === 'monthly' ? 'annual' : 'monthly')}
            className={`relative inline-flex h-10 w-20 items-center rounded-full transition-all ${
              billingCycle === 'annual' ? 'bg-gradient-to-r from-blue-600 to-purple-600' : 'bg-gray-300'
            }`}
          >
            <span
              className={`inline-block h-8 w-8 transform rounded-full bg-white transition-all ${
                billingCycle === 'annual' ? 'translate-x-10' : 'translate-x-1'
              }`}
            />
          </button>
          <span className={`text-lg font-semibold ${billingCycle === 'annual' ? 'text-gray-900' : 'text-gray-500'}`}>
            Annual
            {billingCycle === 'annual' && <span className="ml-2 inline-block bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm font-bold">Save 20%</span>}
          </span>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="px-4 sm:px-6 lg:px-8 pb-20">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8">
            {plans.map((plan, idx) => (
              <div
                key={idx}
                className={`relative rounded-3xl overflow-hidden transition-all ${
                  plan.highlighted
                    ? 'border-0 shadow-2xl scale-105 md:scale-100'
                    : 'border-2 border-gray-200 hover:border-blue-300 hover:shadow-xl'
                }`}
              >
                {/* Background gradient */}
                <div className={`absolute inset-0 bg-gradient-to-br ${plan.color} opacity-5`}></div>

                {/* Badge */}
                {plan.highlighted && (
                  <div className="absolute top-0 right-0 left-0">
                    <div className={`bg-gradient-to-r ${plan.color} text-white text-center py-2 text-sm font-bold`}>
                      ⭐ MOST POPULAR
                    </div>
                  </div>
                )}

                <div className={`relative p-8 ${plan.highlighted ? 'pt-20' : ''}`}>
                  {/* Icon and Name */}
                  <div className="mb-6">
                    <div className="text-5xl mb-4">{plan.icon}</div>
                    <h3 className="text-3xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                    <p className="text-gray-600">{plan.description}</p>
                  </div>

                  {/* Price */}
                  <div className="mb-8">
                    <div className="flex items-baseline">
                      <span className={`text-5xl font-black bg-gradient-to-r ${plan.color} bg-clip-text text-transparent`}>
                        ${plan.price}
                      </span>
                      <span className="text-gray-600 ml-2 font-semibold">/{billingCycle === 'monthly' ? 'mo' : 'yr'}</span>
                    </div>
                    {billingCycle === 'annual' && plan.priceAnnual && (
                      <p className="text-green-600 font-bold mt-2">Save ${plan.savings} per year</p>
                    )}
                  </div>

                  {/* CTA Button */}
                  <button
                    className={`w-full py-4 rounded-xl font-bold text-lg transition-all mb-8 ${
                      plan.highlighted
                        ? `bg-gradient-to-r ${plan.color} text-white hover:shadow-xl hover:-translate-y-1`
                        : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                    }`}
                    onClick={() => {
                      console.log('[Pricing] Button clicked for plan:', plan.name, 'Auth:', isAuthenticated);
                      
                      // Track tier upgrade initiation
                      if (plan.name !== 'Starter') {
                        analyticsTracker.trackEvent('tier_upgrade_initiated', { plan: plan.name.toLowerCase(), price: plan.price }, '').catch(() => {});
                      }
                      
                      if (plan.name === 'Starter') {
                        navigate('/register');
                      } else if (isAuthenticated) {
                        const planKey = plan.name === 'Pro Plus' ? 'pro_plus' : plan.name.toLowerCase();
                        console.log('[Pricing] Navigating to payment for:', planKey);
                        navigate(`/payment?plan=${planKey}&cycle=${billingCycle}`);
                      } else {
                        console.log('[Pricing] Not authenticated, redirecting to register');
                        navigate('/register');
                      }
                    }}
                  >
                    {plan.cta}
                  </button>

                  {/* Features */}
                  <ul className="space-y-4">
                    {plan.features.map((feature, i) => (
                      <li key={i} className="flex items-start gap-3">
                        <svg className={`w-5 h-5 mt-0.5 flex-shrink-0 bg-gradient-to-r ${plan.color} bg-clip-text text-transparent`} fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                        <span className="text-gray-700">{feature}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Comparison Table */}
      <section className="px-4 sm:px-6 lg:px-8 py-20 bg-gray-50">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-4xl font-bold text-gray-900 mb-12 text-center">Feature Comparison</h2>

          <div className="bg-white rounded-2xl border-2 border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-50 border-b-2 border-gray-200">
                    <th className="px-8 py-6 text-left text-lg font-bold text-gray-900">Feature</th>
                    <th className="px-8 py-6 text-center text-lg font-bold text-gray-900">Starter</th>
                    <th className="px-8 py-6 text-center text-lg font-bold text-gray-900">Basic</th>
                    <th className="px-8 py-6 text-center text-lg font-bold text-gray-900">Pro</th>
                    <th className="px-8 py-6 text-center text-lg font-bold text-gray-900">Pro Plus</th>
                    <th className="px-8 py-6 text-center text-lg font-bold text-gray-900">Elite</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { feature: 'Daily Picks', starter: '1', basic: '10', pro: '25', proPlus: '∞', elite: '∞' },
                    { feature: 'Confidence Scores', starter: '✓', basic: '✓', pro: '✓', proPlus: '✓', elite: '✓' },
                    { feature: 'Real-time Alerts', starter: '✗', basic: '✗', pro: '✓', proPlus: '✓', elite: '✓' },
                    { feature: 'Advanced Analytics', starter: '✗', basic: '✗', pro: '✓', proPlus: '✓', elite: '✓' },
                    { feature: 'API Access', starter: '✗', basic: '✗', pro: '✓', proPlus: '✓', elite: '✓' },
                    { feature: 'Full AI Breakdown', starter: '✗', basic: '✗', pro: '✗', proPlus: '✓', elite: '✓' },
                    { feature: 'Priority Support', starter: '✗', basic: '✗', pro: '✓', proPlus: '✓', elite: '✓' },
                    { feature: 'White-Label', starter: '✗', basic: '✗', pro: '✗', proPlus: '✗', elite: '✓' },
                    { feature: 'Custom Models', starter: '✗', basic: '✗', pro: '✗', proPlus: '✗', elite: '✓' }
                  ].map((row, idx) => (
                    <tr key={idx} className="border-b border-gray-200 hover:bg-gray-50">
                      <td className="px-8 py-6 font-semibold text-gray-900">{row.feature}</td>
                      <td className="px-8 py-6 text-center text-gray-600">{row.starter}</td>
                      <td className="px-8 py-6 text-center text-green-600 font-bold">{row.basic}</td>
                      <td className="px-8 py-6 text-center text-blue-600 font-bold">{row.pro}</td>
                      <td className="px-8 py-6 text-center text-orange-600 font-bold">{row.proPlus}</td>
                      <td className="px-8 py-6 text-center text-pink-600 font-bold">{row.elite}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="px-4 sm:px-6 lg:px-8 py-20">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-4xl font-bold text-gray-900 mb-12 text-center">Frequently Asked Questions</h2>

          <div className="space-y-6">
            {[
              {
                q: 'Can I change plans anytime?',
                a: 'Yes! Upgrade or downgrade your plan at any time. Changes take effect immediately.'
              },
              {
                q: 'Do you offer refunds?',
                a: 'We offer a 3-day money-back guarantee. No questions asked.'
              },
              {
                q: 'What payment methods do you accept?',
                a: 'We accept all major credit cards, PayPal, and crypto. All transactions are 256-bit encrypted.'
              },
              {
                q: 'Do you have enterprise pricing?',
                a: 'Yes! Contact our sales team for custom enterprise plans with dedicated support.'
              }
            ].map((item, idx) => (
              <div key={idx} className="bg-gray-50 border-2 border-gray-200 rounded-xl p-8 hover:border-blue-300 transition-colors">
                <h3 className="text-xl font-bold text-gray-900 mb-3">{item.q}</h3>
                <p className="text-gray-600 text-lg leading-relaxed">{item.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="px-4 sm:px-6 lg:px-8 py-20 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600">
        <div className="max-w-2xl mx-auto text-center text-white">
          <h2 className="text-5xl font-black mb-6">Ready to Win More?</h2>
          <p className="text-xl opacity-90 mb-8">Join thousands of successful bettors using AI predictions</p>
          <button className="px-8 py-4 bg-white text-blue-600 rounded-xl font-bold text-lg hover:shadow-xl hover:-translate-y-1 transition-all" onClick={() => navigate('/register')}>
            Start Your Free Trial
          </button>
        </div>
      </section>

      {/* Support Footer */}
      <section className="px-4 py-8 bg-gray-900 text-center">
        <p className="text-gray-400">
          Need help choosing a plan? Contact our support team at{' '}
          <a href="mailto:kojackkovid@gmail.com" className="text-blue-400 hover:text-blue-300 font-bold">
            kojackkovid@gmail.com
          </a>
        </p>
      </section>
    </div>
  );
};

export default Pricing;
