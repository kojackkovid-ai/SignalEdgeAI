#!/usr/bin/env python3
"""
Test payment endpoint without needing database running
Just check if the code itself has errors
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("\n" + "=" * 70)
print("PAYMENT ENDPOINT CODE ANALYSIS")
print("=" * 70)

# Test 1: Check the payment route file for syntax errors
print("\n1. Checking payment.py for syntax errors...")
try:
    import ast
    with open("app/routes/payment.py", "r") as f:
        code = f.read()
    ast.parse(code)
    print("   ✓ No syntax errors in payment.py")
except SyntaxError as e:
    print(f"   ✗ Syntax error in payment.py:")
    print(f"      Line {e.lineno}: {e.msg}")
    print(f"      {e.text}")
    sys.exit(1)

# Test 2: Try to parse the payment route without fully importing
print("\n2. Analyzing payment route structure...")
try:
    with open("app/routes/payment.py", "r") as f:
        lines = f.readlines()
    
    # Check for required class definitions
    required_classes = ["CreatePaymentIntentRequest", "PaymentIntentResponse", "ConfirmPaymentRequest"]
    router_name = "router"
    post_decorators = 0
    
    code = "".join(lines)
    for cls in required_classes:
        if f"class {cls}" in code:
            print(f"   ✓ Found class: {cls}")
        else:
            print(f"   ✗ Missing class: {cls}")
    
    if f"{router_name} = APIRouter()" in code:
        print(f"   ✓ Found: router = APIRouter()")
    
    # Count post decorators
    post_lines = [l for l in lines if "@router.post" in l]
    print(f"   ✓ Found {len(post_lines)} @router.post decorators")
    for line in post_lines:
        print(f"      - {line.strip()}")
    
except Exception as e:
    print(f"   ✗ Error analyzing routes: {e}")
    sys.exit(1)

# Test 3: Check dependencies
print("\n3. Checking imports in payment.py...")
try:
    with open("app/routes/payment.py", "r") as f:
        lines = f.readlines()
    
    imports = [l.strip() for l in lines if l.startswith("from ") or l.startswith("import ")]
    required_imports = [
        "from fastapi import",
        "from sqlalchemy.ext.asyncio import AsyncSession",
        "from pydantic import BaseModel",
        "from app.database import get_db",
        "from app.services.auth_service import AuthService",
        "from app.services.stripe_service import stripe_service",
        "from app.services.audit_service import get_audit_service",
    ]
    
    for req_import in required_imports:
        found = any(req_import in imp for imp in imports)
        if found:
            print(f"   ✓ {req_import}")
        else:
            print(f"   ✗ MISSING: {req_import}")
    
except Exception as e:
    print(f"   ✗ Error checking imports: {e}")
    sys.exit(1)

# Test 4: Check the get_current_user dependency
print("\n4. Checking authentication dependency...")
try:
    with open("app/routes/payment.py", "r") as f:
        content = f.read()
    
    if "async def get_current_user" in content:
        print("   ✓ Found get_current_user function")
    else:
        print("   ✗ MISSING: get_current_user function")
    
    if "def get_auth_service()" in content:
        print("   ✓ Found get_auth_service function")
    else:
        print("   ✗ MISSING: get_auth_service function")
    
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 5: Check create_payment_intent function
print("\n5. Checking create_payment_intent function...")
try:
    with open("app/routes/payment.py", "r") as f:
        content = f.read()
    
    if "@router.post(\"/create-payment-intent\"" in content:
        print("   ✓ Found @router.post(\"/create-payment-intent\") decorator")
    else:
        print("   ! Not found - checking format...")
        if "@router.post" in content and "create-payment-intent" in content:
            print("   ~ Decorator exists but format might be different")
    
    if "async def create_payment_intent(" in content:
        print("   ✓ Found async def create_payment_intent function")
    else:
        print("   ✗ MISSING: create_payment_intent function")
    
    # Check if it uses stripe_service
    if "stripe_service.create_payment_intent" in content:
        print("   ✓ Uses stripe_service.create_payment_intent")
    else:
        print("   ✗ Not using stripe_service.create_payment_intent")
    
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70 + "\n")
