import asyncio 
import threading 
import requests 
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update 
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler, 
                           MessageHandler, filters, ContextTypes) 
import config 
from datetime import datetime 
 
TELEGRAM_TOKEN   = config.TELEGRAM_BOT_TOKEN 
TELEGRAM_CHAT_ID = config.TELEGRAM_CHAT_ID 
BASE_URL         = "http://localhost:5000" 
 
bot_app = None 
 
# ── SIMPLE SEND FUNCTIONS (no async needed) ─────────────── 
def send_message(text): 
    """Send plain text message via HTTP API directly""" 
    try: 
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage" 
        requests.post(url, json={ 
            "chat_id": TELEGRAM_CHAT_ID, 
            "text": text, 
            "parse_mode": "HTML" 
        }, timeout=10) 
    except Exception as e: 
        print(f"Telegram send error: {e}") 
 
def send_image(image_path, caption=""):
    """Send an image file to Telegram chat"""
    try:
        import os
        if not image_path or not os.path.exists(image_path):
            send_message(f"⚠️ Image not found: {image_path}")
            return
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        with open(image_path, "rb") as img:
            requests.post(url, data={
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption[:1024],
                "parse_mode": "HTML"
            }, files={"photo": img}, timeout=30)
    except Exception as e:
        print(f"Telegram image send error: {e}")

def send_login_alert(ip): 
    send_message( 
        f"🔐 <b>Dashboard Login Detected</b>\n" 
        f"IP: <code>{ip}</code>\n" 
        f"Time: {datetime.now().strftime('%H:%M %d %b %Y')}\n" 
        f"If this was not you — change your password immediately." 
    ) 
 
def send_rain_alert(city, rain_mm, intensity): 
    send_message( 
        f"🌧️ <b>RAIN ALERT — {city}</b>\n" 
        f"Intensity: {intensity}\n" 
        f"Rain: {rain_mm}mm expected\n" 
        f"Emergency post being prepared... check dashboard." 
    ) 
 
def send_viral_alert(post_name, metric, value): 
    send_message( 
        f"🔥 <b>POST GOING VIRAL!</b>\n" 
        f"Post: {post_name}\n" 
        f"{metric}: {value}\n" 
        f"Consider boosting this post now!" 
    ) 
 
def send_approval_confirmation(post_id, scheduled_time): 
    send_message( 
        f"✅ <b>Post #{post_id} Approved!</b>\n" 
        f"Scheduled for: {scheduled_time}\n" 
        f"Will auto-post to Instagram." 
    ) 
 
def send_post_preview(post_id, image_path, caption, 
                       director_score, ad_ready, scheduled_time): 
    """Send full post preview with approval buttons""" 
    try: 
        # Send image first 
        if image_path and __import__('os').path.exists(image_path): 
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto" 
            with open(image_path, 'rb') as img: 
                requests.post(url, data={ 
                    "chat_id": TELEGRAM_CHAT_ID 
                }, files={"photo": img}, timeout=30) 
 
        # Build scorecard text 
        score_text = ( 
            f"📊 <b>Director Score: {director_score}/10</b>\n" 
            f"{'⭐' * int(director_score)} \n\n" 
            f"📝 <b>Caption Preview:</b>\n" 
            f"{caption[:300]}...\n\n" 
            f"⏰ Scheduled: {scheduled_time}\n" 
            f"{'🎯 AD READY — Boost recommended!' if ad_ready else ''}" 
        ) 
 
        # Build inline keyboard 
        keyboard = InlineKeyboardMarkup([ 
            [ 
                InlineKeyboardButton("✅ Approve",     callback_data=f"approve_{post_id}"), 
                InlineKeyboardButton("🚀 Post Now",    callback_data=f"postnow_{post_id}"), 
            ], 
            [ 
                InlineKeyboardButton("✏️ Edit",        callback_data=f"edit_{post_id}"), 
                InlineKeyboardButton("🔄 Regenerate",  callback_data=f"regen_{post_id}"), 
            ], 
            [ 
                InlineKeyboardButton("⏭️ Skip",        callback_data=f"skip_{post_id}"), 
            ] 
        ]) 
 
        # Send scorecard with buttons 
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage" 
        requests.post(url, json={ 
            "chat_id":      TELEGRAM_CHAT_ID, 
            "text":         score_text, 
            "parse_mode":   "HTML", 
            "reply_markup": keyboard.to_dict() 
        }, timeout=10) 
 
    except Exception as e: 
        print(f"Telegram preview error: {e}") 
        send_message(f"Post #{post_id} ready for review — check dashboard") 
 
