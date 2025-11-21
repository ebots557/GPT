import os
import threading
import asyncio
import logging
from flask import Flask
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, PeerIdInvalid
from motor.motor_asyncio import AsyncIOMotorClient
from groq import Groq
from gtts import gTTS
from deep_translator import GoogleTranslator

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID", "123456")) 
API_HASH = os.environ.get("API_HASH", "your_api_hash") 
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "your_groq_key")
MONGO_URL = os.environ.get("MONGO_URL", "your_mongo_url")
OWNER_ID = int(os.environ.get("OWNER_ID", "8071471652"))

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DATABASE SETUP (MongoDB) ---
try:
    mongo_client = AsyncIOMotorClient(MONGO_URL)
    db = mongo_client["EvaraBotDB"]
    users_col = db["users"]
    groups_col = db["groups"]
    logger.info("Connected to MongoDB")
except Exception as e:
    logger.error(f"Database Connection Error: {e}")
    users_col = None
    groups_col = None

# --- DATABASE FUNCTIONS ---
async def add_user(user_id):
    if users_col is None: return
    try:
        if not await users_col.find_one({"_id": user_id}):
            await users_col.insert_one({"_id": user_id})
    except Exception:
        pass

async def add_group(chat_id):
    if groups_col is None: return
    try:
        if not await groups_col.find_one({"_id": chat_id}):
            await groups_col.insert_one({"_id": chat_id})
    except Exception:
        pass

async def remove_user(user_id):
    if users_col is None: return
    try:
        await users_col.delete_one({"_id": user_id})
    except Exception:
        pass

async def remove_group(chat_id):
    if groups_col is None: return
    try:
        await groups_col.delete_one({"_id": chat_id})
    except Exception:
        pass

# --- FLASK KEEP-ALIVE ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Evara AI Bot is Alive and Running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    # Note: Use asyncio.run(app.run(host="0.0.0.0", port=port)) if running the bot in the same async event loop, 
    # but threading.Thread(target=run_flask) is correct for separating Flask/Pyrogram loops.
    app.run(host="0.0.0.0", port=port)

# --- BOT CLIENT ---
bot = Client(
    "EvaraAI",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# --- GROQ CLIENT ---
groq_client = Groq(api_key=GROQ_API_KEY)

# --- UTILS ---
INTRO_IMG = "https://iili.io/KLcFyrP.jpg"

# --- HANDLERS ---

@bot.on_message(filters.command("start"))
async def start_command(client, message: Message):
    if users_col is not None:
        asyncio.create_task(add_user(message.from_user.id))
    
    user = message.from_user
    mention = user.mention
    caption = (
        f"Hᴇʏ ᴛʜᴇʀᴇ, ᴅᴇᴀʀ {mention} 💖\n"
        "ʜᴏᴘᴇ ᴛᴏᴅᴀʏ ɪs ᴛʀᴇᴀᴛɪɴɢ ʏᴏᴜ ᴡɪᴛʜ ɢʟᴏᴡ, ɢʀᴀᴄᴇ ᴀɴᴅ ɢᴏᴏᴅ ɴᴇᴡs!\n\n"
        "ɪ ᴀᴍ ᴀɪ ʙᴀsᴇᴅ ᴇᴠᴀʀᴀ ᴄʜᴀᴛ ɢᴘᴛ !\n"
        "✦ ᴀsᴋ ᴍᴇ ᴀɴʏᴛʜɪɴɢ ɪɴ ᴍʏ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ ᴏʀ ɢʀᴏᴜᴘ ᴜsɪɴɢ /ask [ʏᴏᴜʀ ǫᴜᴇʀʏ ʜᴇʀᴇ].\n"
        "ᴛᴏ sᴇᴇ ᴀʟʟ ᴍʏ ᴄᴏᴍᴍᴀɴᴅs ᴀɴᴅ ғᴇᴀᴛᴜʀᴇs, sɪᴍᴘʟʏ ᴛᴀᴘ ᴛʜᴇ ʜᴇʟᴘ ᴀɴᴅ ᴄᴏᴍᴍᴀɴᴅs ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ!\n\n"
        "ᴘᴏᴡᴇʀᴇᴅ ʙʏ ● [ᴇᴠᴀʀᴀ ʙᴏᴛs](https://t.me/EvaraBots)"
    )

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("ᴀᴅᴅ ᴍᴇ ɪɴ ɢʀᴏᴜᴘ +", url=f"https://t.me/{client.me.username}?startgroup=true")],
        [
            InlineKeyboardButton("ᴅᴇᴠᴇʟᴏᴘᴇʀ", user_id=OWNER_ID),
            InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ", url="https://t.me/EvaraSupportChat")
        ],
        [InlineKeyboardButton("ʜᴇʟᴘ ᴀɴᴅ ᴄᴏᴍᴍᴀɴᴅs", callback_data="help_section")]
    ])

    try:
        await message.reply_photo(photo=INTRO_IMG, caption=caption, reply_markup=buttons)
    except Exception:
        await message.reply_text(text=caption, reply_markup=buttons, disable_web_page_preview=True)

