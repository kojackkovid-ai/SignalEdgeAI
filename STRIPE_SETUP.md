# Stripe Payment Integration Setup

## Required Package Installation

Run these commands to complete the Stripe integration:

### Backend (Python/FastAPI)
```bash
cd sports-prediction-platform/backend
pip install stripe==8.0.0
```

### Frontend (React/TypeScript)
```bash
cd sports-prediction-platform/frontend
npm install @stripe/stripe-js @stripe/react-stripe-js
```

## Configuration Files Updated

✅ **Backend `.env`** - Stripe keys added:
- `STRIPE_PUBLIC_KEY=pk_test_your_public_key_here`
- `STRIPE_SECRET_KEY=sk_test_your_secret_key_here`

✅ **Frontend `.env`** - Stripe publishable key added:
- `VITE_STRIPE_PUBLISHABLE_KEY=pk_test_your_public_key_here`

## Files Created/Modified

### Backend
- ✅ Created `app/services/stripe_service.py` - Stripe payment service
- ✅ Created `app/routes/payment.py` - Payment endpoints
- ✅ Updated `app/main.py` - Added payment router
- ✅ Updated `.env` - Added Stripe keys

### Frontend
- ✅ Updated `src/pages/Payment.tsx` - Full Stripe Elements integration
- ✅ Updated `src/pages/Pricing.tsx` - Redirects authenticated users to payment page
- ✅ Updated `src/App.tsx` - Added payment route
- ✅ Updated `src/utils/api.ts` - Added generic HTTP methods
- ✅ Updated `.env` - Added Stripe publishable key

## How the Payment Flow Works

1. **User clicks "Upgrade" on Pricing page**
   - Unauthenticated: Redirected to `/register`
   - Authenticated: Redirected to `/payment?plan=pro&cycle=monthly`

2. **Payment page initializes**
   - Frontend calls `POST /api/payment/create-payment-intent`
   - Backend creates Stripe PaymentIntent
   - Returns `client_secret` to frontend

3. **User enters card details**
   - Stripe Elements renders secure payment form
   - Card data never touches your server

4. **User clicks "Pay"**
   - Frontend calls `stripe.confirmPayment()` with Stripe Elements
   - Stripe processes payment securely
   - Returns PaymentIntent with status

5. **Payment confirmed**
   - Frontend calls `POST /api/payment/confirm-payment` with `payment_intent_id`
   - Backend verifies payment with Stripe API
   - Updates user's `subscription_tier` in database
   - Returns success response

6. **User tier updated**
   - Frontend updates Zustand store
   - User redirected to `/dashboard`
   - Dashboard shows tier-appropriate features

## API Endpoints

### POST `/api/payment/create-payment-intent`
**Request:**
```json
{
  "plan": "pro",
  "billing_cycle": "monthly"
}
```

**Response:**
```json
{
  "client_secret": "pi_xxx_secret_xxx",
  "payment_intent_id": "pi_xxx",
  "amount": 2900
}
```

### POST `/api/payment/confirm-payment`
**Request:**
```json
{
  "payment_intent_id": "pi_xxx",
  "plan": "pro"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Subscription upgraded successfully",
  "new_tier": "pro",
  "payment_intent_id": "pi_xxx"
}
```

## Testing with Stripe Test Cards

Use these test card numbers in the Stripe Elements form:

### Successful Payment
- **Card Number:** `4242 4242 4242 4242`
- **Expiry:** Any future date (e.g., `12/34`)
- **CVC:** Any 3 digits (e.g., `123`)

### Payment Declined
- **Card Number:** `4000 0000 0000 0002`

### Requires Authentication (3D Secure)
- **Card Number:** `4000 0025 0000 3155`

### Insufficient Funds
- **Card Number:** `4000 0000 0000 9995`

## Restart Servers After Installation

After installing the packages, restart both servers:

### Backend
```bash
cd sports-prediction-platform/backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd sports-prediction-platform/frontend
npm run dev
```

## Security Notes

⚠️ **IMPORTANT:** These are TEST keys. For production:

1. **Replace with production keys** from Stripe Dashboard
2. **Enable webhook signing** for payment confirmations
3. **Add webhook endpoint** at `/api/payment/webhook`
4. **Implement proper error handling** for failed payments
5. **Add email notifications** for successful subscriptions
6. **Implement subscription management** (cancel, change plan)
7. **Add billing history** tracking in database

## Verification Steps

1. Install packages (run commands above)
2. Restart servers
3. Register/Login to the platform
4. Navigate to Pricing page
5. Click "Upgrade" on any paid plan
6. Payment page should load with Stripe Elements
7. Enter test card `4242 4242 4242 4242`
8. Click "Pay" button
9. Should see success message and redirect to dashboard
10. Verify tier is updated in dashboard

## Troubleshooting

**Error: "stripe is not defined"**
- Solution: Run `pip install stripe` in backend directory

**Error: "@stripe/stripe-js not found"**
- Solution: Run `npm install @stripe/stripe-js @stripe/react-stripe-js` in frontend directory

**Error: "STRIPE_SECRET_KEY not set"**
- Solution: Check backend `.env` file has the correct key

**Payment form not showing**
- Solution: Check frontend `.env` has `VITE_STRIPE_PUBLISHABLE_KEY`
- Solution: Restart frontend dev server to load new env variable

**Payment succeeds but tier not updated**
- Solution: Check backend logs for errors in `/api/payment/confirm-payment`
- Solution: Verify database connection is working