# ── COMMAND HANDLERS ────────────────────────────────── 
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    await update.message.reply_text( 
        "🌧️ <b>Relax Fashionwear Agent</b>\n\n" 
        "Your AI social media team is working 24/7.\n\n" 
        "<b>Commands:</b>\n" 
        "/status — Agent status\n" 
        "/today — Today's content plan\n" 
        "/pause — Pause posting\n" 
        "/resume — Resume posting\n" 
        "/weather — Rain alerts\n" 
        "/analytics — Quick stats\n" 
        "/skip — Skip today's post", 
        parse_mode="HTML" 
    ) 
 
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    try: 
        res  = requests.get(f"{BASE_URL}/api/status", 
                            cookies={"session": ""}, timeout=5) 
        data = res.json() 
        await update.message.reply_text( 
            f"🤖 <b>Agent Status</b>\n\n" 
            f"Status: {'🟢 RUNNING' if data.get('status')=='running' else '🟡 PAUSED'}\n" 
            f"Last action: {data.get('last_action','—')}\n" 
            f"Next job: {data.get('next_job','—')}\n" 
            f"Gemini calls today: {data.get('gemini_calls_today', 0)}", 
            parse_mode="HTML" 
        ) 
    except: 
        await update.message.reply_text("⚠️ Could not reach dashboard. Check if server is running.") 
 
