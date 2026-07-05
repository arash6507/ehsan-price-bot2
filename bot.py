import os
import logging
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN=os.environ["TOKEN2"]

logging.basicConfig(level=logging.INFO)


def get_crypto_price(symbol):
    url = "https://api.binance.com/api/v3/ticker/price?symbol=" + symbol
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if "price" in data:
            return data["price"]
        return "NOT_FOUND"
    except Exception as e:
        return "ERROR: " + str(e)


def get_crypto_24h(symbol):
    url = "https://api.binance.com/api/v3/ticker/24hr?symbol=" + symbol
    try:
        return requests.get(url, timeout=10).json()
    except Exception as e:
        return {"error": str(e)}


def get_gold_prices():
    pages = {
        "geram18": "https://www.tgju.org/profile/geram18",
        "sekeb":   "https://www.tgju.org/profile/sekeb",
        "dollar":  "https://www.tgju.org/profile/price_dollar_rl",
        "euro":    "https://www.tgju.org/profile/price_eur",
        "mesghal": "https://www.tgju.org/profile/mesghal",
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    result = {}
    for name, url in pages.items():
        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            target_row = None
            for row in soup.select("tr"):
                first_cell = row.find("td")
                if first_cell and "نرخ فعلی" in first_cell.get_text():
                    target_row = row
                    break
            if target_row:
                cells = target_row.find_all("td")
                if len(cells) >= 2:
                    price = cells[1].get_text(strip=True)
                    result[name] = price + " IRR"
                    continue
        except Exception as e:
            result[name] = "ERR"
    return result


async def start(update, context):
    await update.message.reply_text("Bot active! Use /help")


async def help_cmd(update, context):
    await update.message.reply_text("/start, /price BTC, /gold, /auto 5, /autostop")


async def price_cmd(update, context):
    if not context.args:
        await update.message.reply_text("Use: /price BTC")
        return
    symbol = context.args[0].upper() + "USDT"
    try:
        price_val = get_crypto_price(symbol)
        if price_val == "NOT_FOUND" or str(price_val).startswith("ERROR"):
            await update.message.reply_text("Not found: " + symbol)
            return

        info = get_crypto_24h(symbol)
        change = float(info.get("priceChangePercent", 0))
        arrow = "UP" if change > 0 else "DOWN"
        msg = symbol + " | $" + format(float(price_val), ",.2f") + " | 24h: " + format(change, "+.2f") + "% (" + arrow + ")"
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text("Error: " + str(e))


async def gold_cmd(update, context):
    msg = await update.message.reply_text("Fetching gold...")
    data = get_gold_prices()
    text = "Gold Prices IRR:\n"
    for name, value in data.items():
        text += name + ": " + value + "\n"
    await msg.edit_text(text)


async def auto_report(context):
    chat_id = context.job.chat_id
    btc = get_crypto_price("BTCUSDT")
    btc_info = get_crypto_24h("BTCUSDT")
    btc_change = float(btc_info.get("priceChangePercent", 0))
    eth = get_crypto_price("ETHUSDT")
    eth_info = get_crypto_24h("ETHUSDT")
    eth_change = float(eth_info.get("priceChangePercent", 0))
    now = datetime.now().strftime("%H:%M")
    text = "Auto " + now + "\n"
    text += "BTC: $" + str(btc) + " (" + format(btc_change, "+.2f") + "%)\n"
    text += "ETH: $" + str(eth) + " (" + format(eth_change, "+.2f") + "%)\n"
    await context.bot.send_message(chat_id=chat_id, text=text)


async def auto_cmd(update, context):
    if not context.args:
        await update.message.reply_text("Use: /auto 5")
        return
    try:
        minutes = int(context.args[0])
        if minutes < 1 or minutes > 1440:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Number 1-1440")
        return
    chat_id = str(update.effective_chat.id)
    for job in context.job_queue.get_jobs_by_name(chat_id):
        job.schedule_removal()
    context.job_queue.run_repeating(
        auto_report,
        interval=minutes * 60,
        first=10,
        chat_id=update.effective_chat.id,
        name=chat_id,
    )
    await update.message.reply_text("Auto report every " + str(minutes) + " min ON.")


async def autostop_cmd(update, context):
    chat_id = str(update.effective_chat.id)
    jobs = context.job_queue.get_jobs_by_name(chat_id)
    if not jobs:
        await update.message.reply_text("No active auto report.")
        return
    for job in jobs:
        job.schedule_removal()
    await update.message.reply_text("Auto report OFF.")


if __name__ == "__main__":
    if not TOKEN:
        print("TOKEN not set!")
        exit(1)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("price", price_cmd))
    app.add_handler(CommandHandler("gold", gold_cmd))
    app.add_handler(CommandHandler("auto", auto_cmd))
    app.add_handler(CommandHandler("autostop", autostop_cmd))
    print("Bot running...")
    app.run_polling()
