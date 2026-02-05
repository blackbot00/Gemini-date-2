import httpx
import uuid
import logging
from config import CASHFREE_APP_ID, CASHFREE_SECRET_KEY

# Production API URL for Links
BASE_URL = "https://api.cashfree.com/pg/links" 

async def create_cashfree_order(user_id, amount, customer_name="User"):
    link_id = f"LNK_{user_id}_{uuid.uuid4().hex[:5]}"
    
    headers = {
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY,
        "x-api-version": "2023-08-01",
        "accept": "application/json",
        "content-type": "application/json"
    }

    payload = {
        "link_id": link_id,
        "link_amount": float(amount),
        "link_currency": "INR",
        "link_purpose": f"Premium upgrade for {user_id}",
        "customer_details": {
            "customer_phone": "6369622403", # Your valid number
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
            
            # Debugging kaaga:
            if response.status_code != 200:
                logging.error(f"Cashfree API Error: {response.text}")
                return None, None

            # Cashfree Link URL extraction
            link_url = data.get("link_url")
            if link_url:
                return link_url, link_id
            else:
                return None, None
                
        except Exception as e:
            logging.error(f"Gateway Connection Error: {e}")
            return None, None
            