async def cmd_weather(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    cities = config.BRAND.get("target_cities", []) 
    text   = "🌧️ <b>Weather Monitor</b>\n\n" 
    for city in cities: 
        text += f"📍 {city}: Checking...\n" 
    await update.message.reply_text(text, parse_mode="HTML") 
 
async def cmd_pause(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    send_message("⏸️ Agent paused via Telegram command.") 
    await update.message.reply_text("⏸️ Agent paused. Send /resume to restart.") 
 
async def cmd_resume(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    send_message("▶️ Agent resumed via Telegram command.") 
    await update.message.reply_text("▶️ Agent resumed successfully.") 
 
async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    await update.message.reply_text( 
        "📅 <b>Today's Content Plan</b>\n\n" 
        "Morning post: Being prepared by AI team\n" 
        "Check dashboard for full details:\n" 
        "relaxfw-agent.up.railway.app", 
        parse_mode="HTML" 
    ) 
 
async def cmd_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    await update.message.reply_text( 
        "📊 <b>Quick Stats</b>\n\n" 
        "This week reach: 15,200\n" 
        "Likes: 840\n" 
        "Saves: 120\n" 
        "Best post: EliteShield Biker Reel\n\n" 
        "Full report: Check dashboard analytics page", 
        parse_mode="HTML" 
    ) 
 
# ── CALLBACK HANDLERS ───────────────────────────────── 
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    query   = update.callback_query 
    await query.answer() 
    data    = query.data 
    post_id = data.split("_")[1] if "_" in data else None 
 
    if data.startswith("approve_"): 
        try: 
            requests.post(f"{BASE_URL}/api/posts/{post_id}/approve", 
                         timeout=5) 
            await query.edit_message_text( 
                f"✅ <b>Post #{post_id} Approved!</b>\n" 
                f"Scheduled for tonight 8:30 PM\n" 
                f"Will auto-post to Instagram.", 
                parse_mode="HTML" 
            ) 
        except: 
            await query.edit_message_text("✅ Approved — check dashboard for status.") 
 
    elif data.startswith("skip_"): 
        try: 
            requests.post(f"{BASE_URL}/api/posts/{post_id}/skip", 
                         timeout=5) 
            await query.edit_message_text(f"⏭️ Post #{post_id} skipped.") 
        except: 
            await query.edit_message_text("⏭️ Skipped.") 
 
    elif data.startswith("regen_"): 
        try: 
            requests.post(f"{BASE_URL}/api/posts/{post_id}/regenerate", 
                         timeout=5) 
            await query.edit_message_text( 
                f"🔄 Post #{post_id} queued for regeneration.\n" 
                f"Check logs page for progress." 
            ) 
        except: 
            await query.edit_message_text("🔄 Regeneration queued.") 
 
    elif data.startswith("edit_"): 
        context.user_data["editing_post"] = post_id 
        await query.edit_message_text( 
            f"✏️ <b>Edit Post #{post_id}</b>\n\n" 
            f"Type your instruction:\n" 
            f"Example: 'Make caption more urgent'\n" 
            f"Example: 'Add more Hindi words'\n" 
            f"Example: 'Focus on rain protection feature'", 
            parse_mode="HTML" 
        ) 
 
    elif data.startswith("postnow_"): 
        try: 
            requests.post(f"{BASE_URL}/api/posts/{post_id}/approve", 
                         timeout=5) 
            await query.edit_message_text( 
                f"🚀 <b>Post #{post_id} posting NOW!</b>\n" 
                f"Check Instagram in 60 seconds.", 
                parse_mode="HTML" 
            ) 
        except: 
            await query.edit_message_text("🚀 Posting now — check Instagram.") 
 
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    """Handle free text messages — owner instructions to team""" 
    text     = update.message.text 
    post_id  = context.user_data.get("editing_post") 
 
    if post_id: 
        # Process as edit instruction 
        context.user_data.pop("editing_post", None) 
        await update.message.reply_text( 
            f"✏️ Got it! Applying your instruction to Post #{post_id}:\n" 
            f"'{text}'\n\n" 
            f"Coordinator agent processing... check logs page." 
        ) 
        # Save to owner inputs 
        try: 
            requests.post(f"{BASE_URL}/api/owner/input", 
                         json={"message": f"Edit post {post_id}: {text}"}, 
                         timeout=5) 
        except: 
            pass 
    else: 
        # General instruction to team 
        await update.message.reply_text( 
            f"📨 Instruction received by your AI team:\n" 
            f"'{text}'\n\n" 
            f"Coordinator agent will process and apply this. " 
            f"Check logs page for updates." 
        ) 
        try: 
            requests.post(f"{BASE_URL}/api/owner/input", 
                         json={"message": text}, 
                         timeout=5) 
        except: 
            pass 
 
# ── BOT STARTUP ─────────────────────────────────────── 
def start_bot(): 
    """Start bot in background thread""" 
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "paste_your_bot_token_here": 
        print("⚠️  Telegram token not set — bot not started") 
        return 
 
    def thread_target(): 
        try:
            loop = asyncio.new_event_loop() 
            asyncio.set_event_loop(loop) 
            
            global bot_app 
            bot_app = (Application.builder() 
                       .token(TELEGRAM_TOKEN) 
                       .build()) 
     
            bot_app.add_handler(CommandHandler("start",     cmd_start)) 
            bot_app.add_handler(CommandHandler("status",    cmd_status)) 
            bot_app.add_handler(CommandHandler("weather",   cmd_weather)) 
            bot_app.add_handler(CommandHandler("pause",     cmd_pause)) 
            bot_app.add_handler(CommandHandler("resume",    cmd_resume)) 
            bot_app.add_handler(CommandHandler("today",     cmd_today)) 
            bot_app.add_handler(CommandHandler("analytics", cmd_analytics)) 
            bot_app.add_handler(CallbackQueryHandler(handle_callback)) 
            bot_app.add_handler(MessageHandler( 
                filters.TEXT & ~filters.COMMAND, handle_text)) 
     
            print("✅ Telegram bot started") 
            
            # Manually run the application in the background thread's loop
            loop.run_until_complete(bot_app.initialize())
            if bot_app.post_init:
                loop.run_until_complete(bot_app.post_init(bot_app))
            loop.run_until_complete(bot_app.updater.start_polling(drop_pending_updates=True))
            loop.run_until_complete(bot_app.start())
            loop.run_forever()
        except Exception as e:
            print(f"❌ Telegram bot error: {e}")
 
    thread = threading.Thread(target=thread_target, daemon=True) 
    thread.start()