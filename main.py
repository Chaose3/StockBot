import os
import discord
from discord.ext import commands
import yfinance as yf
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Set up logging
logging.basicConfig(level=logging.WARN)  # You can set to DEBUG if you need more detailed logs
logger = logging.getLogger(__name__)
TOKEN = os.getenv('DISCORD_TOKEN')  # Ensure you have set your Discord token as an environment variable
CHANNEL_ID = os.getenv('CHANNEL_ID')  # Set your channel ID
if CHANNEL_ID is None:
    raise ValueError("CHANNEL_ID environment variable is not set.")
CHANNEL_ID = int(CHANNEL_ID)  # Convert to integer after checking

# Set up the bot with the command prefix
intents = discord.Intents.default()
intents.messages = True  # Enable message content intent
bot = commands.Bot(command_prefix='/', intents=intents)

# Helper Functions


def calculate_indicators(data):
    # Moving Averages
    data['SMA_50'] = data['Close'].rolling(window=50).mean()
    data['SMA_200'] = data['Close'].rolling(window=200).mean()

    # RSI
    delta = data['Close'].diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    data['RSI'] = 100 - (100 / (1 + rs))

    # MACD
    data['EMA_12'] = data['Close'].ewm(span=12, adjust=False).mean()
    data['EMA_26'] = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = data['EMA_12'] - data['EMA_26']
    data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean()

    return data


def generate_signals(data):
    signals = []

    # Moving Average Buy/Sell Signals
    if data['SMA_50'].iloc[-1] > data['SMA_200'].iloc[-1]:
        signals.append("Buy signal from Moving Average Crossover (SMA 50 > SMA 200).")
    elif data['SMA_50'].iloc[-1] < data['SMA_200'].iloc[-1]:
        signals.append("Sell signal from Moving Average Crossover (SMA 50 < SMA 200).")

    # RSI Buy/Sell Signals
    if data['RSI'].iloc[-1] < 30:
        signals.append("Buy signal from RSI (RSI < 30).")
    elif data['RSI'].iloc[-1] > 70:
        signals.append("Sell signal from RSI (RSI > 70).")

    # MACD Buy/Sell Signals
    if data['MACD'].iloc[-1] > data['Signal_Line'].iloc[-1]:
        signals.append("Buy signal from MACD crossover (MACD > Signal Line).")
    elif data['MACD'].iloc[-1] < data['Signal_Line'].iloc[-1]:
        signals.append("Sell signal from MACD crossover (MACD < Signal Line).")

    return signals


async def alert_signals(ticker):
    logger.info(f"Fetching data for ticker: {ticker}")
    try:
        data = yf.download(ticker, period='1y', interval='1d')

        if data.empty or len(data) < 200:
            logger.error(f"Not enough data for {ticker}: {data.shape}")
            return f"Not enough data for {ticker}."

        logger.info("Data fetched successfully")
        data = calculate_indicators(data)
        signals = generate_signals(data)
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {e}")
        return f"Error fetching data for {ticker}: {e}"

    if signals:
        message = f"Signals for {ticker}:\n" + "\n".join(signals)
    else:
        message = f"No significant signals for {ticker}."

    return message


async def send_daily_alerts():
    ticker = 'AAPL'  # Change this to the ticker you want to track
    logger.info("Sending daily market open alerts...")
    signals_message = await alert_signals(ticker)  # Fetch signals for the specified ticker
    channel = bot.get_channel(CHANNEL_ID)  # Use your channel ID
    await channel.send(signals_message)  # Send the alert to the channel


company_tickers = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Amazon": "AMZN",
    "Alphabet Class A": "GOOGL",
    "Alphabet Class C": "GOOG",
    "Tesla": "TSLA",
    "NVIDIA": "NVDA",
    "Meta Platforms": "META",
    "PayPal": "PYPL",
    "Intel": "INTC",
    "Netflix": "NFLX",
    "Adobe": "ADBE",
    "Booking Holdings": "BKNG",
    "Cisco Systems": "CSCO",
    "Comcast": "CMCSA",
    "Broadcom": "AVGO",
    "Qualcomm": "QCOM",
    "PepsiCo": "PEP",
    "Amgen": "AMGN",
    "T-Mobile US": "TMUS",
    "Illumina": "ILMN",
    "Starbucks": "SBUX",
    "Applied Materials": "AMAT",
    "KLA Corporation": "KLAC",
    "Charter Communications": "CHTR",
    "Gilead Sciences": "GILD",
    "Regeneron Pharmaceuticals": "REGN",
    "Vertex Pharmaceuticals": "VRTX",
    "Intuit": "INTU",
    "Cadence Design Systems": "CDNS",
    "Biogen": "BIIB",
    "Moderna": "MRNA",
    "Paychex": "PAYX",
    "Salesforce": "CRM",
    "Align Technology": "ALGN",
    "Fortinet": "FTNT",
    "Advanced Micro Devices": "AMD",
    "DocuSign": "DOCU",
    "Palo Alto Networks": "PANW",
    "CrowdStrike": "CRWD",
    "Twilio": "TWLO",
    "Nokia": "NOK",
    "Asana": "ASAN",

    "Johnson & Johnson": "JNJ",
    "JPMorgan Chase": "JPM",
    "Berkshire Hathaway": "BRK.B",
    "Visa": "V",
    "Walmart": "WMT",
    "UnitedHealth Group": "UNH",
    "Exxon Mobil": "XOM",
    "Coca-Cola": "KO",
    "Procter & Gamble": "PG",
    "AbbVie": "ABBV",
    "Home Depot": "HD",
    "Goldman Sachs": "GS",
    "American Express": "AXP",
    "McDonald's": "MCD",
    "Disney": "DIS",
    "3M": "MMM",
    "Pfizer": "PFE",
    "CVS Health": "CVS",
    "Verizon": "VZ",
    "AT&T": "T",
    "Lowe's": "LOW",
    "Bristol-Myers Squibb": "BMY",
    "Abbott Laboratories": "ABT",
    "Chevron": "CVX",
    "IBM": "IBM",
    "Union Pacific": "UNP",
    "Lockheed Martin": "LMT",
    "Nike": "NKE",
    "Travelers": "TRV",
}


# Bot Commands
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


@bot.command(name='stock', help='Get stock signals for a ticker')
async def stock(ctx, ticker: str):
    """Command to get stock signals for a given ticker."""
    async with ctx.typing():  # Optional: show typing indicator while processing
        signals_message = await alert_signals(ticker)
        await ctx.send(signals_message)


@bot.command(name='clear', help='Clear messages from the chat')
async def clear(ctx, amount: int):
    """Clears a specified number of messages."""
    if amount <= 0:
        await ctx.send("Please specify a number greater than 0.")
        return

    await ctx.channel.purge(limit=amount + 1)  # +1 to include the command message itself
    await ctx.send(f"Cleared {amount} messages!")


@bot.command(name="company", help="Get the stock ticker for a specified company.")
async def company(ctx, *, company_name: str):
    company_name = company_name.strip().title()
    ticker = company_tickers.get(company_name)

    if ticker:
        await ctx.send(f"The ticker for {company_name} is {ticker}.")
    else:
        await ctx.send(f"Sorry, I couldn't find a ticker for {company_name}.")
# Initialize the scheduler
scheduler = AsyncIOScheduler()
scheduler.add_job(send_daily_alerts, 'cron', day_of_week='mon-fri', hour=6, minute=30)  # Adjust timezone if necessary
scheduler.start()  # Start the scheduler

# Run the bot
bot.run(TOKEN)
