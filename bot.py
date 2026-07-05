import os
import requests
from telegram.ext import ApplicationBuilder, CommandHandler

TOKEN=os.environ["TOKEN"]

def get_price(symbol):
    url = "https://api.binance.com/api/v3/ticker/price?symbol=" + symbol + "USDT"
    try:
        r = requests.get(url, timeout=10)
        return r.json().get("price")
    except Exception as e:
        return "ERR: " + str(e)

async def start(update, context):
    btc = get_price("BTC")
    eth = get_price("ETH")
    msg = "BTC: $" + format(float(btc), ",.2f") + "\nETH: $" + format(float(eth), ",.2f")
    await update.message.reply_text(msg)

async def ping_cmd(update, context):
    await update.message.reply_text("pong - bot is alive!")

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: TOKEN not set!")
        exit(1)
    print("Token length: " + str(len(TOKEN)))
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping_cmd))
    print("Bot is running...")
    app.run_polling()
