import React from 'react';
import { ChevronLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const TermsOfService: React.FC = () => {
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
          <h1 className="text-4xl font-bold">Terms of Service</h1>
          <p className="text-slate-300 mt-2">Last updated: April 1, 2026</p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="space-y-8 text-slate-700">
          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">1. Agreement to Terms</h2>
            <p className="mb-3">
              By accessing and using the Sports Prediction Platform ("Platform"), you agree to be bound by these Terms of Service ("Terms"). If you do not agree to abide by the above, please do not use this service.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">2. Use License</h2>
            <p className="mb-3">
              Permission is granted to temporarily download one copy of the materials (information or software) on the Sports Prediction Platform for personal, non-commercial transitory viewing only. This is the grant of a license, not a transfer of title, and under this license you may not:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4 mb-3">
              <li>Modify or copy the materials</li>
              <li>Use the materials for any commercial purpose or for any public display</li>
              <li>Attempt to decompile or reverse engineer any software on the Platform</li>
              <li>Remove any copyright or other proprietary notation from the materials</li>
              <li>Transfer the materials to another person or "mirror" the materials on any other server</li>
              <li>Violate any applicable laws or regulations</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">3. Disclaimer of Warranties</h2>
            <p className="mb-3">
              The materials on the Sports Prediction Platform are provided on an 'as is' basis. Sports Prediction Platform makes no warranties, expressed or implied, and hereby disclaims and negates all other warranties including, without limitation, implied warranties or conditions of merchantability, fitness for a particular purpose, or non-infringement of intellectual property or other violation of rights.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">4. Predictions and Entertainment</h2>
            <p className="mb-3 font-semibold text-red-600">
              ⚠️ IMPORTANT: All predictions and analysis provided by the Sports Prediction Platform are for entertainment purposes only and should not be construed as financial advice or guaranteed outcomes.
            </p>
            <p className="mb-3">
              Predictions are based on historical data and machine learning models, which do not guarantee future results. Users should conduct their own research before making any betting decisions.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">5. Limitations of Liability</h2>
            <p className="mb-3">
              In no event shall Sports Prediction Platform or its suppliers be liable for any damages (including, without limitation, damages for loss of data or profit, or due to business interruption) arising out of the use or inability to use the materials on the Sports Prediction Platform.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">6. Accuracy of Materials</h2>
            <p className="mb-3">
              The materials appearing on the Sports Prediction Platform could include technical, typographical, or photographic errors. Sports Prediction Platform does not warrant that any of the materials on the Platform are accurate, complete, or current. Sports Prediction Platform may make changes to the materials contained on the Platform at any time without notice.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">7. Links</h2>
            <p className="mb-3">
              Sports Prediction Platform has not reviewed all of the sites linked to its Platform and is not responsible for the contents of any such linked site. The inclusion of any link does not imply endorsement by Sports Prediction Platform of the site. Use of any such linked website is at the user's own risk.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">8. Modifications</h2>
            <p className="mb-3">
              Sports Prediction Platform may revise these terms of service for the Platform at any time without notice. By using the Platform, you are agreeing to be bound by the then current version of these terms of service.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">9. Governing Law</h2>
            <p className="mb-3">
              These terms and conditions are governed by and construed in accordance with the laws of the United States, and you irrevocably submit to the exclusive jurisdiction of the courts in that location.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">10. User Accounts</h2>
            <p className="mb-3">
              When you create an account on the Platform, you must provide accurate information and maintain the confidentiality of your account credentials. You are responsible for all activity associated with your account. You agree to notify us immediately of any unauthorized use.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">11. User Conduct</h2>
            <p className="mb-3">
              You agree not to:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4 mb-3">
              <li>Engage in any conduct that restricts or inhibits anyone's use or enjoyment</li>
              <li>Post or transmit abusive, obscene, threatening, or illegal content</li>
              <li>Attempt to gain unauthorized access to the Platform</li>
              <li>Interfere with the proper functioning of the Platform</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">12. Subscription Terms</h2>
            <p className="mb-3">
              Subscription plans automatically renew on the date specified in your account. You may cancel at any time through your account settings. Cancellations take effect at the end of the current billing period.
            </p>
          </section>

          <div className="mt-12 p-6 bg-slate-100 rounded-lg">
            <p className="text-sm text-slate-600">
              For questions about these Terms of Service, please contact us at legal@sportspredictionplatform.com
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TermsOfService;
