"""MercadoPago PIX payment service."""
import os
import logging
import mercadopago
import uuid

logger = logging.getLogger(__name__)

ACCESS_TOKEN = os.environ.get("MERCADOPAGO_ACCESS_TOKEN", "")

# Plans: name -> (price, coins, diamonds)
PLANS = {
    "basico": {"price": 15.00, "coins": 150, "diamonds": 0, "label": "⚡ Básico"},
    "premium": {"price": 30.00, "coins": 300, "diamonds": 5, "label": "💎 Premium"},
    "ultra": {"price": 60.00, "coins": 700, "diamonds": 10, "label": "👑 Ultra"},
}

# Cost per generation (in coins/diamonds)
COST_PER_IMAGE = 2  # 2 coins per image
COST_PER_VIDEO_4S = 1  # 1 diamond per 4s video
COST_PER_VIDEO_8S = 2  # 2 diamonds per 8s video


def get_sdk():
    return mercadopago.SDK(ACCESS_TOKEN)


def create_pix_payment(user_id: int, plan: str) -> dict:
    """Create a PIX payment for a plan. Returns dict with qr_code or error."""
    if not ACCESS_TOKEN:
        return {"error": "MercadoPago not configured"}

    plan_data = PLANS.get(plan)
    if not plan_data:
        return {"error": "Invalid plan"}

    sdk = get_sdk()
    idempotency_key = str(uuid.uuid4())

    payment_data = {
        "transaction_amount": plan_data["price"],
        "description": f"Bilion Luxure - Plano {plan_data['label']}",
        "payment_method_id": "pix",
        "payer": {
            "email": f"user{user_id}@telegram.bilionluxure",
        },
        "external_reference": f"bilion_{user_id}_{plan}",
    }

    try:
        result = sdk.payment().create(payment_data, idempotency_key)
        payment = result.get("response", {})

        if payment.get("id"):
            return {
                "success": True,
                "payment_id": str(payment["id"]),
                "qr_code": payment.get("point_of_interaction", {})
                    .get("transaction_data", {})
                    .get("qr_code_base64", ""),
                "qr_code_link": payment.get("point_of_interaction", {})
                    .get("transaction_data", {})
                    .get("ticket_url", ""),
                "amount": plan_data["price"],
            }
        else:
            return {"error": f"Payment creation failed: {payment}"}

    except Exception as e:
        logger.error(f"MercadoPago error: {e}")
        return {"error": str(e)}


def check_payment(payment_id: str) -> str:
    """Check payment status. Returns 'approved', 'pending', or 'error'."""
    try:
        sdk = get_sdk()
        result = sdk.payment().get(payment_id)
        payment = result.get("response", {})
        return payment.get("status", "error")
    except Exception as e:
        logger.error(f"Payment check error: {e}")
        return "error"
