import requests

def create_cashfree_order(user_id, amount):
    # Cashfree API integration logic
    # Amount logic: 1 week = 29, 1 month = 79, 3 month = 149
    url = "https://sandbox.cashfree.com/pg/orders" # Use production URL for live
    headers = {
        "x-client-id": "YOUR_ID",
        "x-client-secret": "YOUR_SECRET",
        "x-api-version": "2022-09-01"
    }
    payload = {
        "order_id": f"order_{user_id}_{amount}",
        "order_amount": amount,
        "order_currency": "INR",
        "customer_details": {"customer_id": str(user_id), "customer_phone": "9999999999"}
    }
    # Return payment link to bot

