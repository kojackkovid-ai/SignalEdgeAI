import React from 'react';
import { ChevronLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const CookiePolicy: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 text-white py-8">
        <div className="max-w-4xl mx-auto px-4">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-slate-300 hover:text-white mb-4"
          >
            <ChevronLeft className="w-4 h-4" />
            Back
          </button>
          <h1 className="text-4xl font-bold">Cookie Policy</h1>
          <p className="text-slate-300 mt-2">Last updated: April 1, 2026</p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="space-y-8 text-slate-700">
          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">1. What Are Cookies?</h2>
            <p className="mb-3">
              Cookies are small text files stored on your device (computer, tablet, or mobile phone) that are used to remember information about you as you navigate our Platform. Cookies help us understand how you use the Platform and improve your experience.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">2. Types of Cookies We Use</h2>

            <h3 className="text-xl font-semibold text-slate-800 mb-3">Essential Cookies</h3>
            <p className="mb-3">
              These cookies are necessary for the Platform to function properly. They enable core functionality such as:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4 mb-4">
              <li>Authentication and session management</li>
              <li>Security and fraud prevention</li>
              <li>Preference settings</li>
            </ul>

            <h3 className="text-xl font-semibold text-slate-800 mb-3">Analytics Cookies</h3>
            <p className="mb-3">
              These cookies help us understand how users interact with the Platform by collecting data such as:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4 mb-4">
              <li>Pages visited and time spent on each page</li>
              <li>User actions and clicks</li>
              <li>Traffic sources</li>
              <li>Error tracking and debugging</li>
            </ul>

            <h3 className="text-xl font-semibold text-slate-800 mb-3">Marketing Cookies</h3>
            <p className="mb-3">
              These cookies track your browsing habits to deliver targeted advertising and marketing content based on your interests.
            </p>

            <h3 className="text-xl font-semibold text-slate-800 mb-3">Third-Party Cookies</h3>
            <p className="mb-3">
              We allow third-party service providers to place cookies on your device for analytics, payments, and other functions.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">3. Specific Cookies We Use</h2>
            <table className="w-full border-collapse mb-4">
              <thead>
                <tr className="bg-slate-100">
                  <th className="border border-slate-300 p-3 text-left">Cookie Name</th>
                  <th className="border border-slate-300 p-3 text-left">Purpose</th>
                  <th className="border border-slate-300 p-3 text-left">Type</th>
                  <th className="border border-slate-300 p-3 text-left">Duration</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="border border-slate-300 p-3">access_token</td>
                  <td className="border border-slate-300 p-3">User authentication</td>
                  <td className="border border-slate-300 p-3">Essential</td>
                  <td className="border border-slate-300 p-3">Session</td>
                </tr>
                <tr>
                  <td className="border border-slate-300 p-3">analytics_id</td>
                  <td className="border border-slate-300 p-3">Analytics tracking</td>
                  <td className="border border-slate-300 p-3">Analytics</td>
                  <td className="border border-slate-300 p-3">1 year</td>
                </tr>
                <tr>
                  <td className="border border-slate-300 p-3">user_preferences</td>
                  <td className="border border-slate-300 p-3">Personalization</td>
                  <td className="border border-slate-300 p-3">Essential</td>
                  <td className="border border-slate-300 p-3">1 year</td>
                </tr>
              </tbody>
            </table>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">4. How to Control Cookies</h2>
            <p className="mb-3">
              Most web browsers allow you to control cookies through their settings. You can:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4 mb-3">
              <li>Accept or reject cookies</li>
              <li>Delete existing cookies</li>
              <li>Manage cookie preferences by type</li>
            </ul>
            <p className="mb-3">
              <strong>Note:</strong> Disabling essential cookies may affect the functionality of the Platform. We recommend keeping essential cookies enabled.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">5. Do Not Track</h2>
            <p className="mb-3">
              If your browser has a "Do Not Track" feature enabled, we will honor that preference and refrain from using tracking cookies, though essential cookies will still be used for functionality.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">6. Third-Party Analytics</h2>
            <p className="mb-3">
              We use third-party analytics services that may place their own cookies on your device. These services have their own privacy policies and cookie practices. We encourage you to review their policies directly.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">7. Updates to This Policy</h2>
            <p className="mb-3">
              We may update this Cookie Policy periodically. When we make updates, we will post the new policy on this page and update the "Last updated" date. It is your responsibility to review this policy regularly.
            </p>
          </section>

          <div className="mt-12 p-6 bg-slate-100 rounded-lg">
            <p className="text-sm text-slate-600">
              For questions about our use of cookies, please contact privacy@sportspredictionplatform.com
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CookiePolicy;