@bot.on_callback_query()
async def callback_handlers(client, cb: CallbackQuery):
    data = cb.data
    
    if data == "help_section":
        text = "ʜᴇʏ, ᴄʟɪᴄᴋ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ , ᴛᴏ sᴇᴇ ʜᴏᴡ ᴛᴏ ᴜsᴇ ! ᴛʜɪs ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅ."
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("ᴛᴛs🎙️", callback_data="info_tts"), InlineKeyboardButton("ᴛʀᴀɴsʟᴀᴛᴇ📟", callback_data="info_tr")],
            [InlineKeyboardButton("ᴜsᴇʀs ɪᴅ🆔", callback_data="info_id"), InlineKeyboardButton("ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ🥀", callback_data="go_home")]
        ])
        await cb.message.edit_caption(caption=text, reply_markup=buttons)

    elif data == "info_tts":
        text = "/tts - ᴡʀɪᴛᴇ ᴀɴʏ ᴛᴇxᴛ, ᴛʜɪs ᴄᴏɴᴠᴇʀᴛ ʏᴏᴜʀ ᴛᴇxᴛ ɪɴᴛᴏ ᴀɪ ᴠᴏɪᴄᴇ"
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="help_section")]])
        await cb.message.edit_caption(caption=text, reply_markup=btn)

    elif data == "info_tr":
        text = "/tr - ʀᴇᴘʟʏ ᴀɴʏ ᴍᴇssᴀɢᴇ, ɪᴛ ᴄᴏɴᴠᴇʀᴛ ᴛʜᴀᴛ ʟᴀɴɢᴀᴜɢᴇ ɪɴ ᴇɴɢʟɪsʜ"
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="help_section")]])
        await cb.message.edit_caption(caption=text, reply_markup=btn)

    elif data == "info_id":
        text = "/id - ɢᴇᴛ ʏᴏᴜʀ ɪᴅ ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ᴜsᴇʀ ᴍᴇssᴀɢᴇ/ᴜsᴇʀɴᴀᴍᴇ"
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="help_section")]])
        await cb.message.edit_caption(caption=text, reply_markup=btn)

    elif data == "go_home":
        user = cb.from_user
        mention = user.mention
        caption = (
            f"Hᴇʏ ᴛʜᴇʀᴇ, ᴅᴇᴀʀ {mention} 💖\n"
            "ʜᴏᴘᴇ ᴛᴏᴅᴀʏ ɪs ᴛʀᴇᴀᴛɪɴɢ ʏᴏᴜ ᴡɪᴛʜ ɢʟᴏᴡ, ɢʀᴀᴄᴇ ᴀɴᴅ ɢᴏᴏᴅ ɴᴇᴡs!\n\n"
            "ɪ ᴀᴍ ᴀɪ ʙᴀsᴇᴅ ᴇᴠᴀʀᴀ ᴄʜᴀᴛ ɢᴘᴛ !\n"
            "✦ ᴀsᴋ ᴍᴇ ᴀɴʏᴛʜɪɴɢ ɪɴ ᴍʏ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ ᴏʀ ɢʀᴏᴜᴘ ᴜsɪɴɢ /ask [ʏᴏᴜʀ ǫᴜᴇʀʏ ʜᴇʀᴇ].\n"
            "ᴛᴏ sᴇᴇ ᴀʟʟ ᴍʏ ᴄᴏᴍᴍᴀɴᴅs ᴀɴᴅ ғᴇᴀᴛᴜʀᴇs, sɪᴍᴘʟʏ ᴛᴀᴘ ᴛʜᴇ ʜᴇʟᴘ ᴀɴᴅ ᴄᴏᴍᴍᴀɴᴅs ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ!\n\n"
            "ᴘᴏᴡᴇʀᴇᴅ ʙʏ ● [ᴇᴠᴀʀᴀ ʙᴏᴛs](https://t.me/Evara_Updates)"
        )
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("ᴀᴅᴅ ᴍᴇ ɪɴ ɢʀᴏᴜᴘ +", url=f"https://t.me/{client.me.username}?startgroup=true")],
            [
                InlineKeyboardButton("ᴅᴇᴠᴇʟᴏᴘᴇʀ", user_id=OWNER_ID),
                InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ", url="https://t.me/EvaraSupportChat")
            ],
            [InlineKeyboardButton("ʜᴇʟᴘ ᴀɴᴅ ᴄᴏᴍᴍᴀɴᴅs", callback_data="help_section")]
        ])
        await cb.message.edit_caption(caption=caption, reply_markup=buttons)

