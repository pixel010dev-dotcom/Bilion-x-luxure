"""Test sanidade do Bilion Luxure pós-refatoração."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.mercadopago_service import (
    PLANS, COST_PER_IMAGE, COST_PER_VIDEO_4S, COST_PER_VIDEO_8S,
    calculate_net_amount, get_plan_cost_percentage
)
from src.services.database import init_db, get_financial_summary

# Verifica constantes
print("=== CUSTOS ===")
print(f"Imagem: {COST_PER_IMAGE} coin")
print(f"Video 4s: {COST_PER_VIDEO_4S} coins")
print(f"Video 8s: {COST_PER_VIDEO_8S} coins")

print()
print("=== PACKS ===")
for k, v in PLANS.items():
    net = calculate_net_amount(v["price"])
    cost_pct = get_plan_cost_percentage(k)
    print(f"{v['label']}: R${v['price']:.2f} -> liquido R${net:.2f} | {v['coins']} coins | custo max {cost_pct}%")

print()
print("=== DB SCHEMA ===")
init_db()
print("DB ok")

print()
print("=== IMPORTS ===")
from src.handlers.start import start_handler, menu_callback
from src.handlers.img import img_handler
from src.handlers.video import video_handler
from src.handlers.payment import buy_handler, buy_callback, check_payment_callback
from src.handlers.balance import balance_handler
from src.handlers.finance import financial_handler
print("Todos os handlers importaram sem erro")

print()
print("OK!")
