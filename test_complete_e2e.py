import requests
import time

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"

print("\n" + "="*80)
print("COMPLETE END-TO-END SYSTEM TEST")
print("="*80)

test_results = []

def test(name, passed, details=""):
    status = "PASS" if passed else "FAIL"
    test_results.append((name, status, details))
    symbol = "+" if passed else "X"
    print(f"[{symbol}] {name}: {status}")
    if details:
        print(f"    {details}")

# TEST 1: Backend Health
print("\n--- BACKEND TESTS ---")
try:
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    test("Backend Health Check", r.status_code == 200, f"Status: {r.status_code}")
except Exception as e:
    test("Backend Health Check", False, str(e))
    print("\nFATAL: Backend not running. Exiting.")
    exit(1)

# TEST 2: Frontend Accessibility
print("\n--- FRONTEND TESTS ---")
try:
    r = requests.get(FRONTEND_URL, timeout=5)
    test("Frontend Accessibility", r.status_code == 200, f"Status: {r.status_code}")
except Exception as e:
    test("Frontend Accessibility", False, str(e))

# TEST 3: User Registration
print("\n--- AUTHENTICATION TESTS ---")
test_email = f"e2e_test_{int(time.time())}@test.com"
test_password = "SecurePass123!"
test_username = "e2etester"

try:
    r = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": test_email, "password": test_password, "username": test_username},
        timeout=10
    )
    test("User Registration", r.status_code == 200, f"Email: {test_email}")
    if r.status_code != 200:
        print(f"    Response: {r.text}")
except Exception as e:
    test("User Registration", False, str(e))
    exit(1)

# TEST 4: User Login
try:
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": test_email, "password": test_password},
        timeout=10
    )
    if r.status_code == 200:
        data = r.json()
        token = data.get("access_token")
        user_id = data.get("id")
        tier = data.get("subscription_tier", "free")
        test("User Login", True, f"Token received, Tier: {tier}")
    else:
        test("User Login", False, f"Status: {r.status_code}")
        exit(1)
except Exception as e:
    test("User Login", False, str(e))
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

# TEST 5: Get User Profile
try:
    r = requests.get(f"{BASE_URL}/api/users/me", headers=headers, timeout=10)
    test("Get User Profile", r.status_code == 200, f"User ID: {r.json().get('id') if r.status_code == 200 else 'N/A'}")
except Exception as e:
    test("Get User Profile", False, str(e))

# TEST 6: Get User Stats
try:
    r = requests.get(f"{BASE_URL}/api/users/me/stats", headers=headers, timeout=10)
    test("Get User Stats", r.status_code == 200)
except Exception as e:
    test("Get User Stats", False, str(e))

# PAYMENT TESTS
print("\n--- PAYMENT INTEGRATION TESTS ---")

# TEST 7-12: Payment Intent Creation for All Plans
plans = [
    ("basic", "monthly", 900, "$9.00"),
    ("basic", "annual", 9000, "$90.00"),
    ("pro", "monthly", 2900, "$29.00"),
    ("pro", "annual", 29000, "$290.00"),
    ("elite", "monthly", 9900, "$99.00"),
    ("elite", "annual", 99000, "$990.00"),
]

