import requests
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import first_app_with_weather_api
import spacy
from spacytextblob.spacytextblob import SpacyTextBlob

# Load spaCy model and add sentiment analysis pipeline
nlp = spacy.load('en_core_web_sm')
nlp.add_pipe("spacytextblob")

#Environment variables
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
    
# Sentiment Analysis with spaCy
def analyze_sentiment(text: str) -> str:
    doc = nlp(text)
    polarity = doc._.blob.polarity
    if polarity > 0.1:
        return "Positive"
    elif polarity < -0.1:
        return "Negative"
    else:
        return "Neutral"

# Simple Intent Recognition with spaCy
def recognize_intent(text: str) -> str:
    doc = nlp(text.lower().strip())
    tokens = [token.text for token in doc]
    print(f"Tokens: {tokens}")  # Debug: See what spaCy tokenized
    
    # Check for greetings
    greeting_keywords = {"hello", "hi", "hey"}
    if any(token in greeting_keywords for token in tokens):
        print("Intent detected: greeting")  # Debug
        return "greeting"
    
    # Check for farewells
    farewell_keywords = {"goodbye", "bye", "see you"}
    if any(token in farewell_keywords for token in tokens):
        print("Intent detected: farewell")  # Debug
        return "farewell"

    # Check for Weather
    weather_keyword = {"weather", "temperature", "forecast"}
    if any(token in weather_keyword for token in tokens):
        print("Intent detected: weather")  # Debug
        return "weather"
    
    # Check for Joke
    joke_keyword = {"joke", "funny", "humor"}
    if any(token in joke_keyword for token in tokens):
        print("Intent detected: joke")
        return "joke"

    # Check for Quote
    quote_keyword = {"quote", "inspire", "motivate"}
    if any(token in quote_keyword for token in tokens):
        print("Intent detected: quote")
        return "quote"

    # Sadness or emotional state (for better sentiment handling)
    if any(token in {"sad", "down", "unhappy"} for token in tokens):
        return "sad"

    # Yes/No for follow-up (e.g., "want a joke?")
    if any(token in {"yes", "yeah", "sure"} for token in tokens):
        return "yes"
    if any(token in {"no", "nah", "nope"} for token in tokens):
        return "no"
    
    # Check for questions (using POS tagging for Wh-words)
    for token in doc:
        print(f"Token: {token.text}, POS: {token.pos_}, Tag: {token.tag_}")  # Debug
        if token.tag_ == "WP" or token.pos_ == "PRON" and token.text in {"what", "who", "where", "when", "why", "how"}:
            print("Intent detected: question")  # Debug
            return "question"

    # Default case
    print("Intent detected: unknown")  # Debug
    return "unknown"

# Command handlers

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello, I am Naod's First Bot, how can I help you?")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use /quote [category], /joke, or /weather [city]. I also analyze your mood and intent!")

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
async def response_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> str:
    text = text.lower().strip()
    sentiment = analyze_sentiment(text)
    intent = recognize_intent(text)
    user_data = context.user_data # for state tracking

    # Handle previous context(e.g., waiting for city or yes/no)
    if "waiting_for" in user_data:
        if user_data["waiting_for"] == "city":
            city = text.stip()
            weather = first_app_with_weather_api.WeatherApp.get_weather(city)
            del user_data["waiting_for"]
            return weather
        elif user_data["waiting_for"] == "joke_confirmation":
            if intent == "yes":
                del user_data["waiting_for"]
                return get_joke()
            elif intent == "no":
                del user_data["waiting_for"]
                return "Okay, let me know how can I help!"
            else:
                return "Please say 'yes' or 'no' Want a joke to cheer up?"
    
    # Base responses
    responses = {
        "greeting": "Hello! How can I assist you today?",
        "farewell": "Goodbye! Have a great day!",
        "question": "I'm here to help! What would you like to know?",
        "joke": get_joke(),
        "quote": get_quote(),
        "weather": "Which city would you like the weather for?",
        "sad": "Sorry to hear you're feeling down. Want a joke to cheer up?",
        "unknown": "I'm not sure what you mean. How can I assist?"
    }

    base_response = responses.get(intent, responses["unknown"])

    # State transitions
    if intent == "weather":
        user_data["waiting_for"] = city
    elif intent == "sad" and sentiment == "Negative":
        user_data["waiting_for"] = "joke_confirmation"

    # Sentiment Modification
    if sentiment == "Positive" and intent not in ["joke", "quote", "weather"]:
        return f"{base_response} You seem happy today!😊"
    elif sentiment = "Negative" and intent not in ["sad", "joke", "quote", "weather"]:
        return f"{base_response} Sorry you're feeling down.\n Want to hear a joke?😞"
    return base_response

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
    
    print(f"Bot: {response} (Sentiment: {analyze_sentiment(text)}, Intent: {recognize_intent(text)})")
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
    webhook_url = f"https://my-first-telegram-bot-4.onrender.com/{TOKEN}"
    print(f"Setting webhook to: {webhook_url}")

    # Start the bot with webhook
    app.run_webhook(
        listen="0.0.0.0",  # Listen on all interfaces
        port=PORT,         # Use Render's assigned port or default 8443
        url_path=TOKEN,    # Telegram sends updates to this path
        webhook_url=webhook_url  # Full URL Telegram should send updates to
    )