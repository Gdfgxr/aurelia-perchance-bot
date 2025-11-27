import asyncio
import os
import aiohttp
import json
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configuracao
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Historico de conversas por usuario
conversations = {}

# Configuracao do personagem Aurelia
CHARACTER_CONFIG = {
    "name": "Aurelia",
    "personality": "Voce e Aurelia, uma assistente virtual brasileira carismatica e inteligente. Voce sempre responde em portugues brasileiro de forma natural, acolhedora e bem-humorada. Voce e prestativa, curiosa e gosta de ajudar as pessoas com qualquer assunto.",
    "language": "pt-BR"
}

async def call_perchance_ai(prompt: str) -> str:
    """Chama a API do Perchance AI para gerar resposta"""
    try:
        url = "https://api.perchance.org/ai/text"
        
        payload = {
            "prompt": prompt,
            "type": "chat"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=30) as response:
                if response.status == 200:
                    result = await response.text()
                    return result.strip()
                else:
                    return None
    except Exception as e:
        print(f"Erro na API Perchance: {e}")
        return None

async def get_ai_response(user_id: int, user_message: str) -> str:
    """Gera resposta usando IA"""
    try:
        # Recupera ou inicia historico
        if user_id not in conversations:
            conversations[user_id] = []
        
        # Adiciona mensagem ao historico
        conversations[user_id].append({"role": "user", "content": user_message})
        
        # Monta contexto
        history = conversations[user_id][-10:]  # Ultimas 10 mensagens
        context = "\n".join([f"{m['role'].title()}: {m['content']}" for m in history])
        
        full_prompt = f"""{CHARACTER_CONFIG['personality']}

Historico da conversa:
{context}

Responda a ultima mensagem do usuario como Aurelia, em portugues brasileiro:"""
        
        # Tenta API do Perchance
        response = await call_perchance_ai(full_prompt)
        
        if not response:
            # Fallback: resposta padrao
            response = "Oi! Desculpa, estou com um probleminha tecnico agora. Pode tentar de novo em alguns segundos? 😊"
        
        # Salva resposta
        conversations[user_id].append({"role": "assistant", "content": response})
        
        # Limita historico
        if len(conversations[user_id]) > 20:
            conversations[user_id] = conversations[user_id][-20:]
        
        return response
    
    except Exception as e:
        print(f"Erro: {e}")
        return "Ops! Algo deu errado. Tenta de novo? 😅"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    user_id = update.effective_user.id
    conversations[user_id] = []
    
    welcome = """🌟 **Ola! Eu sou a Aurelia!** 🌟

Sou sua assistente virtual brasileira, pronta pra conversar!

📝 **Comandos:**
• Manda qualquer mensagem que eu respondo!
• /reset - Comeca conversa nova
• /help - Ver comandos

Bora conversar? 💬"""
    
    await update.message.reply_text(welcome, parse_mode='Markdown')

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /reset"""
    user_id = update.effective_user.id
    conversations[user_id] = []
    await update.message.reply_text("🔄 Conversa reiniciada! Vamos comecar de novo? 😊")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help"""
    help_text = """📚 **Comandos:**

/start - Inicia o bot
/reset - Limpa historico
/help - Mostra isso

💬 Pra conversar, so mandar mensagem!"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa mensagens"""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    response = await get_ai_response(user_id, user_message)
    await update.message.reply_text(response)

def main():
    print("🚀 Iniciando Aurelia Bot...")
    
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN nao configurado!")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Aurelia esta online!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