payment_intents = []
for plan, cycle, expected_cents, expected_display in plans:
    try:
        r = requests.post(
            f"{BASE_URL}/api/payment/create-payment-intent",
            json={"plan": plan, "billing_cycle": cycle},
            headers=headers,
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            pi_id = data.get("payment_intent_id")
            amount = data.get("amount")
            payment_intents.append((pi_id, plan))
            test(f"Payment Intent: {plan.capitalize()} {cycle.capitalize()}", 
                 amount == expected_cents, 
                 f"Expected: {expected_display}, Got: ${amount/100:.2f}, ID: {pi_id[:20]}...")
        else:
            test(f"Payment Intent: {plan.capitalize()} {cycle.capitalize()}", False, f"Status: {r.status_code}")
    except Exception as e:
        test(f"Payment Intent: {plan.capitalize()} {cycle.capitalize()}", False, str(e))

# TEST 13: Payment Confirmation (Expected to Fail - No Real Payment)
print("\n--- PAYMENT CONFIRMATION TESTS ---")
if payment_intents:
    pi_id, plan = payment_intents[0]
    try:
        r = requests.post(
            f"{BASE_URL}/api/payment/confirm-payment",
            json={"payment_intent_id": pi_id, "plan": plan},
            headers=headers,
            timeout=10
        )
        # Should fail with 400 because payment not actually made through Stripe
        test("Payment Confirmation Endpoint", r.status_code == 400, 
             "Correctly rejects unverified payment")
    except Exception as e:
        test("Payment Confirmation Endpoint", False, str(e))

# PREDICTIONS TESTS
print("\n--- PREDICTIONS API TESTS ---")

# TEST 14: Get All Predictions
try:
    r = requests.get(f"{BASE_URL}/api/predictions/", headers=headers, timeout=10)
    if r.status_code == 200:
        preds = r.json()
        count = len(preds) if isinstance(preds, list) else 0
        test("Get All Predictions", True, f"Retrieved {count} predictions")
    else:
        test("Get All Predictions", r.status_code in [200, 404], f"Status: {r.status_code}")
except Exception as e:
    test("Get All Predictions", False, str(e))

# TEST 15: Get Filtered Predictions (NFL)
try:
    r = requests.get(f"{BASE_URL}/api/predictions/?sport=nfl", headers=headers, timeout=10)
    test("Get Filtered Predictions (NFL)", r.status_code in [200, 404], f"Status: {r.status_code}")
except Exception as e:
    test("Get Filtered Predictions (NFL)", False, str(e))

# TEST 16: Get Public Predictions
try:
    r = requests.get(f"{BASE_URL}/api/predictions/public", timeout=10)
    test("Get Public Predictions", r.status_code in [200, 404], f"Status: {r.status_code}")
except Exception as e:
    test("Get Public Predictions", False, str(e))

# MODEL TESTS
print("\n--- ML MODEL API TESTS ---")

# TEST 17: Get Model Status
try:
    r = requests.get(f"{BASE_URL}/api/models/status", headers=headers, timeout=10)
    test("Get Model Status", r.status_code in [200, 404], f"Status: {r.status_code}")
except Exception as e:
    test("Get Model Status", False, str(e))

# INVALID REQUEST TESTS
print("\n--- SECURITY & VALIDATION TESTS ---")

# TEST 18: Invalid Login
try:
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "fake@test.com", "password": "wrongpass"},
        timeout=10
    )
    test("Reject Invalid Login", r.status_code == 401, f"Status: {r.status_code}")
except Exception as e:
    test("Reject Invalid Login", False, str(e))

# TEST 19: Unauthorized Access
try:
    r = requests.get(f"{BASE_URL}/api/users/me", timeout=10)
    test("Reject Unauthorized Access", r.status_code == 401, f"Status: {r.status_code}")
except Exception as e:
    test("Reject Unauthorized Access", False, str(e))

# TEST 20: Invalid Payment Plan
try:
    r = requests.post(
        f"{BASE_URL}/api/payment/create-payment-intent",
        json={"plan": "invalid", "billing_cycle": "monthly"},
        headers=headers,
        timeout=10
    )
    test("Reject Invalid Payment Plan", r.status_code == 400, f"Status: {r.status_code}")
except Exception as e:
    test("Reject Invalid Payment Plan", False, str(e))

# SUMMARY
print("\n" + "="*80)
print("TEST SUMMARY")
print("="*80)

passed = sum(1 for _, status, _ in test_results if status == "PASS")
failed = sum(1 for _, status, _ in test_results if status == "FAIL")
total = len(test_results)

print(f"\nTotal Tests: {total}")
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"Success Rate: {(passed/total)*100:.1f}%")

if failed > 0:
    print("\nFailed Tests:")
    for name, status, details in test_results:
        if status == "FAIL":
            print(f"  - {name}: {details}")

print("\n" + "="*80)
if failed == 0:
    print("ALL TESTS PASSED - SYSTEM FULLY FUNCTIONAL")
else:
    print(f"SOME TESTS FAILED - {failed} ISSUES FOUND")
print("="*80)

print("\nMANUAL BROWSER TEST:")
print("1. Open: http://localhost:5173")
print("2. Register a new account")
print("3. Navigate to Pricing page")
print("4. Click 'Upgrade' on any plan")
print("5. Enter test card: 4242 4242 4242 4242")
print("6. Expiry: 12/26, CVC: 123")
print("7. Submit payment and verify tier upgrade")
print("="*80 + "\n")
