import discord
from discord.ext import tasks
import asyncio
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import numpy as np
import datetime
import random

TOKEN = "ZjNkM2NkOGUtNDYzMS00OTU5LTkxYjItYWQ1NzBlNjM1NmU5"
GUILD_ID = 847596372018345732
CHANNEL_ID = 456129837123098712
MARKET_API = "https://api.solscan.io/market/metrics"

class MeowbotAI:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=5000)
        self.model = LogisticRegression(max_iter=200)
        self.training_data = self.generate_training_data()
        self.sentiment_map = {"positive": 1, "neutral": 0, "negative": -1}
        self.train_model()
        self.current_emotion = "neutral"

    def generate_training_data(self):
        base_data = [
            ("I love this project!", "positive"),
            ("This isn't looking good.", "negative"),
            ("I'm feeling unsure.", "neutral"),
            ("Amazing progress!", "positive"),
            ("This is disastrous.", "negative"),
            ("I'm holding for the long term.", "neutral"),
        ]
        additional_data = [
            ("The market is up!", "positive"),
            ("The market is down.", "negative"),
            ("We are seeing steady growth.", "neutral")
        ]
        synthetic_data = [
            (f"Generated sentiment {random.randint(1, 100)}", random.choice(["positive", "neutral", "negative"]))
            for _ in range(200)
        ]
        return base_data + additional_data + synthetic_data

    def train_model(self):
        texts, sentiments = zip(*self.training_data)
        X = self.vectorizer.fit_transform(texts)
        y = [self.sentiment_map[s] for s in sentiments]
        self.model.fit(X, y)

    def analyze_sentiment(self, text):
        X = self.vectorizer.transform([text])
        return self.model.predict(X)[0]

    def fetch_market_sentiment(self):
        try:
            response = requests.get(MARKET_API, timeout=5)
            if response.status_code == 200:
                data = response.json()
                holder_count = data.get("holder_count", 0)
                price_change = data.get("price_change_percentage", 0.0)
                if holder_count > 2000 and price_change > 1.0:
                    return 1
                elif holder_count < 1000 and price_change < -1.0:
                    return -1
                else:
                    return 0
        except requests.RequestException:
            return 0

    def update_emotion(self, sentiment_score):
        if sentiment_score > 0:
            self.current_emotion = "happy"
        elif sentiment_score < 0:
            self.current_emotion = "sad"
        else:
            self.current_emotion = "neutral"

    def generate_ai_message(self):
        timestamp = datetime.datetime.now().isoformat()
        return f"Meowbot at {timestamp}: Current emotion is {self.current_emotion}"

class SentimentAggregator:
    def __init__(self):
        self.chat_sentiments = []

    def add_sentiment(self, score):
        self.chat_sentiments.append(score)
        if len(self.chat_sentiments) > 100:
            self.chat_sentiments.pop(0)

    def calculate_overall_sentiment(self):
        if len(self.chat_sentiments) == 0:
            return 0
        return np.mean(self.chat_sentiments)

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

client = discord.Client(intents=intents)
meowbot_ai = MeowbotAI()
sentiment_aggregator = SentimentAggregator()

@tasks.loop(seconds=30)
async def analyze_chat():
    guild = discord.utils.get(client.guilds, id=GUILD_ID)
    if guild is None:
        return
    channel = discord.utils.get(guild.text_channels, id=CHANNEL_ID)
    if channel is None:
        return
    async for message in channel.history(limit=50):
        sentiment_score = meowbot_ai.analyze_sentiment(message.content)
        sentiment_aggregator.add_sentiment(sentiment_score)
    overall_sentiment = sentiment_aggregator.calculate_overall_sentiment()
    market_sentiment = meowbot_ai.fetch_market_sentiment()
    final_sentiment = overall_sentiment + market_sentiment
    meowbot_ai.update_emotion(final_sentiment)

@client.event
async def on_ready():
    analyze_chat.start()

@client.event
async def on_message(message):
    if message.author.bot:
        return
    sentiment_score = meowbot_ai.analyze_sentiment(message.content)
    sentiment_aggregator.add_sentiment(sentiment_score)
    if "meowbot" in message.content.lower():
        response = meowbot_ai.generate_ai_message()
        await message.channel.send(response)

async def post_launch_phase():
    await asyncio.sleep(86400)
    print("Post-launch phase initialized. Preparing additional AI capabilities.")

client.run(TOKEN)
