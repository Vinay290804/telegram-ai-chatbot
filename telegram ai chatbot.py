import logging
import os
import google.generativeai as genai
import pymongo
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, Dispatcher

# Environment Variables
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
MONGO_URI = "YOUR_MONGODB_CONNECTION_STRING"

# Set up Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# MongoDB Connection
client = pymongo.MongoClient(MONGO_URI)
db = client["telegram_bot"]
users_collection = db["users"]
chats_collection = db["chats"]
files_collection = db["files"]

# Flask App
app = Flask(_name_)

# Logging
logging.basicConfig(level=logging.INFO)

# Function to handle new user registration
def register_user(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    username = update.message.chat.username
    first_name = update.message.chat.first_name

    user_data = {
        "chat_id": chat_id,
        "username": username,
        "first_name": first_name
    }

    # Check if user exists
    if not users_collection.find_one({"chat_id": chat_id}):
        users_collection.insert_one(user_data)
        update.message.reply_text("✅ Registered successfully! Please share your phone number.", 
                                  reply_markup=ReplyKeyboardMarkup(
                                      [[KeyboardButton("📞 Share Contact", request_contact=True)]], 
                                      one_time_keyboard=True, resize_keyboard=True
                                  ))

# Function to save user's phone number
def save_phone_number(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    phone_number = update.message.contact.phone_number

    users_collection.update_one({"chat_id": chat_id}, {"$set": {"phone_number": phone_number}})
    update.message.reply_text("✅ Phone number saved!")

# Function to process text messages using Gemini AI
def chat_with_ai(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user_message = update.message.text

    # Call Gemini AI
    response = genai.generate_text(prompt=user_message).text.strip()

    # Store chat history in MongoDB
    chat_data = {
        "chat_id": chat_id,
        "user_message": user_message,
        "bot_response": response
    }
    chats_collection.insert_one(chat_data)

    update.message.reply_text(response)

# Function to handle images and files
def handle_files(update: Update, context: CallbackContext):
    file = update.message.document or update.message.photo[-1]
    file_id = file.file_id
    file_info = context.bot.get_file(file_id)
    file_url = file_info.file_path

    # Store file metadata in MongoDB
    file_metadata = {
        "chat_id": update.message.chat_id,
        "file_id": file_id,
        "file_url": file_url
    }
    files_collection.insert_one(file_metadata)

    update.message.reply_text(f"✅ File received. Processing...")
    # (Optional) Use AI to analyze content here

# Function to perform web search (placeholder)
def web_search(update: Update, context: CallbackContext):
    update.message.reply_text("🔍 Web search is not implemented yet!")

# Webhook setup
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(), bot)
    dp.process_update(update)
    return "OK"

if _name_ == "_main_":
    from telegram import Bot
    from telegram.ext import Dispatcher

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(bot, None, workers=4)

    # Add Handlers
    dp.add_handler(CommandHandler("start", register_user))
    dp.add_handler(MessageHandler(Filters.contact, save_phone_number))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, chat_with_ai))
    dp.add_handler(MessageHandler(Filters.document | Filters.photo, handle_files))
    dp.add_handler(CommandHandler("websearch", web_search))

    # Start Flask server
    app.run(host="0.0.0.0", port=5000, debug=True)
