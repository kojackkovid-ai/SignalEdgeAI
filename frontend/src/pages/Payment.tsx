import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { loadStripe, Stripe } from '@stripe/stripe-js';
import { Elements, PaymentElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { useAuthStore } from '../utils/store';
import api from '../utils/api';
import { analyticsTracker } from '../utils/analytics';

// Initialize Stripe with proper error handling
let stripePromise: Promise<Stripe | null> | null = null;

function getStripePromise() {
  if (stripePromise) return stripePromise;

  const stripeApiKey = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY;
  
  if (stripeApiKey) {
    stripePromise = loadStripe(stripeApiKey);
  } else {
    console.error('[Stripe] VITE_STRIPE_PUBLISHABLE_KEY is not set');
    stripePromise = Promise.resolve(null);
  }
  
  return stripePromise;
}


const CheckoutForm: React.FC<{
  plan: string;
  cycle: string;
  price: number;
  planName: string;
}> = ({ plan, cycle: _cycle, price, planName }) => {

  const stripe = useStripe();
  const elements = useElements();
  const navigate = useNavigate();
  const { user, setUser } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!stripe || !elements) {
      setError('Stripe is not loaded yet. Please wait a moment and try again.');
      return;
    }

    if (loading) return;

    setLoading(true);
    setError(null);

    try {
      // Confirm payment with Stripe
      const { error: stripeError, paymentIntent } = await stripe.confirmPayment({
        elements,
        redirect: 'if_required',
      });

      if (stripeError) {
        setError(`Stripe Error: ${stripeError.message}`);
        setLoading(false);
        return;
      }

      if (paymentIntent && paymentIntent.status === 'succeeded') {
        // Confirm payment with backend and upgrade subscription
        const confirmResponse = await api.post('/payment/confirm-payment', {
          payment_intent_id: paymentIntent.id,
          plan: plan,
        });

        // Get the confirmed tier from backend response
        const confirmedTier = confirmResponse.data?.new_tier || plan;

        // Update user tier in store with confirmed tier from backend
        if (user) {
          setUser({ ...user, tier: confirmedTier, subscription_tier: confirmedTier });
        }

        // Track payment completion
        analyticsTracker.trackPaymentComplete(user?.id || '', price, plan, paymentIntent.id).catch(() => {});

        setSuccess(true);
        
        // Allow a small delay for state to update before navigation
        await new Promise(resolve => setTimeout(resolve, 500));
        
        setTimeout(() => {
          navigate('/dashboard');
        }, planName === 'Elite' ? 10000 : 2000);
      } else {
        setError(`Payment status: ${paymentIntent?.status}. Please contact support.`);
      }
    } catch (err: any) {
      console.error('[Payment] Error confirming payment:', err?.message);
      const errorMsg = err?.response?.data?.detail || err?.message || 'Payment confirmation failed';
      setError(errorMsg);
    }

    setLoading(false);
  };

  if (success) {
    if (planName === 'Elite') {
      return (
        <div className="text-center py-8">
          <div className="text-6xl mb-4">👑</div>
          <h2 className="text-2xl font-bold text-green-600 mb-4">Elite Upgrade Successful!</h2>
          <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6 mb-6">
            <h3 className="text-lg font-bold text-yellow-800 mb-2">Important Next Step</h3>
            <p className="text-yellow-700 mb-4">
              To activate all your Elite features (Custom Models, White-Label options, etc.), 
              please contact our VIP support team immediately.
            </p>
            <a 
              href="mailto:kojackkovid@gmail.com"
              className="inline-block bg-yellow-100 text-yellow-800 font-bold px-4 py-2 rounded-lg hover:bg-yellow-200 transition-colors"
            >
              kojackkovid@gmail.com
            </a>
          </div>
          <p className="text-gray-600">Redirecting to your dashboard in a moment...</p>
        </div>
      );
    }

    return (
      <div className="text-center py-8">
        <div className="text-6xl mb-4">✅</div>
        <h2 className="text-2xl font-bold text-green-600 mb-2">Payment Successful!</h2>
        <p className="text-gray-600">Redirecting to your dashboard...</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit}>
      {error && (
        <div className="mb-6 p-4 bg-red-50 border-2 border-red-500 rounded-lg text-red-700 font-semibold">
          <p className="mb-2">❌ Payment Error</p>
          <p className="text-sm">{error}</p>
        </div>
      )}

      {!error && (
        <div className="mb-6">
          <PaymentElement />
        </div>
      )}

      <button
        type="submit"
        disabled={!stripe || loading || !!error}
        className="w-full py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold rounded-xl hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? (
          <>
            <span className="inline-block animate-spin mr-2">⏳</span>
            Processing...
          </>
        ) : !stripe ? (
          'Loading Stripe... Please wait'
        ) : (
          `Pay $${price}`
        )}
      </button>

      <button
        type="button"
        onClick={() => navigate('/pricing')}
        className="w-full mt-4 py-3 bg-gray-200 text-gray-700 font-semibold rounded-xl hover:bg-gray-300 transition-all"
      >
        Cancel
      </button>

      <p className="mt-6 text-xs text-gray-500 text-center">
        🔒 Payments are securely processed by Stripe
      </p>
    </form>
  );
};

