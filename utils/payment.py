import httpx
import uuid
import logging
from config import CASHFREE_APP_ID, CASHFREE_SECRET_KEY

# Real Payment API
BASE_URL = "https://api.cashfree.com/pg/orders" 

async def create_cashfree_order(user_id, amount, customer_name="User"):
    # Unique Order ID generation
    order_id = f"ORDER_{user_id}_{uuid.uuid4().hex[:6]}"
    
    headers = {
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY,
        "x-api-version": "2023-08-01",
        "Content-Type": "application/json"
    }

    payload = {
        "order_id": order_id,
        "order_amount": float(amount),
        "order_currency": "INR",
        "customer_details": {
            "customer_id": str(user_id),
            "customer_phone": "9999999999", # Required placeholder
            "customer_name": customer_name
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(BASE_URL, json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                # Session ID is key for generating the checkout URL
                return data.get("payment_session_id"), order_id
            else:
                logging.error(f"Cashfree API Error: {response.text}")
                return None, None
        except Exception as e:
            logging.error(f"Connection Error: {e}")
            return None, None
