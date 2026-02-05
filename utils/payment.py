import httpx
import uuid
import logging
from config import CASHFREE_APP_ID, CASHFREE_SECRET_KEY

# Production API URL
BASE_URL = "https://api.cashfree.com/pg/orders" 

async def create_cashfree_order(user_id, amount, customer_name="User"):
    # Unique Order ID
    order_id = f"CF_{user_id}_{uuid.uuid4().hex[:5]}"
    
    headers = {
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY,
        "x-api-version": "2023-08-01",
        "accept": "application/json",
        "content-type": "application/json"
    }

    # IMPORTANT: Real phone number format and valid email is needed for PROD
    payload = {
        "order_id": order_id,
        "order_amount": float(amount),
        "order_currency": "INR",
        "customer_details": {
            "customer_id": str(user_id),
            "customer_phone": "6369622403", # Valid number (screenshot-la irunthathu)
            "customer_name": customer_name,
            "customer_email": "user@example.com" # Required in some cases
        },
        "order_meta": {
            "return_url": f"https://t.me/Coupledatingbot?start=verify_{order_id}",
            "payment_methods": "upi,cc,dc,nb"
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(BASE_URL, json=payload, headers=headers)
            data = response.json()
            
            if response.status_code == 200:
                # SDK session_id pathila, Direct Payment Link edukka porom
                # Sila samayam 'payment_link' field-la varum
                payment_link = data.get("payments", {}).get("url") 
                
                # If 'payments' is empty, it means we need to use the Session flow
                # For Telegram Bots, Payment Link is the easiest:
                session_id = data.get("payment_session_id")
                
                # Inga dhaan logic: 
                # Create a simple checkout URL using session_id if direct link is missing
                checkout_url = f"https://payments.cashfree.com/order/#/{session_id}"
                
                return checkout_url, order_id
            else:
                logging.error(f"Cashfree Error: {response.text}")
                return None, None
        except Exception as e:
            logging.error(f"Payment logic error: {e}")
            return None, None
            
