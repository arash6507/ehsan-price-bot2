import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN=os.environ["TOKEN"]


def get_price(symbol):
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=" + symbol + "USDT"
        r = requests.get(url, timeout=10)
        return r.json().get("price")
    except Exception as e:
        return "ERR:" + str(e)


def get_24h(symbol):
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr?symbol=" + symbol + "USDT"
        r = requests.get(url, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    btc = get_price("BTC")
    eth = get_price("ETH")
    msg = "BTC: " + str(btc) + "\nETH: " + str(eth)
    await update.message.reply_text(msg)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start, /help, /price BTC")


async def price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Use: /price BTC")
        return

    sym = context.args[0].upper()
    symbol = sym + "USDT"

    p = get_price(sym)
    info = get_24h(sym)

    if "code" in info or "error" in info:
        await update.message.reply_text("Error for " + symbol)
        return

    try:
        change = float(info.get("priceChangePercent", 0))
        high = float(info.get("highPrice", 0))
        low = float(info.get("lowPrice", 0))
        emoji = "UP" if change > 0 else "DOWN"

        msg = (
            sym + "/USDT\n"
            "Price: $" + format(float(p), ",.2f") + "\n"
            "24h: " + format(change, "+.2f") + "% (" + emoji + ")\n"
            "High: $" + format(high, ",.2f") + "\n"
            "Low: $" + format(low, ",.2f")
        )
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text("Parse error: " + str(e))


if __name__ == "__main__":
    if not TOKEN:
        print("TOKEN not set!")
        exit(1)
    print("Token OK, len=" + str(len(TOKEN)))

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("price", price_cmd))

    print("Bot running...")
    app.run_polling()
