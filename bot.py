
import telebot
import json
from datetime import datetime, timedelta

# بارگذاری تنظیمات
with open('config.json', 'r') as f:
    config = json.load(f)

bot = telebot.TeleBot(config["BOT_TOKEN"])
admin_id = config["ADMIN_ID"]
wallet_address = config["WALLET_ADDRESS"]

# فایل کاربران
try:
    with open('users.json', 'r') as f:
        users = json.load(f)
except:
    users = {}

# پلن‌ها
plans = {
    "mini": {"price": 39, "daily_profit": 3},
    "average": {"price": 59, "daily_profit": 7},
    "large": {"price": 100, "daily_profit": 14}
}

languages = {
    "fa": {
        "welcome": "👋 خوش آمدی به ربات سرمایه‌گذاری Crypto Flow",
        "menu": ["📥 خرید سهام", "💵 دریافت سود", "📤 برداشت", "💼 وضعیت من", "👥 دعوت دوستان", "🌐 تغییر زبان"],
        "choose_plan": "لطفاً پلن مورد نظر خود را انتخاب کن:",
        "send_txid": "لطفاً TxID واریز به آدرس زیر را ارسال کن:"
        USDT (TRC-20):"TKBvzFm5byVVr7eG1z8NAC6HvYsV4iXfGe"
        
        "confirmed": "✅ تراکنش شما برای پلن {} تأیید شد.",
        "already_today": "شما امروز سودتان را دریافت کرده‌اید. فردا دوباره تلاش کنید.",
        "profit_added": "✅ {} تتر به سود شما اضافه شد.",
        "choose_language": "🌐 لطفاً زبان خود را انتخاب کنید:",
        "status": "💼 موجودی: {} تتر
📈 سود کل: {} تتر
🗓 پلن‌ها: {}",
    },
    "en": {
        "welcome": "👋 Welcome to Crypto Flow Investment Bot",
        "menu": ["📥 Buy Stock", "💵 Get Profit", "📤 Withdraw", "💼 My Status", "👥 Invite Friends", "🌐 Change Language"],
        "choose_plan": "Please choose your investment plan:",
        "send_txid": "Please send your TxID for payment to:"

USDT(TRC20): {}",
        "confirmed": "✅ Your transaction for {} plan has been confirmed.",
        "already_today": "You already received today's profit. Come back tomorrow.",
        "profit_added": "✅ {} USDT profit added to your balance.",
        "choose_language": "🌐 Please choose your language:",
        "status": "💼 Balance: {} USDT
📈 Total Profit: {} USDT
🗓 Plans: {}",
    }
}

# ذخیره کاربران
def save_users():
    with open('users.json', 'w') as f:
        json.dump(users, f)

# دریافت زبان کاربر
def get_lang(user_id):
    return users.get(str(user_id), {}).get("lang", "fa")

# شروع
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        users[user_id] = {
            "lang": "fa",
            "plans": [],
            "balance": 0,
            "total_profit": 0,
            "last_profit_date": ""
        }
        save_users()
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    lang = get_lang(user_id)
    for btn in languages[lang]["menu"]:
        markup.add(btn)
    bot.send_message(message.chat.id, languages[lang]["welcome"], reply_markup=markup)

# انتخاب زبان
@bot.message_handler(func=lambda msg: msg.text == "🌐 تغییر زبان" or msg.text == "🌐 Change Language")
def change_lang(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🇮🇷 فارسی", "🇺🇸 English")
    bot.send_message(message.chat.id, "🌐 لطفاً زبان را انتخاب کنید:", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text in ["🇮🇷 فارسی", "🇺🇸 English"])
def set_lang(message):
    user_id = str(message.from_user.id)
    users[user_id]["lang"] = "fa" if "فارسی" in message.text else "en"
    save_users()
    send_welcome(message)

# خرید پلن
@bot.message_handler(func=lambda msg: msg.text in ["📥 خرید سهام", "📥 Buy Stock"])
def buy_stock(message):
    user_id = str(message.from_user.id)
    lang = get_lang(user_id)
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("Mini - 39$", callback_data="buy_mini"),
        telebot.types.InlineKeyboardButton("Average - 59$", callback_data="buy_average"),
        telebot.types.InlineKeyboardButton("Large - 100$", callback_data="buy_large"),
    )
    bot.send_message(message.chat.id, languages[lang]["choose_plan"], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def handle_buy(call):
    plan_key = call.data.replace("buy_", "")
    user_id = str(call.from_user.id)
    lang = get_lang(user_id)
    users[user_id]["pending_plan"] = plan_key
    save_users()
    bot.send_message(call.message.chat.id, languages[lang]["send_txid"].format(wallet_address))

# دریافت TxID
@bot.message_handler(func=lambda msg: msg.text.startswith("TXID"))
def receive_txid(message):
    user_id = str(message.from_user.id)
    plan = users[user_id].get("pending_plan")
    if not plan:
        return
    bot.send_message(admin_id, f"📥 درخواست خرید پلن جدید:

کاربر: {message.from_user.first_name}
پلن: {plan}
TxID: {message.text}")
    bot.send_message(message.chat.id, "⏳ تراکنش شما برای بررسی ارسال شد. پس از تایید فعال خواهد شد.")

# دریافت سود روزانه
@bot.message_handler(func=lambda msg: msg.text in ["💵 دریافت سود", "💵 Get Profit"])
def get_profit(message):
    user_id = str(message.from_user.id)
    user = users.get(user_id)
    lang = get_lang(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    if user["last_profit_date"] == today:
        bot.send_message(message.chat.id, languages[lang]["already_today"])
        return
    total_today_profit = sum([plans[p]["daily_profit"] for p in user["plans"]])
    user["balance"] += total_today_profit
    user["total_profit"] += total_today_profit
    user["last_profit_date"] = today
    save_users()
    bot.send_message(message.chat.id, languages[lang]["profit_added"].format(total_today_profit))

# وضعیت
@bot.message_handler(func=lambda msg: msg.text in ["💼 وضعیت من", "💼 My Status"])
def status(message):
    user_id = str(message.from_user.id)
    user = users.get(user_id)
    lang = get_lang(user_id)
    plans_list = ", ".join(user["plans"]) if user["plans"] else "ندارد"
    bot.send_message(message.chat.id, languages[lang]["status"].format(user["balance"], user["total_profit"], plans_list))

bot.infinity_polling()
