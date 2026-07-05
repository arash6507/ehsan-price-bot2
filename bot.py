import logging
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


TOKEN=8367114377:AAGd_vEuxGLFhgvJiTrBvB7lzwmNd6sJX-Y 


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


# ===============================================
# 🟢 توابع کریپتو
# ===============================================

def get_crypto_price(symbol: str) -> str:
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if "price" in data:
            return data["price"]
        return "NOT_FOUND"
    except Exception as e:
        return f"ERROR: {e}"


def get_crypto_24h(symbol: str) -> dict:
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
    try:
        r = requests.get(url, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


# ===============================================
# 🟡 توابع طلا (tgju.org)
# ===============================================

def get_gold_prices() -> dict:
    pages = {
        "طلای ۱۸ عیار": "https://www.tgju.org/profile/geram18",
        "سکه امامی":   "https://www.tgju.org/profile/sekeb",
        "دلار":        "https://www.tgju.org/profile/price_dollar_rl",
        "یورو":        "https://www.tgju.org/profile/price_eur",
        "مثقال طلا":   "https://www.tgju.org/profile/mesghal",
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36"
    }

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
                    result[name] = price + " ریال"
                    continue

            heading = soup.find("h3")
            if heading:
                result[name] = heading.get_text(strip=True)

        except Exception as e:
            result[name] = f"خطا: {e}"

    return result


# ===============================================
# 📋 دستورهای ربات
# ===============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام احسان! 👋\n"
        "ربات قیمت‌یاب v3 فعاله ✅\n\n"
        "برای راهنما بزن: /help"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 *دستورهای موجود:*\n\n"
        "/start       -  شروع\n"
        "/help        -  راهنما\n"
        "/price BTC   -  قیمت بیت‌کوین\n"
        "/gold        -  طلا و سکه ایران 🇮🇷\n"
        "/auto N      -  گزارش خودکار هر N دقیقه\n"
        "/autostop    -  خاموش کردن گزارش خودکار\n\n"
        "💡 هر نمادی که توی Binance هست رو میشه گرفت",
        parse_mode="Markdown"
    )


async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ لطفاً نماد رو بگو.\nمثال: /price BTC")
        return

    symbol = context.args[0].upper() + "USDT"

    price_val = get_crypto_price(symbol)
    if price_val == "NOT_FOUND" or price_val.startswith("ERROR"):
        await update.message.reply_text(f"⚠️ نماد `{symbol}` پیدا نشد.", parse_mode="Markdown")
        return

    info = get_crypto_24h(symbol)
    change_pct = float(info.get("priceChangePercent", 0))
    high_24h = float(info.get("highPrice", 0))
    low_24h = float(info.get("lowPrice", 0))
    volume_24h = float(info.get("quoteVolume", 0))

    if change_pct > 0:
        trend_emoji = "📈"
        trend_text = "سبز"
    else:
        trend_emoji = "📉"
        trend_text = "قرمز"

    msg = (
        f"{trend_emoji} *{context.args[0].upper()} / USDT*\n\n"
        f"💰 قیمت: `${float(price_val):,.2f}`\n"
        f"📊 تغییر ۲۴ ساعت: `{change_pct:+.2f}%` ({trend_text})\n"
        f"⬆️ بالاترین ۲۴ ساعت: `${high_24h:,.2f}`\n"
        f"⬇️ پایین‌ترین ۲۴ ساعت: `${low_24h:,.2f}`\n"
        f"💵 حجم معاملات: `${volume_24h:,.0f}`"
    )

    await update.message.reply_text(msg, parse_mode="Markdown")


async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ در حال گرفتن قیمت‌ها از tgju.org...")

    data = get_gold_prices()

    if not data:
        await msg.edit_text("⚠️ هیچ قیمتی پیدا نشد.")
        return

    text = "*🟡 قیمت‌های لحظه‌ای بازار ایران*\n\n"
    for name, value in data.items():
        if "خطا" in value:
            text += f"⚠️ *{name}*: {value}\n"
        else:
            text += f"🔸 *{name}*: `{value}`\n"

    text += "\n_منبع: tgju.org | به‌روز: لحظه‌ای_"

    await msg.edit_text(text, parse_mode="Markdown")


# ===============================================
# ⏰ گزارش خودکار
# ===============================================

async def auto_report(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id

    crypto_text = ""
    symbols = [("BTC", "بیت‌کوین"), ("ETH", "اتریوم")]
    for sym, fa_name in symbols:
        price_val = get_crypto_price(sym + "USDT")
        info = get_crypto_24h(sym + "USDT")
        if isinstance(info, dict) and "priceChangePercent" in info:
            change = float(info["priceChangePercent"])
            emoji = "📈" if change > 0 else "📉"
            sym_emoji = "🟢" if change > 0 else "🔴"
            crypto_text += (
                f"{sym_emoji} *{fa_name}*: `${float(price_val):,.2f}`  "
                f"{emoji} `{change:+.2f}%`\n"
            )

    gold_data = get_gold_prices()
    gold_text = ""
    for name, value in gold_data.items():
        if "خطا" not in value:
            gold_text += f"🔸 *{name}*: `{value}`\n"

    now = datetime.now().strftime("%H:%M")

    msg = (
        f"🕐 *گزارش خودکار — ساعت {now}*\n\n"
        f"*کریپتو:*\n{crypto_text}\n"
        f"*بازار ایران:*\n{gold_text}\n"
        f"_ربات قیمت‌یاب احسان | tgju + Binance_"
    )

    await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")


async def auto_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❌ استفاده: `/auto 5` یعنی هر ۵ دقیقه گزارش بده.",
            parse_mode="Markdown"
        )
        return

    try:
        minutes = int(context.args[0])
        if minutes < 1 or minutes > 1440:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "⚠️ عدد باید بین ۱ تا ۱۴۴۰ باشد (۱ دقیقه تا ۲۴ ساعت)."
        )
        return

    chat_id = str(update.effective_chat.id)
    current_jobs = context.job_queue.get_jobs_by_name(chat_id)
    for job in current_jobs:
        job.schedule_removal()

    context.job_queue.run_repeating(
        auto_report,
        interval=minutes * 60,
        first=10,
        chat_id=update.effective_chat.id,
        name=chat_id,
    )

    await update.message.reply_text(
        f"⏰ گزارش خودکار هر *{minutes} دقیقه* فعال شد! 🎉\n"
        f"برای خاموش کردن بزن: /autostop",
        parse_mode="Markdown"
    )


async def autostop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    current_jobs = context.job_queue.get_jobs_by_name(chat_id)
    if not current_jobs:
        await update.message.reply_text("ℹ️ الان هیچ گزارش خودکاری فعال نیست.")
        return

    for job in current_jobs:
        job.schedule_removal()

    await update.message.reply_text("🛑 گزارش خودکار خاموش شد.")


# ===============================================
# 🚀 اجرای ربات
# ===============================================

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("gold", gold))
    app.add_handler(CommandHandler("auto", auto_cmd))
    app.add_handler(CommandHandler("autostop", autostop_cmd))

    print("✅ ربات روشن شد. منتظر پیام‌ها می‌مونه...")
    app.run_polling()
