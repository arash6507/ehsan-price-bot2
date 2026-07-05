import os
import requests
from telegram.ext import ApplicationBuilder, CommandHandler

TOKEN=os.get...EN")

def get_price(symbol):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
    try:
        r = requests.get(url, timeout=10)
        return r.json().get("price")
    except Exception as e:
        return f"ERR: {e}"

async def start(update, context):
    btc = get_price("BTC")
    eth = get_price("ETH")
    await update.message.reply_text(f"BTC: ${float(btc):,.2f}\nETH: ${float(eth):,.2f}")

async def ping_cmd(update, context):
    await update.message.reply_text("pong - bot is alive!")

if __name__ == "__main__":
    print(f"Token loaded: {len(TOKEN) if TOKEN else 0} chars")
    if not TOKEN:
        print("ERROR: TOKEN env variable not set!")
        exit(1)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping_cmd))
    print("Bot is running...")
    app.run_polling()
