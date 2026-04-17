import React from 'react';
import { ChevronLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const RefundPolicy: React.FC = () => {
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
          <h1 className="text-4xl font-bold">Refund & Cancellation Policy</h1>
          <p className="text-slate-300 mt-2">Last updated: April 1, 2026</p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="space-y-8 text-slate-700">
          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">1. Subscription Cancellation</h2>
            <p className="mb-3">
              You may cancel your subscription at any time through your account settings. Cancellations take effect at the end of your current billing period. You will retain access to your subscription tier until the end of the current billing cycle.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">2. No Refunds for Used Services</h2>
            <p className="mb-3">
              Refunds will not be issued for subscription fees if you have already accessed the Platform and its services during the current billing period. Subscription fees are non-refundable once the service period has begun.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">3. 7-Day Trial Refund</h2>
            <p className="mb-3">
              If you are a new user and have not accessed any predictions within the first 7 days of subscribing, you may request a full refund of your subscription fee by contacting support@sportspredictionplatform.com with your account information and the reason for the refund request.
            </p>
            <p className="mb-3">
              To qualify: Account must be deactivated within 7 days of creation and no predictions must have been viewed or unlocked.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">4. Billing Issues</h2>
            <p className="mb-3">
              If you believe you have been charged in error or have been double-charged, please contact us immediately at billing@sportspredictionplatform.com with:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4 mb-3">
              <li>Your account email address</li>
              <li>Transaction ID (from your payment confirmation)</li>
              <li>Description of the issue</li>
              <li>Any supporting documentation</li>
            </ul>
            <p>
              We will investigate billing disputes within 5-7 business days and resolve them appropriately.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">5. Payment Method Changes</h2>
            <p className="mb-3">
              You can update your payment method at any time through your account settings. Your new payment method will be used for your next billing cycle. Changing your payment method does not entitle you to a refund of previous charges.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">6. Pro-Rata Refunds</h2>
            <p className="mb-3">
              If you upgrade your subscription mid-cycle, we will charge the difference for the upgrade. If you downgrade your subscription mid-cycle, no pro-rata refunds will be issued; the downgrade will take effect on your next billing date.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">7. Chargeback Policy</h2>
            <p className="mb-3">
              Chargebacks are considered a violation of our Terms of Service. Accounts associated with chargebacks may be permanently suspended. If you have a legitimate billing dispute, please contact us directly instead of initiating a chargeback through your bank.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">8. Service Disruptions</h2>
            <p className="mb-3">
              We strive to maintain 99.5% uptime. Extended service disruptions (&gt; 24 hours) may entitle you to compensation in the form of service credits or subscription extensions at our discretion. We will not issue cash refunds for service disruptions.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">9. Account Closure by Us</h2>
            <p className="mb-3">
              If we terminate your account due to violation of our Terms of Service, no refunds will be issued. If we terminate your account without cause, you may be eligible for a pro-rata refund of unused subscription fees.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">10. European Union Customers</h2>
            <p className="mb-3">
              Customers in the European Union have the right to withdraw from purchase within 14 days without providing any reason. To exercise this right, contact refunds@sportspredictionplatform.com within 14 days of your purchase.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">11. Contact For Refunds</h2>
            <p className="mb-3">
              To request a refund or discuss billing issues, please contact:
            </p>
            <ul className="list-none space-y-2 ml-4 mb-3">
              <li><strong>Email:</strong> refunds@sportspredictionplatform.com</li>
              <li><strong>Response time:</strong> 5-7 business days</li>
            </ul>
          </section>

          <div className="mt-12 p-6 bg-slate-100 rounded-lg">
            <p className="text-sm text-slate-600">
              Please note that processing times may vary. Approved refunds will be returned to your original payment method within 5-10 business days.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RefundPolicy;
