import os
import telebot
import json
from datetime import datetime

# تنظیمات از متغیرهای محیطی
BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')
WALLET_ADDRESS = os.environ.get('WALLET_ADDRESS')

if not all([BOT_TOKEN, ADMIN_ID, WALLET_ADDRESS]):
    raise ValueError("خطا: متغیرهای محیطی تنظیم نشده‌اند!")

bot = telebot.TeleBot(BOT_TOKEN)

# دیتابیس کاربران
try:
    with open('users.json', 'r') as f:
        users = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    users = {}

# پلن‌های سرمایه‌گذاری
plans = {
    "mini": {"price": 39, "daily_profit": 3, "name": {"fa": "مینی", "en": "Mini"}},
    "average": {"price": 59, "daily_profit": 7, "name": {"fa": "متوسط", "en": "Average"}},
    "large": {"price": 100, "daily_profit": 14, "name": {"fa": "بزرگ", "en": "Large"}}
}

# متن‌های چندزبانه
languages = {
    "fa": {
        "welcome": "👋 خوش آمدی به ربات سرمایه‌گذاری Crypto Flow",
        "menu": ["📥 خرید سهام", "💵 دریافت سود", "📤 برداشت", "💼 وضعیت من", "👥 دعوت دوستان", "🌐 تغییر زبان"],
        "choose_plan": "لطفاً پلن مورد نظر خود را انتخاب کن:",
        "send_txid": "لطفاً TxID واریز به آدرس زیر را ارسال کن:\n\nUSDT (TRC-20): {}\n\nمبلغ: {} تتر",
        "confirmed": "✅ تراکنش شما برای پلن {} تأیید شد.",
        "already_today": "شما امروز سودتان را دریافت کرده‌اید. فردا دوباره تلاش کنید.",
        "profit_added": "✅ {} تتر به سود شما اضافه شد.",
        "choose_language": "🌐 لطفاً زبان خود را انتخاب کنید:",
        "status": "💼 موجودی: {} تتر\n📈 سود کل: {} تتر\n🗓 پلن‌ها: {}",
        "no_plans": "شما هیچ پلنی ندارید.",
        "invalid_txid": "⚠️ فرمت TxID نامعتبر است. لطفاً دوباره تلاش کنید.",
        "pending_approval": "⏳ تراکنش شما برای بررسی ارسال شد. پس از تأیید فعال خواهد شد.",
        "admin_new_request": "📥 درخواست خرید پلن جدید:\n\n👤 کاربر: {}\n🆔 آیدی: {}\n📋 پلن: {}\n💰 مبلغ: {} تتر\n🔗 TxID: {}"
    },
    "en": {
        "welcome": "👋 Welcome to Crypto Flow Investment Bot",
        "menu": ["📥 Buy Stock", "💵 Get Profit", "📤 Withdraw", "💼 My Status", "👥 Invite Friends", "🌐 Change Language"],
        "choose_plan": "Please choose your investment plan:",
        "send_txid": "Please send your TxID for payment to:\n\nUSDT (TRC20): {}\n\nAmount: {} USDT",
        "confirmed": "✅ Your transaction for {} plan has been confirmed.",
        "already_today": "You already received today's profit. Come back tomorrow.",
        "profit_added": "✅ {} USDT profit added to your balance.",
        "choose_language": "🌐 Please choose your language:",
        "status": "💼 Balance: {} USDT\n📈 Total Profit: {} USDT\n🗓 Plans: {}",
        "no_plans": "You don't have any plans.",
        "invalid_txid": "⚠️ Invalid TxID format. Please try again.",
        "pending_approval": "⏳ Your transaction has been sent for review. It will be activated after approval.",
        "admin_new_request": "📥 New purchase request:\n\n👤 User: {}\n🆔 ID: {}\n📋 Plan: {}\n💰 Amount: {} USDT\n🔗 TxID: {}"
    }
}

def save_users():
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=4)

def get_lang(user_id):
    return users.get(str(user_id), {}).get("lang", "fa")

def get_user_plans_names(user_id, lang):
    user_plans = users.get(str(user_id), {}).get("plans", [])
    return ", ".join([plans[plan]["name"][lang] for plan in user_plans]) if user_plans else languages[lang]["no_plans"]

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        users[user_id] = {
            "lang": "fa",
            "plans": [],
            "balance": 0,
            "total_profit": 0,
            "last_profit_date": "",
            "pending_plan": None
        }
        save_users()
    
    lang = get_lang(user_id)
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for btn in languages[lang]["menu"]:
        markup.add(btn)
    bot.send_message(message.chat.id, languages[lang]["welcome"], reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text in ["🌐 تغییر زبان", "🌐 Change Language"])
