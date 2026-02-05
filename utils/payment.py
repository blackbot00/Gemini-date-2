import httpx
import uuid
import logging
import re  # Added for name cleaning
from config import CASHFREE_APP_ID, CASHFREE_SECRET_KEY

BASE_URL = "https://api.cashfree.com/pg/links" 

async def create_cashfree_order(user_id, amount, customer_name="User"):
    # CLEANING NAME: Only keep alphabets and spaces (Cashfree requirement)
    clean_name = re.sub(r'[^a-zA-Z\s]', '', customer_name).strip()
    
    # Name romba short-ah or empty-ah iruntha "User" nu fallback kudukanum
    if not clean_name or len(clean_name) < 3:
        clean_name = "Premium User"

    link_id = f"LNK_{user_id}_{uuid.uuid4().hex[:5]}"
    
    headers = {
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY,
        "x-api-version": "2025-01-01",
        "accept": "application/json",
        "content-type": "application/json"
    }

    payload = {
        "link_id": link_id,
        "link_amount": float(amount),
        "link_currency": "INR",
        "link_purpose": "Premium Upgrade",
        "customer_details": {
            "customer_phone": "6369622403", 
            "customer_name": clean_name, # Cleaned name sent here
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
                return data.get("link_url"), link_id
            else:
                logging.error(f"Cashfree API Error: {response.text}")
                return None, None
        except Exception as e:
            logging.error(f"Gateway Connection Error: {e}")
            return None, None
            
