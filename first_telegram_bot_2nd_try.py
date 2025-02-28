import requests
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import first_app_with_weather_api

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_NINJAS_KEY = os.getenv("QUOTE_GENERATOR_TOKEN")
BOT_USERNAME = "@Naods_First_Bot"
PORT = int(os.environ.get("PORT", 8443))  # Render assigns PORT; default to 8443 if not set

# Function to fetch a dad joke from icanhazdadjoke
def get_joke():
    url = 'https://icanhazdadjoke.com/'
    headers = {'Accept': 'application/json'}
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Joke API Status: {response.status_code}")
        if response.status_code == 200:
            joke_data = response.json()
            return joke_data["joke"]
        else:
            return "Sorry, I couldn't fetch a joke right now."
    except Exception as e:
        return f"An error occurred: {str(e)}"
    
# Function to fetch a random quote from API Ninjas
def get_quote(category=""):
    url = 'https://api.api-ninjas.com/v1/quotes'
    params = {'category': category.lower().strip()} if category else {}
    
    try:
        response = requests.get(url, headers={'X-Api-Key': API_NINJAS_KEY}, params=params)
        print(f"API Request URL: {response.url}")
        print(f"API Response Status: {response.status_code}")
        if response.status_code == 200:
            quote_data = response.json()[0]
            print(f"API Response: {response.json()}")
            return f'"{quote_data["quote"]}"\n— {quote_data["author"]}'
        else:
            return f"Sorry, I couldn't fetch a quote. Status: {response.status_code}"
    except Exception as e:
        return f"An error occurred: {str(e)}"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello, I am Naod's First Bot, how can I help you?")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("I am Naod's First Bot! Use /quote [category] for a quote (e.g., /quote love).")

async def generate_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = " ".join(context.args) if context.args else ""
    print(f"Requested category: '{category}'")
    quote = get_quote(category)
    await update.message.reply_text(quote)

async def generate_joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    joke = get_joke()
    await update.message.reply_text(joke)

async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = " ".join(context.args) if context.args else ""
    print(f"Requested city: '{city}'")
    if not city:
        await update.message.reply_text("Please provide a city name (e.g., /weather Denver)")
        return
    weather = first_app_with_weather_api.WeatherApp.get_weather(city)
    print(f"Weather response: '{weather}'")
    await update.message.reply_text(weather)
    
# Responses
def response_handler(text: str) -> str:
    text = text.lower().strip()
    responses = {
        "hello": "Hello, how are you?",
        "goodbye": "Goodbye, have a great day!",
        "how are you": "I am doing well, thank you for asking!",
        "what is your name": "I am Naod's First Bot, how can I help you?",
        "what is your purpose": "I am here to help you with anything you need, just ask me!"
    }
    return responses.get(text, "I am sorry, I do not understand that.")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type = update.message.chat.type
    text = update.message.text
    print(f"User {update.message.chat.id} in {message_type}: '{text}'")

    if message_type == "group":
        if BOT_USERNAME in text:
            new_text = text.replace(BOT_USERNAME, "").strip()
            response = response_handler(new_text)
        else:
            return
    else:
        response = response_handler(text)
    
    print("Bot: ", response)
    await update.message.reply_text(response)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")
    if update and update.message:
        await update.message.reply_text("Oops, something went wrong!")

if __name__ == "__main__":
    print("Bot is starting...")
    
    # Validate environment variables
    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not set in environment")
    if not API_NINJAS_KEY:
        raise ValueError("QUOTE_GENERATOR_TOKEN not set in environment")

    # Build the application
    app = Application.builder().token(TOKEN).build()

    # Add command and message handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("quote", generate_quote))
    app.add_handler(CommandHandler("joke", generate_joke))
    app.add_handler(CommandHandler("weather", weather_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_error_handler(error)

    # Webhook configuration
    webhook_url = f"https://My-first-telegram-bot-2.onrender.com/{TOKEN}"
    print(f"Setting webhook to: {webhook_url}")

    # Start the bot with webhook
    app.run_webhook(
        listen="0.0.0.0",  # Listen on all interfaces
        port=PORT,         # Use Render's assigned port or default 8443
        url_path=TOKEN,    # Telegram sends updates to this path
        webhook_url=webhook_url  # Full URL Telegram should send updates to
    )