@bot.on_message(filters.command("ask"))
async def ask_ai(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("ᴘʟᴇᴀsᴇ ᴜsᴇ /ask [ʏᴏᴜʀ ǫᴜᴇʀʏ ʜᴇʀᴇ]")
    
    query = message.text.split(None, 1)[1]
    
    await client.send_chat_action(message.chat.id, enums.ChatAction.TYPING)

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are Evara, a helpful AI assistant. Keep answers concise and friendly."
                },
                {
                    "role": "user",
                    "content": query,
                }
            ],
            model="llama-3.3-70b-versatile", 
        )
        response = chat_completion.choices[0].message.content
        
        # Split long responses
        if len(response) > 4000:
            for i in range(0, len(response), 4000):
                await message.reply_text(response[i:i+4000])
        else:
            await message.reply_text(response)
        
        if message.chat.type == enums.ChatType.PRIVATE and users_col is not None:
            asyncio.create_task(add_user(message.from_user.id))

    except Exception as e:
        await message.reply_text(f"ᴇʀʀᴏʀ: {str(e)}\n\n_Try again later._")

@bot.on_message(filters.command("tts"))
async def text_to_speech(client, message: Message):
    text = None
    if message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption
    elif len(message.command) > 1:
        text = message.text.split(None, 1)[1]
        
    if not text:
        return await message.reply_text("Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴛᴇxᴛ ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ. Usᴀɢᴇ: /tts ʜᴇʟʟᴏ")
    
    m = await message.reply_text("ᴘʀᴏᴄᴇssɪɴɢ ᴀᴜᴅɪᴏ...")
    await client.send_chat_action(message.chat.id, enums.ChatAction.RECORD_AUDIO)

    try:
        tts = gTTS(text=text, lang='en')
        file_path = f"tts_{message.from_user.id}.mp3"
        tts.save(file_path)
        
        await message.reply_audio(audio=file_path, caption=f"🎤 ᴛᴇxᴛ: {text[:50]}...")
        await m.delete()
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        await m.edit_text(f"Error: {e}")

@bot.on_message(filters.command("tr"))
async def translate_text(client, message: Message):
    target = message.reply_to_message
    if not target or (not target.text and not target.caption):
        return await message.reply_text("Rᴇᴘʟʏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ᴛʀᴀɴsʟᴀᴛᴇ ɪᴛ.")
    
    text_to_tr = target.text or target.caption
    m = await message.reply_text("ᴛʀᴀɴsʟᴀᴛɪɴɢ...")
    
    try:
        translated = GoogleTranslator(source='auto', target='en').translate(text_to_tr)
        await m.edit_text(f"**ᴏʀɪɢɪɴᴀʟ→:** {text_to_tr}\n\n**Tʀᴀɴsʟᴀᴛᴇᴅ→ (English):** {translated}")
    except Exception as e:
        await m.edit_text(f"Error: {e}")

@bot.on_message(filters.command("id"))
async def get_id(client, message: Message):
    try:
        if message.reply_to_message:
            user = message.reply_to_message.from_user
            await message.reply_text(f"👤 **✰ Usᴇʀ:** {user.first_name}\n🆔 **✰ Iᴅ:** `{user.id}`")
        elif len(message.command) > 1:
            user_input = message.command[1]
            try:
                user = await client.get_users(user_input)
                await message.reply_text(f"👤 **Usᴇʀ:** {user.first_name}\n🆔 **Iᴅ:** `{user.id}`")
            except Exception:
                await message.reply_text("❌ Usᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ ᴏʀ ɪɴᴠᴀɪʟᴇᴅ ᴜsᴇʀɴᴀᴍᴇ.")
        else:
            await message.reply_text(f"👤 **Usᴇʀ:** {message.from_user.first_name}\n🆔 **Yᴏᴜʀ ɪᴅ:** `{message.from_user.id}`\n💬 **Cʜᴀᴛ ɪᴅ:** `{message.chat.id}`")
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@bot.on_message(filters.new_chat_members)
async def welcome_group(client, message: Message):
    for member in message.new_chat_members:
        if member.id == client.me.id:
            if groups_col is not None:
                asyncio.create_task(add_group(message.chat.id))
            await message.reply_text(
                "ᴛʜᴀɴᴋs ғᴏʀ ᴀᴅᴅɪɴɢ ᴍᴇ, ɪ ᴀᴍ ʜᴇʀᴇ, ᴀsᴋ ᴍᴇ ᴀɴʏᴛʜɪɴɢ !\nʙʏ /ask [ʏᴏᴜʀ ǫᴜᴇʀʏ]"
            )

