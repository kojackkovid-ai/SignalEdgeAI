import asyncio
import httpx
import json
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

async def test_payment():
    """Test payment endpoint to see exact error"""
    
    # First, register and login
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        try:
            # Try payment with a valid token (use existing user or register first)
            payment_resp = await client.post(
                "/api/payment/create-payment-intent",
                headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0Njg4OWY0MS0yODczLTRlODAtYmMwYi1hNTUwN2M4YmI5YjUiLCJleHAiOjE3NDQ1MzQwMDAsImlhdCI6MTc0NDQxNDAwMH0.invalid"},
                json={
                    "plan": "pro",
                    "billing_cycle": "monthly"
                }
            )
            
            print(f"Payment Response Status: {payment_resp.status_code}")
            print(f"Payment Response Body: {json.dumps(payment_resp.json(), indent=2)}")
        except Exception as e:
            print(f"Error: {str(e)}")

asyncio.run(test_payment())