const Payment: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user: _user, isAuthenticated } = useAuthStore();

  const [clientSecret, setClientSecret] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stripePromiseState, setStripePromiseState] = useState<Promise<Stripe | null> | null>(null);

  const plan = searchParams.get('plan') || 'basic';
  const cycle = searchParams.get('cycle') || 'monthly';

  const planDetails: Record<string, { name: string; price: number; priceAnnual: number }> = {
    basic: { name: 'Basic', price: 9, priceAnnual: 90 },
    pro: { name: 'Pro', price: 29, priceAnnual: 290 },
    pro_plus: { name: 'Pro Plus', price: 49, priceAnnual: 490 },
    elite: { name: 'Elite', price: 99, priceAnnual: 990 },
  };

  const selectedPlan = planDetails[plan] || planDetails.basic;
  const price = cycle === 'annual' ? selectedPlan.priceAnnual : selectedPlan.price;

  useEffect(() => {
    setStripePromiseState(getStripePromise());
  }, []);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    // Create payment intent
    const createPaymentIntent = async () => {
      try {
        const response = await api.post('/payment/create-payment-intent', {
          plan: plan,
          billing_cycle: cycle,
        });

        const clientSecretValue = response.data?.client_secret;
        
        if (!clientSecretValue) {
          setError('Payment initialization failed. Please try again.');
          setLoading(false);
          return;
        }
        
        setClientSecret(clientSecretValue);
        setLoading(false);
      } catch (err: any) {
        console.error('[Payment] Error creating payment intent:', err?.message);
        
        const detailedError = err?.response?.status === 401 
          ? 'Please log in again to continue'
          : err?.response?.data?.detail || err?.message || 'Failed to initialize payment. Please try again.';
          
        setError(detailedError);
        setLoading(false);
      }
    };

    createPaymentIntent();
  }, [isAuthenticated, plan, cycle, navigate]);

  const options = {
    clientSecret: clientSecret || undefined,
    appearance: {
      theme: 'stripe' as const,
      variables: {
        colorPrimary: '#2563eb',
      },
    },
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 pt-24 px-4">
      <div className="max-w-md mx-auto bg-white rounded-2xl shadow-xl p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Complete Your Upgrade</h1>

        <div className="mb-8 p-6 bg-gray-50 rounded-xl">
          <div className="flex justify-between items-center mb-4">
            <span className="text-gray-600">Plan:</span>
            <span className="text-xl font-bold text-gray-900">{selectedPlan.name}</span>
          </div>
          <div className="flex justify-between items-center mb-4">
            <span className="text-gray-600">Billing Cycle:</span>
            <span className="text-lg font-semibold text-gray-900">
              {cycle === 'monthly' ? 'Monthly' : 'Annual'}
            </span>
          </div>
          <div className="flex justify-between items-center pt-4 border-t border-gray-200">
            <span className="text-gray-600">Total:</span>
            <span className="text-2xl font-bold text-blue-600">${price}</span>
          </div>
        </div>

        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
            <p className="text-gray-600 font-semibold">Initializing payment system...</p>
            <p className="text-xs text-gray-500 mt-2">This may take a moment...</p>
          </div>
        )}

        {!loading && error && (
          <div className="p-4 bg-red-50 border-2 border-red-500 rounded-lg text-red-700 mb-6">
            <p className="font-bold mb-2">❌ Payment Error</p>
            <p className="text-sm mb-3">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="text-sm text-red-600 hover:text-red-800 underline font-semibold"
            >
              Click to refresh page and try again
            </button>
          </div>
        )}

        {!loading && !error && clientSecret && stripePromiseState && (
          <>
            <p className="text-sm text-green-600 mb-4 font-semibold">✅ Payment system ready. Enter your card below.</p>
            <Elements stripe={stripePromiseState} options={options}>
              <CheckoutForm plan={plan} cycle={cycle} price={price} planName={selectedPlan.name} />
            </Elements>
          </>
        )}

        {!loading && !error && clientSecret && !stripePromiseState && (
          <div className="p-4 bg-yellow-50 border-2 border-yellow-400 rounded-lg text-yellow-700">
            <p className="font-bold mb-2">⚠️ Loading Payment System</p>
            <p>Stripe is initializing... Please wait.</p>
          </div>
        )}

        {!loading && !error && !clientSecret && !stripePromiseState && (
          <div className="p-4 bg-red-50 border-2 border-red-500 rounded-lg text-red-700">
            <p className="font-bold mb-2">❌ Stripe Configuration Missing</p>
            <p className="text-sm mb-3">
              The payment system is not properly configured. The Stripe API key might be missing from the environment configuration.
            </p>
            <p className="text-xs text-red-600 mb-3">
              This is a server configuration issue. Please contact support if this persists.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="text-sm bg-red-100 hover:bg-red-200 px-4 py-2 rounded font-semibold"
            >
              Try Again
            </button>
          </div>
        )}

        {!loading && !error && !clientSecret && (
          <div className="p-4 bg-red-50 border-2 border-red-500 rounded-lg text-red-700">
            <p className="font-bold mb-2">❌ Could Not Load Payment</p>
            <p className="text-sm mb-3">The payment system failed to initialize.</p>
            <button
              onClick={() => window.location.reload()}
              className="text-sm bg-red-100 hover:bg-red-200 px-4 py-2 rounded font-semibold"
            >
              Refresh and try again
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Payment;
