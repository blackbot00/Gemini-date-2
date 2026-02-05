import httpx
import uuid
import logging
from config import CASHFREE_APP_ID, CASHFREE_SECRET_KEY

# Use Payment Links Endpoint
BASE_URL = "https://api.cashfree.com/pg/links" 

async def create_cashfree_order(user_id, amount, customer_name="User"):
    link_id = f"LNK_{user_id}_{uuid.uuid4().hex[:5]}"
    
    headers = {
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY,
        "x-api-version": "2025-01-01",
        "Content-Type": "application/json"
    }

    payload = {
        "link_id": link_id,
        "link_amount": float(amount),
        "link_currency": "INR",
        "link_purpose": "Premium Upgrade",
        "customer_details": {
            "customer_phone": "6369622403",
            "customer_name": customer_name,
            "customer_email": "user@example.com"
        },
        "link_meta": {
            "return_url": f"https://t.me/Coupledatingbot?start=verify_{link_id}"
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(BASE_URL, json=payload, headers=headers)
            data = response.json()
            if response.status_code == 200:
                # Direct URL kidaikum
                return data.get("link_url"), link_id
            else:
                logging.error(f"Cashfree Link Error: {response.text}")
                return None, None
        except Exception as e:
            logging.error(f"Connection Error: {e}")
            return None, None
    