def change_lang(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🇮🇷 فارسی", "🇺🇸 English")
    lang = get_lang(str(message.from_user.id))
    bot.send_message(message.chat.id, languages[lang]["choose_language"], reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text in ["🇮🇷 فارسی", "🇺🇸 English"])
def set_lang(message):
    user_id = str(message.from_user.id)
    users[user_id]["lang"] = "fa" if "فارسی" in message.text else "en"
    save_users()
    send_welcome(message)

@bot.message_handler(func=lambda msg: msg.text in ["📥 خرید سهام", "📥 Buy Stock"])
def buy_stock(message):
    user_id = str(message.from_user.id)
    lang = get_lang(user_id)
    markup = telebot.types.InlineKeyboardMarkup()
    for plan_key, plan_data in plans.items():
        markup.add(telebot.types.InlineKeyboardButton(
            f"{plan_data['name'][lang]} - {plan_data['price']}$",
            callback_data=f"buy_{plan_key}"
        ))
    bot.send_message(message.chat.id, languages[lang]["choose_plan"], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def handle_buy(call):
    plan_key = call.data.replace("buy_", "")
    user_id = str(call.from_user.id)
    lang = get_lang(user_id)
    users[user_id]["pending_plan"] = plan_key
    save_users()
    bot.send_message(
        call.message.chat.id,
        languages[lang]["send_txid"].format(WALLET_ADDRESS, plans[plan_key]["price"])
    )

@bot.message_handler(func=lambda msg: msg.text.startswith("TXID_"))
def receive_txid(message):
    user_id = str(message.from_user.id)
    lang = get_lang(user_id)
    
    if user_id not in users or "pending_plan" not in users[user_id]:
        return
    
    if len(message.text.split("_")[1]) != 64:
        bot.send_message(message.chat.id, languages[lang]["invalid_txid"])
        return
    
    plan_key = users[user_id]["pending_plan"]
    plan_data = plans[plan_key]
    
    # ارسال به ادمین
    admin_msg = languages["en"]["admin_new_request"].format(
        message.from_user.first_name,
        user_id,
        plan_data["name"]["en"],
        plan_data["price"],
        message.text
    )
    bot.send_message(ADMIN_ID, admin_msg)
    
    # پاسخ به کاربر
    bot.send_message(message.chat.id, languages[lang]["pending_approval"])
    
    # حذف pending_plan
    del users[user_id]["pending_plan"]
    save_users()

@bot.message_handler(commands=['approve'])
def approve_transaction(message):
    if str(message.from_user.id) != ADMIN_ID:
        return
    
    try:
        _, user_id, plan_key = message.text.split()
        user_id = str(user_id)
        
        if user_id not in users:
            bot.send_message(ADMIN_ID, "⚠️ کاربر یافت نشد.")
            return
            
        users[user_id]["plans"].append(plan_key)
        save_users()
        
        lang = get_lang(user_id)
        bot.send_message(
            user_id,
            languages[lang]["confirmed"].format(plans[plan_key]["name"][lang])
        )
        bot.send_message(ADMIN_ID, "✅ تراکنش تأیید شد.")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"⚠️ خطا: {str(e)}")

@bot.message_handler(func=lambda msg: msg.text in ["💵 دریافت سود", "💵 Get Profit"])
def get_profit(message):
    user_id = str(message.from_user.id)
    lang = get_lang(user_id)
    
    if user_id not in users or not users[user_id]["plans"]:
        bot.send_message(message.chat.id, languages[lang]["no_plans"])
        return
    
    today = datetime.now().strftime("%Y-%m-%d")
    if users[user_id]["last_profit_date"] == today:
        bot.send_message(message.chat.id, languages[lang]["already_today"])
        return
    
    total_profit = sum([plans[p]["daily_profit"] for p in users[user_id]["plans"]])
    users[user_id]["balance"] += total_profit
    users[user_id]["total_profit"] += total_profit
    users[user_id]["last_profit_date"] = today
    save_users()
    
    bot.send_message(
        message.chat.id,
        languages[lang]["profit_added"].format(total_profit)
    )

@bot.message_handler(func=lambda msg: msg.text in ["💼 وضعیت من", "💼 My Status"])
def status(message):
    user_id = str(message.from_user.id)
    lang = get_lang(user_id)
    
    if user_id not in users:
        send_welcome(message)
        return
    
    user = users[user_id]
    plans_names = get_user_plans_names(user_id, lang)
    
    bot.send_message(
        message.chat.id,
        languages[lang]["status"].format(
            user["balance"],
            user["total_profit"],
            plans_names
        )
    )

if __name__ == "__main__":
    bot.infinity_polling()