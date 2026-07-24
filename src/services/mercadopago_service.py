"""MercadoPago PIX payment service com tracking financeiro."""
import os
import logging
import mercadopago

logger = logging.getLogger(__name__)

ACCESS_TOKEN = os.environ.get("MERCADOPAGO_ACCESS_TOKEN", "")

# Taxas MercadoPago Pix (atualizado 2026)
MP_FEE_PERCENTAGE = 0.0299  # 2,99%
MP_FEE_FIXED = 0.40  # R$0,40 por transação

# Plans: só coins, sem diamantes
PLANS = {
    "basico": {
        "price": 15.00,
        "coins": 150,
        "label": "⚡ Básico",
        "description": "150 coins",
    },
    "premium": {
        "price": 30.00,
        "coins": 350,
        "label": "💎 Premium",
        "description": "350 coins",
    },
    "ultra": {
        "price": 60.00,
        "coins": 800,
        "label": "👑 Ultra",
        "description": "800 coins",
    },
}

# Custos de geração (só coins)
COST_PER_IMAGE = 1       # 1 coin por imagem
COST_PER_VIDEO_4S = 15   # 15 coins por vídeo 4s
COST_PER_VIDEO_8S = 30   # 30 coins por vídeo 8s


def calculate_net_amount(price: float) -> float:
    """Calcula o valor líquido recebido após taxas do MercadoPago."""
    fee = (price * MP_FEE_PERCENTAGE) + MP_FEE_FIXED
    net = price - fee
    return round(net, 2)


def get_plan_cost_percentage(plan: str) -> float:
    """Quanto do valor pago é 'consumido' se o usuário gastar tudo em imagem."""
    plan_data = PLANS.get(plan)
    if not plan_data:
        return 0.0
    total_coins = plan_data["coins"]
    # Pior caso: tudo em imagem (1 coin = R$0,011 de custo real)
    max_gen_cost = total_coins * 0.011  # R$0,011 por imagem SDXL
    return round((max_gen_cost / plan_data["price"]) * 100, 1)


def get_sdk():
    return mercadopago.SDK(ACCESS_TOKEN)


def create_pix_payment(user_id: int, plan: str) -> dict:
    """Create a PIX payment for a plan. Returns dict with qr_code or error."""
    if not ACCESS_TOKEN:
        return {"error": "MercadoPago não configurado"}

    plan_data = PLANS.get(plan)
    if not plan_data:
        return {"error": "Plano inválido"}

    sdk = get_sdk()

    payment_data = {
        "transaction_amount": plan_data["price"],
        "description": f"Bilion Luxure - {plan_data['label']}",
        "payment_method_id": "pix",
        "payer": {
            "email": f"user{user_id}@example.com",
        },
        "external_reference": f"bilion_{user_id}_{plan}",
    }

    try:
        result = sdk.payment().create(payment_data)
        payment = result.get("response", {})

        if payment.get("id"):
            gross = plan_data["price"]
            net = calculate_net_amount(gross)
            return {
                "success": True,
                "payment_id": str(payment["id"]),
                "qr_code": payment.get("point_of_interaction", {})
                    .get("transaction_data", {})
                    .get("qr_code_base64", ""),
                "qr_code_text": payment.get("point_of_interaction", {})
                    .get("transaction_data", {})
                    .get("qr_code", ""),
                "qr_code_link": payment.get("point_of_interaction", {})
                    .get("transaction_data", {})
                    .get("ticket_url", ""),
                "amount_gross": gross,
                "amount_net": net,
                "amount": gross,  # compatibilidade
            }
        else:
            return {"error": f"Falha ao criar pagamento: {payment}"}

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
