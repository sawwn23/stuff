from strands import tool
import json



# A mock database for demonstration purposes
MOCK_ORDERS_DB = {
    "12345": {"status": "Shipped", "estimated_delivery": "2025-10-28"},
    "67890": {"status": "Processing", "items": []},
}

@tool #decorator to register the function as a tool
def get_order_status(order_id: str) -> str:
    """
    Retrieves the current status and details for a given order ID.
    Use this tool to answer customer questions about their orders.
    """
    print(f"--- Tool: get_order_status called with order_id={order_id} ---")
    status = MOCK_ORDERS_DB.get(order_id)
    if status:
        return json.dumps(status)
    return json.dumps({"error": "Order not found."})

@tool
def lookup_return_policy(product_category: str) -> str:
    """
    Looks up the return policy for a specific product category.
    Valid categories are 'electronics', 'apparel', and 'home_goods'.
    """
    print(f"--- Tool: lookup_return_policy called with category={product_category} ---")
    policies = {
        "electronics": "Electronics can be returned within 30 days of purchase with original packaging.",
        "apparel": "Apparel can be returned within 60 days, provided it is unworn with tags attached.",
        "home_goods": "Home goods have a 90-day return policy."
    }
    return policies.get(product_category.lower(), "Sorry, I could not find a policy for that category.")

@tool
def initiate_refund(order_id: str, reason: str) -> str:
    """
    Initiates a refund process for a given order ID and reason.
    Only use this tool when a customer explicitly requests a refund.
    Returns a confirmation number for the refund request.
    """
    print(f"--- Tool: initiate_refund called for order_id={order_id} ---")
    if order_id in MOCK_ORDERS_DB:
        # create a short deterministic confirmation token from the reason
        token = str(abs(hash(reason)))[:6]
        confirmation_number = f"REF-{order_id}-{token}"
        return json.dumps({"status": "Refund initiated", "confirmation_number": confirmation_number})
    return json.dumps({"error": "Cannot initiate refund. Order not found."})