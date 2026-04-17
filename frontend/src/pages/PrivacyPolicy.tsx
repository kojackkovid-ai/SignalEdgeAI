import React from 'react';
import { ChevronLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const PrivacyPolicy: React.FC = () => {
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
          <h1 className="text-4xl font-bold">Privacy Policy</h1>
          <p className="text-slate-300 mt-2">Last updated: April 1, 2026</p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="space-y-8 text-slate-700">
          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">1. Introduction</h2>
            <p className="mb-3">
              Sports Prediction Platform ("we," "us," "our," or "Platform") respects your privacy and is committed to protecting your personal data. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our Platform.
            </p>
            <p>
              Please read this Privacy Policy carefully. If you do not agree with our data practices, please do not use the Platform.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">2. Information We Collect</h2>
            <h3 className="text-xl font-semibold text-slate-800 mb-3">Personal Information You Provide</h3>
            <ul className="list-disc list-inside space-y-2 ml-4 mb-3">
              <li>Email address and username</li>
              <li>Password (encrypted)</li>
              <li>Subscription tier and payment information</li>
              <li>Account preferences and settings</li>
            </ul>

            <h3 className="text-xl font-semibold text-slate-800 mb-3">Information Automatically Collected</h3>
            <ul className="list-disc list-inside space-y-2 ml-4 mb-3">
              <li>IP address and device information</li>
              <li>Browser type and operating system</li>
              <li>Pages visited and time spent</li>
              <li>Cookies and similar tracking technologies</li>
              <li>Usage analytics and prediction interactions</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">3. How We Use Your Information</h2>
            <p className="mb-3">We use collected information for:</p>
            <ul className="list-disc list-inside space-y-2 ml-4 mb-3">
              <li>Providing and maintaining the Platform services</li>
              <li>Processing subscription payments</li>
              <li>Sending transactional and informational emails</li>
              <li>Improving and optimizing Platform features</li>
              <li>Complying with legal obligations</li>
              <li>Detecting and preventing fraud or abuse</li>
              <li>Personalizing your experience</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">4. Cookies and Tracking Technologies</h2>
            <p className="mb-3">
              We use cookies and similar technologies to track activity on our Platform and hold certain information. You can instruct your browser to refuse all cookies or to indicate when a cookie is being sent. However, if you do not accept cookies, you may not be able to use portions of our Platform.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">5. Data Security</h2>
            <p className="mb-3">
              We implement appropriate technical and organizational measures designed to protect your personal information against unauthorized access, alteration, disclosure, or destruction. We use encryption (SSL), secure servers, and firewalls.
            </p>
            <p className="mb-3">
              However, no method of transmission over the Internet or electronic storage is 100% secure. While we strive to protect your data, we cannot guarantee absolute security.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">6. Third-Party Services</h2>
            <p className="mb-3">
              We may share your information with third-party service providers who assist us in operating our Platform and conducting our business, including:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4 mb-3">
              <li>Payment processors (Stripe)</li>
              <li>Email service providers (SendGrid)</li>
              <li>Analytics providers</li>
              <li>Cloud hosting providers</li>
            </ul>
            <p>
              These service providers are contractually obligated to use your information only to provide services to us and are required to maintain the confidentiality of your information.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">7. Your Rights</h2>
            <p className="mb-3">Depending on your location, you may have the following rights:</p>
            <ul className="list-disc list-inside space-y-2 ml-4 mb-3">
              <li>Right to access your personal data</li>
              <li>Right to correct inaccurate data</li>
              <li>Right to request deletion of your data</li>
              <li>Right to opt-out of marketing communications</li>
              <li>Right to data portability</li>
            </ul>
            <p className="mt-3">
              To exercise these rights, contact us at privacy@sportspredictionplatform.com
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">8. GDPR Compliance (EU Users)</h2>
            <p className="mb-3">
              If you are located in the European Union, you have additional rights under the General Data Protection Regulation (GDPR). We process your personal data based on:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4 mb-3">
              <li>Your consent</li>
              <li>Performance of our contract with you</li>
              <li>Our legitimate interests</li>
              <li>Legal obligations</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">9. CCPA Compliance (California Users)</h2>
            <p className="mb-3">
              If you are a California resident, you have specific rights under the California Consumer Privacy Act (CCPA), including the right to know, delete, and opt-out of the sale of your personal information.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">10. Children's Privacy</h2>
            <p className="mb-3">
              The Platform is not intended for users under the age of 18. We do not knowingly collect personal information from children. If we become aware that we have collected personal information from a child, we will take steps to delete such information.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">11. Changes to This Privacy Policy</h2>
            <p className="mb-3">
              We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new policy on this page and updating the "Last updated" date.
            </p>
          </section>

          <div className="mt-12 p-6 bg-slate-100 rounded-lg">
            <p className="text-sm text-slate-600">
              For questions about this Privacy Policy, please contact us at privacy@sportspredictionplatform.com
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PrivacyPolicy;
