"""Financial handler - admin dashboard com lucro real pós-taxas MP."""
from telegram import Update
from telegram.ext import ContextTypes
from src.services.database import get_financial_summary


async def financial_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /finance — mostra o resumo financeiro real do bot."""
    user_id = update.effective_user.id

    # Só o dono pode ver (telegram ID do admin)
    ADMIN_IDS = [int(x) for x in context.bot_data.get("admin_ids", "").split(",") if x]
    # Se não configurou admin_ids no bot_data, usa env var
    if not ADMIN_IDS:
        import os
        ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x]

    if ADMIN_IDS and user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Comando restrito.")
        return

    summary = get_financial_summary()

    v = summary["vendas"]
    g = summary["geracoes"]

    # Cálculo das margens
    margem_pct = 0
    if v["bruto"] > 0:
        margem_pct = round((v["liquido"] - g["custo_real"]) / v["bruto"] * 100, 1)

    text = (
        "📊 *Financeiro - Bilion Luxure*\n\n"
        "*Vendas*\n"
        f"• Total: {v['total']} vendas\n"
        f"• Bruto: R$ {v['bruto']:.2f}\n"
        f"• Taxas MP: -R$ {v['taxas_mp']:.2f}\n"
        f"• Líquido: R$ {v['liquido']:.2f}\n\n"
        "*Gerações*\n"
        f"• Total: {g['total']} gerações\n"
        f"• Coins gastos: {g['coins_gastos']}\n"
        f"• Custo real: -R$ {g['custo_real']:.2f}\n\n"
        f"*Resultado Final*\n"
        f"💰 Lucro estimado: R$ {summary['lucro_estimado']:.2f}\n"
        f"📈 Margem: {margem_pct}%\n"
        f"🪙 Coins emitidos: {summary['coins_emitidas']}"
    )

    await update.message.reply_text(text, parse_mode="Markdown")
