import logging
import os
import base64
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from app.database.connection import SessionLocal
from app.models.cliente import Cliente
from app.models.mensalidade import Mensalidade
from datetime import date

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_TELEGRAM_ID"))
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================================
# COMANDO /start
# ================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Olá! Bem-vindo ao *Atleta em Foco*!\n\n"
        "Para registrar seu pagamento, basta enviar a foto do comprovante aqui.\n\n"
        "📌 Comandos disponíveis:\n"
        "/status — Ver status da sua mensalidade\n"
        "/ajuda — Ver instruções",
        parse_mode='Markdown'
    )

# ================================
# COMANDO /status
# ================================
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    db = SessionLocal()
    try:
        cliente = db.query(Cliente).filter(Cliente.telegram_id == telegram_id).first()
        if not cliente:
            await update.message.reply_text(
                "⚠️ Você ainda não está cadastrado no sistema.\n"
                "Por favor, entre em contato com o administrador."
            )
            return

        mensalidade = db.query(Mensalidade).filter(
            Mensalidade.cliente_id == cliente.id,
            Mensalidade.status != 'pago'
        ).order_by(Mensalidade.data_vencimento.desc()).first()

        if not mensalidade:
            await update.message.reply_text("✅ Você não tem mensalidades pendentes!")
            return

        emoji = "⏳" if mensalidade.status == "pendente" else "🔴"
        await update.message.reply_text(
            f"{emoji} *Status da sua mensalidade:*\n\n"
            f"📅 Vencimento: {mensalidade.data_vencimento}\n"
            f"💰 Valor: R${mensalidade.valor:.0f}\n"
            f"📌 Status: {mensalidade.status.upper()}\n\n"
            "Para pagar, envie a foto do comprovante aqui!",
            parse_mode='Markdown'
        )
    finally:
        db.close()

# ================================
# RECEBER COMPROVANTE (FOTO)
# ================================
async def receber_comprovante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    db = SessionLocal()

    try:
        cliente = db.query(Cliente).filter(Cliente.telegram_id == telegram_id).first()
        if not cliente:
            await update.message.reply_text(
                "⚠️ Você não está cadastrado no sistema.\n"
                "Entre em contato com o administrador."
            )
            return

        mensalidade = db.query(Mensalidade).filter(
            Mensalidade.cliente_id == cliente.id,
            Mensalidade.status != 'pago'
        ).order_by(Mensalidade.data_vencimento.desc()).first()

        if not mensalidade:
            await update.message.reply_text("✅ Você não tem mensalidades pendentes!")
            return

        await update.message.reply_text(
            "📨 Comprovante recebido! Aguarde a confirmação do administrador."
        )

        photo = update.message.photo[-1]
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo.file_id,
            caption=(
                f"📋 *Comprovante recebido!*\n\n"
                f"👤 Cliente: {cliente.nome}\n"
                f"📅 Vencimento: {mensalidade.data_vencimento}\n"
                f"💰 Valor: R${mensalidade.valor:.0f}\n"
                f"🔑 ID Mensalidade: {mensalidade.id}\n\n"
                f"Para aprovar: `/aprovar {mensalidade.id}`\n"
                f"Para rejeitar: `/rejeitar {mensalidade.id}`"
            ),
            parse_mode='Markdown'
        )
    finally:
        db.close()

# ================================
# VALIDAÇÃO COM CLAUDE AI
# ================================
async def validar_comprovante_ia(image_base64: str, valor_esperado: float) -> bool:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 256,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/jpeg",
                                        "data": image_base64
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": f"Esta imagem é um comprovante de pagamento válido no valor de R${valor_esperado:.0f}? Responda apenas SIM ou NAO."
                                }
                            ]
                        }
                    ]
                },
                timeout=30.0
            )
            result = response.json()
            resposta = result['content'][0]['text'].strip().upper()
            return 'SIM' in resposta
    except Exception as e:
        logger.error(f"Erro na validação IA: {e}")
        return False

# ================================
# COMANDO /aprovar (admin)
# ================================
async def aprovar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Comando /aprovar recebido de {update.effective_user.id}, ADMIN_ID={ADMIN_ID}")
    if not context.args:
        await update.message.reply_text("Use: /aprovar <id_mensalidade>")
        return

    mensalidade_id = int(context.args[0])
    db = SessionLocal()
    try:
        mensalidade = db.query(Mensalidade).filter(Mensalidade.id == mensalidade_id).first()
        if not mensalidade:
            await update.message.reply_text("❌ Mensalidade não encontrada.")
            return

        cliente = db.query(Cliente).filter(Cliente.id == mensalidade.cliente_id).first()
        mensalidade.status = 'pago'
        mensalidade.validado_por = 'admin'
        mensalidade.data_pagamento = date.today().strftime("%d/%m/%Y")
        db.commit()

        await update.message.reply_text(
            f"✅ Mensalidade #{mensalidade_id} de {cliente.nome} aprovada!"
        )

        if cliente.telegram_id:
            await context.bot.send_message(
                chat_id=int(cliente.telegram_id),
                text=(
                    f"✅ *Pagamento confirmado!*\n\n"
                    f"Olá {cliente.nome}!\n"
                    f"Sua mensalidade de R${mensalidade.valor:.0f} foi confirmada.\n\n"
                    f"Obrigado! 💪"
                ),
                parse_mode='Markdown'
            )
    finally:
        db.close()

# ================================
# COMANDO /rejeitar (admin)
# ================================
async def rejeitar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Use: /rejeitar <id_mensalidade>")
        return

    mensalidade_id = int(context.args[0])
    db = SessionLocal()
    try:
        mensalidade = db.query(Mensalidade).filter(Mensalidade.id == mensalidade_id).first()
        if not mensalidade:
            await update.message.reply_text("❌ Mensalidade não encontrada.")
            return

        cliente = db.query(Cliente).filter(Cliente.id == mensalidade.cliente_id).first()
        await update.message.reply_text(
            f"❌ Mensalidade #{mensalidade_id} de {cliente.nome} rejeitada."
        )

        if cliente.telegram_id:
            await context.bot.send_message(
                chat_id=int(cliente.telegram_id),
                text=(
                    f"❌ *Comprovante não aprovado.*\n\n"
                    f"Olá {cliente.nome}!\n"
                    f"Seu comprovante não foi aprovado.\n"
                    f"Por favor, envie novamente ou entre em contato."
                ),
                parse_mode='Markdown'
            )
    finally:
        db.close()

# ================================
# COMANDO /ajuda
# ================================
async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Como usar o bot:*\n\n"
        "1. Tire uma foto clara do comprovante\n"
        "2. Envie a foto aqui no chat\n"
        "3. Aguarde a confirmação automática\n\n"
        "📌 Comandos:\n"
        "/start — Iniciar o bot\n"
        "/status — Ver sua mensalidade\n"
        "/ajuda — Ver estas instruções",
        parse_mode='Markdown'
    )

# ================================
# INICIAR O BOT
# ================================
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("ajuda", ajuda))
    app.add_handler(CommandHandler("aprovar", aprovar))
    app.add_handler(CommandHandler("rejeitar", rejeitar))
    app.add_handler(MessageHandler(filters.PHOTO, receber_comprovante))
    print("🤖 Bot iniciado! Pressione Ctrl+C para parar.")
    app.run_polling()

if __name__ == "__main__":
    main()