@bot.on_message(filters.private & ~filters.command("ask") & ~filters.service)
async def handle_private_no_command(client, message: Message):
    if message.text and not message.text.startswith("/"):
        await message.reply_text("◉ Pʟᴇᴀsᴇ ᴜsᴇ /ask [ʏᴏᴜʀ ǫᴜᴇʀʏ ʜᴇʀᴇ] ᴛʜɪs ɪs ᴀ ᴍᴀɪɴ ᴄᴏᴍᴍᴀɴᴅ !")

# --- OWNER COMMANDS (Working in Private and Group for Owner) ---

@bot.on_message(filters.command("stats") & filters.user(OWNER_ID))
async def bot_stats(client, message: Message):
    if users_col is None or groups_col is None:
        return await message.reply_text("Database not connected or collection missing.")
        
    m = await message.reply_text("Fᴇᴛᴄʜɪɴɢ sᴛᴀᴛs◉‿◉...")
    try:
        # Count documents
        users_count = await users_col.count_documents({})
        groups_count = await groups_col.count_documents({})
        
        # Apply the requested custom formatting
        stats_text = (
            "📊 **ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs**\n\n"
            f"        ✦ ᴛᴏᴛᴀʟ ᴜsᴇʀs (ᴘʀɪᴠᴀᴛᴇ): `{users_count}`\n"
            f"        ✦ ᴛᴏᴛᴀʟ ɢʀᴏᴜᴘs: `{groups_count}`\n\n"
            "        ❖ ᴘᴏᴡᴇʀᴇᴅ ʙʏ :- [ᴇᴠᴀʀᴀ ʙᴏᴛs](https://t.me/Evara_Updates)"
        )
        
        await m.edit_text(stats_text, disable_web_page_preview=True)
    except Exception as e:
        await m.edit_text(f"Error fetching stats: {e}")

@bot.on_message(filters.command("gcast") & filters.user(OWNER_ID))
async def broadcast_msg(client, message: Message):
    if users_col is None or groups_col is None:
        return await message.reply_text("Database not connected or collection missing.")
        
    if not message.reply_to_message:
        return await message.reply_text("Rᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ғᴏʀ ʙʀᴏᴀᴅᴄᴀsᴛ!!.")
    
    msg = message.reply_to_message
    m = await message.reply_text("Bʀᴏᴀᴅᴄᴀsᴛ sᴛᴀʀᴛᴇᴅ...")
    
    success_users = 0
    success_groups = 0
    
    # Broadcast to Users
    async for user_doc in users_col.find():
        user_id = user_doc["_id"]
        try:
            # Use copy() which is generally more reliable than forward() for broadcasing
            await msg.forward(user_id) 
            success_users += 1
            await asyncio.sleep(0.5)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await msg.forward(user_id)
            success_users += 1
        except (UserIsBlocked, InputUserDeactivated, PeerIdInvalid):
            # Passively remove user if they've blocked the bot or account is deactivated
            await remove_user(user_id)
        except Exception:
            pass

    # Broadcast to Groups
    async for group_doc in groups_col.find():
        chat_id = group_doc["_id"]
        try:
            # Use copy()
            await msg.forward(chat_id)
            success_groups += 1
            await asyncio.sleep(0.5)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await msg.forward(chat_id)
            success_groups += 1
        except Exception:
            # Passively remove group if the bot was kicked or other issue
            await remove_group(chat_id)

    await m.edit_text(
        f"✅ **◉ Bʀᴏᴀᴅᴄᴀsᴛ Cᴏᴍᴘʟᴇᴛᴇᴅ.**\n\n"
        f"✦ Sᴇɴᴛ ᴛᴏ **{success_users}** users.\n"
        f"✦ Sᴇɴᴛ ᴛᴏ **{success_groups}** groups."
    )

if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    print("Bot Started...")
    bot.run()
