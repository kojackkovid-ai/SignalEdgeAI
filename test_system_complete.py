#!/usr/bin/env python3
"""
COMPLETE SYSTEM TEST - Sports Prediction Platform
Tests all features end-to-end including auth, predictions, and payment
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5174"

print("\n" + "="*80)
print("COMPLETE SYSTEM TEST - Sports Prediction Platform")
print("="*80)

test_results = []
test_user_token = None
test_user_id = None

def log_test(name, passed, details=""):
    status = "✓ PASS" if passed else "✗ FAIL"
    test_results.append((name, passed, details))
    print(f"{status:8} | {name}")
    if details:
        print(f"         | {details}")

def log_section(title):
    print(f"\n{'-'*80}")
    print(f"  {title}")
    print(f"{'-'*80}")

# ============================================================================
# 1. SYSTEM HEALTH CHECKS
# ============================================================================
log_section("1. SYSTEM HEALTH CHECKS")

try:
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    log_test("Backend Server Running", r.status_code == 200, f"Status: {r.status_code}")
except Exception as e:
    log_test("Backend Server Running", False, f"Error: {e}")
    print("\n❌ FATAL: Backend not responding. Test aborted.")
    exit(1)

try:
    r = requests.get(FRONTEND_URL, timeout=5)
    log_test("Frontend Server Running", r.status_code == 200, f"Status: {r.status_code}")
except Exception as e:
    log_test("Frontend Server Running", False, f"Error: {e}")

# ============================================================================
# 2. AUTHENTICATION FLOW
# ============================================================================
log_section("2. AUTHENTICATION FLOW")

# Generate unique test credentials
timestamp = int(time.time())
test_email = f"systemtest_{timestamp}@test.com"
test_password = "SecurePass123!"
test_username = f"systemtest_{timestamp}"

# Test Registration
try:
    r = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={
            "email": test_email,
            "password": test_password,
            "username": test_username
        },
        timeout=10
    )
    success = r.status_code == 200
    log_test("User Registration", success, f"Email: {test_email}, Status: {r.status_code}")
    if not success:
        print(f"         | Response: {r.text[:200]}")
except Exception as e:
    log_test("User Registration", False, f"Error: {e}")
    exit(1)

# Test Login
try:
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "email": test_email,
            "password": test_password
        },
        timeout=10
    )
    if r.status_code == 200:
        data = r.json()
        test_user_token = data.get("access_token")
        test_user_id = data.get("user_id")
        tier = data.get("subscription_tier", "unknown")
        log_test("User Login", True, f"Token received, Tier: {tier}, User ID: {test_user_id}")
    else:
        log_test("User Login", False, f"Status: {r.status_code}, Response: {r.text[:200]}")
        exit(1)
except Exception as e:
    log_test("User Login", False, f"Error: {e}")
    exit(1)

headers = {"Authorization": f"Bearer {test_user_token}"}

# Test Get User Profile
try:
    r = requests.get(f"{BASE_URL}/api/users/me", headers=headers, timeout=10)
    if r.status_code == 200:
        user_data = r.json()
        log_test("Get User Profile", True, f"Username: {user_data.get('username')}, Email: {user_data.get('email')}")
    else:
        log_test("Get User Profile", False, f"Status: {r.status_code}")
except Exception as e:
    log_test("Get User Profile", False, f"Error: {e}")

# Test Invalid Token
try:
    bad_headers = {"Authorization": "Bearer invalid_token_12345"}
    r = requests.get(f"{BASE_URL}/api/users/me", headers=bad_headers, timeout=10)
    log_test("Invalid Token Rejection", r.status_code == 401, f"Status: {r.status_code}")
except Exception as e:
    log_test("Invalid Token Rejection", False, f"Error: {e}")

# ============================================================================
# 3. PREDICTIONS API
# ============================================================================
log_section("3. PREDICTIONS API")

# Test Get Predictions (Authenticated)
try:
    r = requests.get(f"{BASE_URL}/api/predictions/", headers=headers, timeout=30)
    if r.status_code == 200:
        predictions = r.json()
        count = len(predictions) if isinstance(predictions, list) else 0
        log_test("Get Predictions (Auth)", True, f"Received {count} predictions")
        
        # Check prediction structure
        if count > 0:
            pred = predictions[0]
            has_required_fields = all(k in pred for k in ["id", "sport", "home_team", "away_team", "prediction"])
            log_test("Prediction Data Structure", has_required_fields, 
                    f"Sample: {pred.get('sport')} - {pred.get('home_team')} vs {pred.get('away_team')}")
            
            # Check for supported sports only
            sports = [p.get('sport') for p in predictions]
            valid_sports = {'NFL', 'NBA', 'NHL', 'EPL', 'MLS'}
            invalid_sports = [s for s in sports if s not in valid_sports]
            log_test("Sport Filtering", len(invalid_sports) == 0, 
                    f"Sports: {set(sports)}, Invalid: {invalid_sports if invalid_sports else 'None'}")
        else:
            log_test("Prediction Data Available", False, "No predictions returned")
    else:
        log_test("Get Predictions (Auth)", False, f"Status: {r.status_code}")
except Exception as e:
    log_test("Get Predictions (Auth)", False, f"Error: {e}")

# Test Get Public Predictions
try:
    r = requests.get(f"{BASE_URL}/api/predictions/public", timeout=30)
    if r.status_code == 200:
        public_preds = r.json()
        count = len(public_preds) if isinstance(public_preds, list) else 0
        log_test("Get Public Predictions", True, f"Received {count} predictions")
    else:
        log_test("Get Public Predictions", False, f"Status: {r.status_code}")
except Exception as e:
    log_test("Get Public Predictions", False, f"Error: {e}")

# Test Predictions Without Auth
try:
    r = requests.get(f"{BASE_URL}/api/predictions/", timeout=10)
    log_test("Predictions Require Auth", r.status_code == 401, f"Status: {r.status_code}")
except Exception as e:
    log_test("Predictions Require Auth", False, f"Error: {e}")

# ============================================================================
# 4. PAYMENT INTEGRATION
# ============================================================================
log_section("4. PAYMENT INTEGRATION")

# Test all payment intent creations
payment_plans = [
    ("basic", "monthly", 900),
    ("basic", "annual", 9000),
    ("pro", "monthly", 2900),
    ("pro", "annual", 29000),
    ("elite", "monthly", 9900),
    ("elite", "annual", 99000),
]

created_payment_intents = []

for plan, cycle, expected_amount in payment_plans:
    try:
        r = requests.post(
            f"{BASE_URL}/api/payment/create-payment-intent",
            headers=headers,
            json={"plan": plan, "billing_cycle": cycle},
            timeout=15
        )
        if r.status_code == 200:
            data = r.json()
            client_secret = data.get("client_secret")
            payment_id = data.get("payment_intent_id")
            amount = data.get("amount")
            
            success = (client_secret and payment_id and amount == expected_amount)
            log_test(f"Payment Intent: {plan.title()} {cycle.title()}", success,
                    f"Amount: ${amount/100:.2f}, ID: {payment_id[:20]}...")
            
            if success:
                created_payment_intents.append(payment_id)
        else:
            log_test(f"Payment Intent: {plan.title()} {cycle.title()}", False,
                    f"Status: {r.status_code}, Response: {r.text[:100]}")
    except Exception as e:
        log_test(f"Payment Intent: {plan.title()} {cycle.title()}", False, f"Error: {e}")

# Test Invalid Plan
try:
    r = requests.post(
        f"{BASE_URL}/api/payment/create-payment-intent",
        headers=headers,
        json={"plan": "invalid_plan", "billing_cycle": "monthly"},
        timeout=10
    )
    log_test("Invalid Plan Rejection", r.status_code == 400, f"Status: {r.status_code}")
except Exception as e:
    log_test("Invalid Plan Rejection", False, f"Error: {e}")

# ============================================================================
# 5. MODEL API
# ============================================================================
log_section("5. MODEL API")

# Test Model Status
try:
    r = requests.get(f"{BASE_URL}/api/models/status", timeout=10)
    if r.status_code == 200:
        models = r.json()
        count = len(models) if isinstance(models, list) else 0
        log_test("Get Model Status", True, f"Received status for {count} models")
        
        if count > 0:
            model_names = [m.get('name') for m in models]
            log_test("Model Ensemble Present", 'ensemble' in model_names or count >= 3,
                    f"Models: {', '.join(model_names)}")
    else:
        log_test("Get Model Status", False, f"Status: {r.status_code}")
except Exception as e:
    log_test("Get Model Status", False, f"Error: {e}")

# ============================================================================
# 6. SECURITY TESTS
# ============================================================================
log_section("6. SECURITY TESTS")

# Test SQL Injection in Email
try:
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "' OR '1'='1", "password": "anything"},
        timeout=10
    )
    log_test("SQL Injection Protection", r.status_code == 401, f"Status: {r.status_code}")
except Exception as e:
    log_test("SQL Injection Protection", False, f"Error: {e}")

# Test XSS in Username
try:
    xss_username = "<script>alert('xss')</script>"
    r = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={
            "email": f"xss_test_{timestamp}@test.com",
            "password": "SecurePass123!",
            "username": xss_username
        },
        timeout=10
    )
    # Should either reject or sanitize
    log_test("XSS Input Handling", r.status_code in [200, 400, 422], f"Status: {r.status_code}")
except Exception as e:
    log_test("XSS Input Handling", False, f"Error: {e}")

# Test CORS Headers
try:
    r = requests.options(f"{BASE_URL}/api/predictions/", timeout=10)
    has_cors = 'access-control-allow-origin' in [h.lower() for h in r.headers.keys()]
    log_test("CORS Headers Present", has_cors, f"CORS configured: {has_cors}")
except Exception as e:
    log_test("CORS Headers Present", False, f"Error: {e}")

# ============================================================================
# TEST SUMMARY
# ============================================================================
log_section("TEST SUMMARY")

passed = sum(1 for _, p, _ in test_results if p)
failed = sum(1 for _, p, _ in test_results if not p)
total = len(test_results)
pass_rate = (passed / total * 100) if total > 0 else 0

print(f"\n{'='*80}")
print(f"  RESULTS: {passed}/{total} tests passed ({pass_rate:.1f}%)")
print(f"{'='*80}\n")

if failed > 0:
    print("❌ FAILED TESTS:")
    for name, passed, details in test_results:
        if not passed:
            print(f"   • {name}")
            if details:
                print(f"     {details}")
    print()

print(f"✓ Backend: http://localhost:8000")
print(f"✓ Frontend: http://localhost:5174")
print(f"✓ Test User: {test_email}")
print(f"✓ User ID: {test_user_id}")

if pass_rate >= 90:
    print("\n🎉 SYSTEM TEST PASSED - Platform is ready for use!")
elif pass_rate >= 70:
    print("\n⚠️  SYSTEM TEST PARTIALLY PASSED - Some issues need attention")
else:
    print("\n❌ SYSTEM TEST FAILED - Critical issues found")

print(f"\n{'='*80}\n")
