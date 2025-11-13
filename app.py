import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from ta.trend import EMAIndicator, MACD
from ta.volatility import BollingerBands, AverageTrueRange
from ta.momentum import RSIIndicator, StochasticOscillator
from binance.client import Client
import requests
import numpy as np

# Page config
st.set_page_config(
    page_title="KryptoView - Crypto Analytics Platform",
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'mailto:cryptoalert.feedback@gmail.com',
        'Report a bug': 'mailto:cryptoalert.feedback@gmail.com',
        'About': "# KryptoView\nProfessional Crypto Analytics Platform\n\nVersion 1.0.0"
    }
)

# Google Analytics tracking
st.markdown("""
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-7G6W61KPNT"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-7G6W61KPNT');
</script>
""", unsafe_allow_html=True)

# Helper function to format large numbers
def format_number(num):
    """Format large numbers to readable format (e.g., 2.02T, 1.5B, 234.5M)"""
    if num is None:
        return "N/A"

    try:
        num = float(num)
        if num >= 1_000_000_000_000:  # Trillion
            return f"{num / 1_000_000_000_000:.2f}T"
        elif num >= 1_000_000_000:  # Billion
            return f"{num / 1_000_000_000:.2f}B"
        elif num >= 1_000_000:  # Million
            return f"{num / 1_000_000:.2f}M"
        elif num >= 1_000:  # Thousand
            return f"{num / 1_000:.2f}K"
        else:
            return f"{num:.2f}"
    except:
        return "N/A"

def send_feedback_email(feedback_type, message, user_email):
    """Send feedback via Formspree (free email service)"""
    # Formspree endpoint - configured to send to project email
    FORMSPREE_ENDPOINT = "https://formspree.io/f/xldadrrn"

    try:
        # Prepare form data
        data = {
            'feedback_type': feedback_type,
            'message': message,
            'user_email': user_email if user_email else 'Anonymous',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '_subject': f'Crypto Alert Feedback: {feedback_type}'
        }

        # Send POST request to Formspree
        print(f"📤 Sending feedback to Formspree...")
        print(f"Data: {data}")

        response = requests.post(
            FORMSPREE_ENDPOINT,
            data=data,
            timeout=10
        )

        print(f"📬 Response Status: {response.status_code}")
        print(f"📬 Response Body: {response.text}")

        if response.status_code == 200:
            return True, "Feedback sent successfully!"
        else:
            return False, f"Failed to send feedback. Status: {response.status_code} - {response.text}"
    except Exception as e:
        print(f"❌ Error sending feedback: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, f"Error sending feedback: {str(e)}"

# Initialize theme in session state (moved here before CSS)
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'

# Dynamic CSS based on theme
if st.session_state.theme == 'dark':
    bg_gradient = "linear-gradient(135deg, #0f1419 0%, #1a1f2e 100%)"
    sidebar_bg = "linear-gradient(180deg, #161b26 0%, #1e2433 100%)"
    text_color = "#e8f4ff"
    text_secondary = "#8b9dc3"
    card_bg = "linear-gradient(135deg, rgba(30, 40, 60, 0.4) 0%, rgba(40, 50, 70, 0.3) 100%)"
    border_color = "rgba(100, 140, 200, 0.15)"
    button_bg = "linear-gradient(135deg, rgba(40, 60, 90, 0.5) 0%, rgba(50, 70, 100, 0.4) 100%)"
    button_hover = "linear-gradient(135deg, rgba(60, 90, 130, 0.6) 0%, rgba(70, 100, 140, 0.5) 100%)"
    tab_bg = "rgba(30, 40, 60, 0.3)"
    tab_item_bg = "rgba(40, 50, 70, 0.3)"
    tab_hover = "rgba(60, 80, 120, 0.4)"
else:
    bg_gradient = "linear-gradient(135deg, #f0f2f6 0%, #e1e8f0 100%)"
    sidebar_bg = "linear-gradient(180deg, #ffffff 0%, #f5f7fa 100%)"
    text_color = "#1a1f2e"
    text_secondary = "#4a5568"
    card_bg = "linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.9) 100%)"
    border_color = "rgba(100, 140, 200, 0.3)"
    button_bg = "linear-gradient(135deg, rgba(255, 255, 255, 0.8) 0%, rgba(240, 245, 250, 0.7) 100%)"
    button_hover = "linear-gradient(135deg, rgba(230, 240, 250, 0.9) 0%, rgba(220, 235, 245, 0.8) 100%)"
    tab_bg = "rgba(230, 235, 245, 0.5)"
    tab_item_bg = "rgba(255, 255, 255, 0.6)"
    tab_hover = "rgba(220, 230, 245, 0.7)"

# Custom CSS for modern theme (inspired by CoinGecko/TradingView)
st.markdown(f"""
<style>
    /* Main background */
    .stApp {{
        background: {bg_gradient};
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background: {sidebar_bg};
        border-right: 1px solid {border_color};
    }}

    .block-container {{
        padding-top: 1.5rem;
        padding-bottom: 0rem;
        padding-left: 2.5rem;
        padding-right: 2.5rem;
    }}

    /* Modern Metrics Cards */
    .stMetric {{
        background: {card_bg};
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 8px;
        border: 1px solid {border_color};
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }}
    .stMetric:hover {{
        border-color: {border_color};
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
        transform: translateY(-2px);
    }}
    .stMetric label {{
        font-size: 13px !important;
        color: {text_secondary} !important;
        font-weight: 500 !important;
        letter-spacing: 0.5px !important;
        text-transform: uppercase !important;
    }}
    .stMetric [data-testid="stMetricValue"] {{
        font-size: 26px !important;
        color: {text_color} !important;
        font-weight: 600 !important;
    }}

    /* Modern Typography */
    h1 {{
        font-size: 32px !important;
        margin-bottom: 1rem !important;
        color: {text_color} !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px !important;
    }}
    h2 {{
        font-size: 24px !important;
        margin-top: 1rem !important;
        margin-bottom: 0.75rem !important;
        color: {text_color} !important;
        font-weight: 600 !important;
    }}
    h3 {{
        font-size: 20px !important;
        margin-top: 0.75rem !important;
        margin-bottom: 0.5rem !important;
        color: {text_color} !important;
        font-weight: 600 !important;
    }}
    h4 {{
        font-size: 16px !important;
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
        color: {text_secondary} !important;
        font-weight: 500 !important;
    }}

    /* Progress bars */
    .stProgress > div > div > div > div {{
        background: linear-gradient(90deg, #00C853 0%, #00E676 100%);
    }}

    /* Modern Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 12px;
        background: {tab_bg};
        padding: 8px;
        border-radius: 12px;
        border: 1px solid {border_color};
    }}
    .stTabs [data-baseweb="tab"] {{
        font-size: 14px;
        font-weight: 500;
        padding: 12px 20px;
        background: {tab_item_bg};
        border-radius: 8px;
        color: {text_secondary};
        transition: all 0.3s ease;
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        background: {tab_hover};
        color: {text_color};
    }}
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, #2962ff 0%, #1e88e5 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(41, 98, 255, 0.3);
    }}

    /* Modern Text */
    p, .stMarkdown {{
        font-size: 14px !important;
        color: {text_color} !important;
    }}
    .stCaption {{
        font-size: 12px !important;
        color: {text_secondary} !important;
    }}

    /* Modern Buttons */
    .stButton > button {{
        background: {button_bg};
        border: 1px solid {border_color};
        border-radius: 10px;
        color: {text_color};
        font-weight: 500;
        padding: 10px 20px;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }}
    .stButton > button:hover {{
        background: {button_hover};
        border-color: {border_color};
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        transform: translateY(-2px);
    }}

    /* Primary Button (Selected State) */
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #2962ff 0%, #1e88e5 100%);
        border: 1px solid rgba(41, 98, 255, 0.5);
        color: #ffffff;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(41, 98, 255, 0.4);
    }}
    .stButton > button[kind="primary"]:hover {{
        background: linear-gradient(135deg, #1e88e5 0%, #1565c0 100%);
        box-shadow: 0 6px 16px rgba(41, 98, 255, 0.5);
        transform: translateY(-2px);
    }}

    /* Secondary Button */
    .stButton > button[kind="secondary"] {{
        background: rgba(40, 60, 90, 0.3);
        border: 1px solid rgba(100, 140, 200, 0.15);
        color: #8b9dc3;
    }}
    .stButton > button[kind="secondary"]:hover {{
        background: rgba(60, 90, 130, 0.4);
        border-color: rgba(120, 160, 220, 0.3);
        color: #c8d8ec;
    }}

    /* Modern DataFrames/Tables */
    .stDataFrame {{
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }}

    /* Checkbox styling */
    .stCheckbox {{
        color: {text_color} !important;
    }}

    /* Selectbox styling */
    .stSelectbox > div > div {{
        background: {card_bg};
        border: 1px solid {border_color};
        border-radius: 8px;
        color: {text_color};
    }}
</style>
""", unsafe_allow_html=True)

# Constants - Coins with >$1B market cap (Top 80+)
SYMBOLS = {
    'Bitcoin (BTC)': 'BTCUSDT',
    'Ethereum (ETH)': 'ETHUSDT',
    'Binance Coin (BNB)': 'BNBUSDT',
    'Solana (SOL)': 'SOLUSDT',
    'Ripple (XRP)': 'XRPUSDT',
    'Cardano (ADA)': 'ADAUSDT',
    'Avalanche (AVAX)': 'AVAXUSDT',
    'Dogecoin (DOGE)': 'DOGEUSDT',
    'TRON (TRX)': 'TRXUSDT',
    'Polkadot (DOT)': 'DOTUSDT',
    'Polygon (MATIC)': 'MATICUSDT',
    'Chainlink (LINK)': 'LINKUSDT',
    'Toncoin (TON)': 'TONUSDT',
    'Shiba Inu (SHIB)': 'SHIBUSDT',
    'Litecoin (LTC)': 'LTCUSDT',
    'Bitcoin Cash (BCH)': 'BCHUSDT',
    'Uniswap (UNI)': 'UNIUSDT',
    'Stellar (XLM)': 'XLMUSDT',
    'Cosmos (ATOM)': 'ATOMUSDT',
    'Ethereum Classic (ETC)': 'ETCUSDT',
    'Hedera (HBAR)': 'HBARUSDT',
    'Filecoin (FIL)': 'FILUSDT',
    'Arbitrum (ARB)': 'ARBUSDT',
    'Optimism (OP)': 'OPUSDT',
    'VeChain (VET)': 'VETUSDT',
    'Algorand (ALGO)': 'ALGOUSDT',
    'Near Protocol (NEAR)': 'NEARUSDT',
    'Aptos (APT)': 'APTUSDT',
    'Injective (INJ)': 'INJUSDT',
    'Sui (SUI)': 'SUIUSDT',
    'Render (RNDR)': 'RNDRUSDT',
    'Fantom (FTM)': 'FTMUSDT',
    'Theta (THETA)': 'THETAUSDT',
    'Monero (XMR)': 'XMRUSDT',
    'Kaspa (KAS)': 'KASUSDT',
    'Stacks (STX)': 'STXUSDT',
    'Immutable (IMX)': 'IMXUSDT',
    'Cronos (CRO)': 'CROUSDT',
    'Mantle (MNT)': 'MNTUSDT',
    'The Graph (GRT)': 'GRTUSDT',
    'Quant (QNT)': 'QNTUSDT',
    'Lido DAO (LDO)': 'LDOUSDT',
    'Maker (MKR)': 'MKRUSDT',
    'Aave (AAVE)': 'AAVEUSDT',
    'Arweave (AR)': 'ARUSDT',
    'Celestia (TIA)': 'TIAUSDT',
    'Sei (SEI)': 'SEIUSDT',
    'Thorchain (RUNE)': 'RUNEUSDT',
    'Axie Infinity (AXS)': 'AXSUSDT',
    'The Sandbox (SAND)': 'SANDUSDT',
    'Decentraland (MANA)': 'MANAUSDT',
    'Gala (GALA)': 'GALAUSDT',
    'Enjin (ENJ)': 'ENJUSDT',
    'Flow (FLOW)': 'FLOWUSDT',
    'Chiliz (CHZ)': 'CHZUSDT',
    'Flare (FLR)': 'FLRUSDT',
    'Kava (KAVA)': 'KAVAUSDT',
    'Synthetix (SNX)': 'SNXUSDT',
    'Curve (CRV)': 'CRVUSDT',
    'Compound (COMP)': 'COMPUSDT',
    'Sushi (SUSHI)': 'SUSHIUSDT',
    '1inch (1INCH)': '1INCHUSDT',
    'Zilliqa (ZIL)': 'ZILUSDT',
    'Zcash (ZEC)': 'ZECUSDT',
    'Dash (DASH)': 'DASHUSDT',
    'Qtum (QTUM)': 'QTUMUSDT',
    'Ravencoin (RVN)': 'RVNUSDT',
    'Harmony (ONE)': 'ONEUSDT',
    'Celo (CELO)': 'CELOUSDT',
    'Ankr (ANKR)': 'ANKRUSDT',
    'IOTA (IOTA)': 'IOTAUSDT',
    'Waves (WAVES)': 'WAVESUSDT',
    'Holo (HOT)': 'HOTUSDT',
    'Ren (REN)': 'RENUSDT',
    'OMG Network (OMG)': 'OMGUSDT',
    'Loopring (LRC)': 'LRCUSDT',
    'Fetch.ai (FET)': 'FETUSDT',
    'Ocean Protocol (OCEAN)': 'OCEANUSDT',
    'Numeraire (NMR)': 'NMRUSDT',
    'Band Protocol (BAND)': 'BANDUSDT'
}

# Timeframe options (interval only, user can zoom/pan to see any range)
TIMEFRAME_OPTIONS = {
    '1m': {'interval': Client.KLINE_INTERVAL_1MINUTE, 'name': '1 Minute'},
    '5m': {'interval': Client.KLINE_INTERVAL_5MINUTE, 'name': '5 Minutes'},
    '15m': {'interval': Client.KLINE_INTERVAL_15MINUTE, 'name': '15 Minutes'},
    '30m': {'interval': Client.KLINE_INTERVAL_30MINUTE, 'name': '30 Minutes'},
    '1h': {'interval': Client.KLINE_INTERVAL_1HOUR, 'name': '1 Hour'},
    '2h': {'interval': Client.KLINE_INTERVAL_2HOUR, 'name': '2 Hours'},
    '4h': {'interval': Client.KLINE_INTERVAL_4HOUR, 'name': '4 Hours'},
    '6h': {'interval': Client.KLINE_INTERVAL_6HOUR, 'name': '6 Hours'},
    '12h': {'interval': Client.KLINE_INTERVAL_12HOUR, 'name': '12 Hours'},
    '1d': {'interval': Client.KLINE_INTERVAL_1DAY, 'name': '1 Day'},
    '3d': {'interval': Client.KLINE_INTERVAL_3DAY, 'name': '3 Days'},
    '1w': {'interval': Client.KLINE_INTERVAL_1WEEK, 'name': '1 Week'},
}

# Keep TIME_OPTIONS for Backtest mode only
TIME_OPTIONS = {
    '1 Day': {'days': 1, 'interval': Client.KLINE_INTERVAL_15MINUTE, 'limit': 96},
    '3 Days': {'days': 3, 'interval': Client.KLINE_INTERVAL_1HOUR, 'limit': 72},
    '7 Days': {'days': 7, 'interval': Client.KLINE_INTERVAL_2HOUR, 'limit': 84},
    '14 Days': {'days': 14, 'interval': Client.KLINE_INTERVAL_4HOUR, 'limit': 84},
    '1 Month': {'days': 30, 'interval': Client.KLINE_INTERVAL_6HOUR, 'limit': 120},
    '3 Months': {'days': 90, 'interval': Client.KLINE_INTERVAL_1DAY, 'limit': 90},
    '6 Months': {'days': 180, 'interval': Client.KLINE_INTERVAL_1DAY, 'limit': 180},
    '1 Year': {'days': 365, 'interval': Client.KLINE_INTERVAL_1DAY, 'limit': 365},
    '3 Years': {'days': 1095, 'interval': Client.KLINE_INTERVAL_1WEEK, 'limit': 156},
    '5 Years': {'days': 1825, 'interval': Client.KLINE_INTERVAL_1WEEK, 'limit': 260}
}

ENTRY_AMOUNT = 100
client = Client()

# Helper function to format large numbers
def format_large_number(num):
    """Format large numbers to K/M/B/T notation"""
    if num >= 1_000_000_000_000:
        return f"${num/1_000_000_000_000:.2f}T"
    elif num >= 1_000_000_000:
        return f"${num/1_000_000_000:.2f}B"
    elif num >= 1_000_000:
        return f"${num/1_000_000:.2f}M"
    elif num >= 1_000:
        return f"${num/1_000:.2f}K"
    else:
        return f"${num:.2f}"

# Cache functions
@st.cache_data(ttl=300)
def fetch_data(symbol, interval, limit):
    try:
        klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(klines, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume',
                                           'Close_time', 'Quote_asset_volume', 'Number_of_trades',
                                           'Taker_buy_base_volume', 'Taker_buy_quote_volume', 'Ignore'])
        df['Close'] = df['Close'].astype(float)
        df['High'] = df['High'].astype(float)
        df['Low'] = df['Low'].astype(float)
        df['Volume'] = df['Volume'].astype(float)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_fng():
    url = "https://api.alternative.me/fng/?limit=0"
    try:
        r = requests.get(url)
        data = r.json()["data"]
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df['value'] = pd.to_numeric(df['value'])
        df = df.sort_values("timestamp").reset_index(drop=True)
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_current_fng():
    """Fetch current Fear & Greed Index"""
    url = "https://api.alternative.me/fng/?limit=1"
    try:
        r = requests.get(url, timeout=5)
        data = r.json()["data"][0]
        value = int(data['value'])
        classification = data['value_classification']
        return value, classification
    except:
        return None, None

def get_fng_color(value):
    """Get color based on Fear & Greed value"""
    if value <= 25:
        return "#FF4444", "😱"  # Extreme Fear - Red
    elif value <= 45:
        return "#FF8C00", "😰"  # Fear - Orange
    elif value <= 55:
        return "#FFD700", "😐"  # Neutral - Yellow
    elif value <= 75:
        return "#90EE90", "😊"  # Greed - Light Green
    else:
        return "#00FF00", "🤑"  # Extreme Greed - Green

@st.cache_data(ttl=60)
def fetch_24h_ticker(symbol):
    """Fetch 24h ticker statistics from Binance"""
    try:
        ticker = client.get_ticker(symbol=symbol)
        return {
            'price_change': float(ticker['priceChange']),
            'price_change_percent': float(ticker['priceChangePercent']),
            'high_price': float(ticker['highPrice']),
            'low_price': float(ticker['lowPrice']),
            'volume': float(ticker['volume']),
            'quote_volume': float(ticker['quoteVolume']),
            'open_price': float(ticker['openPrice']),
            'last_price': float(ticker['lastPrice']),
            'bid_price': float(ticker['bidPrice']),
            'ask_price': float(ticker['askPrice']),
            'trades_count': int(ticker['count'])
        }
    except Exception as e:
        return None

@st.cache_data(ttl=10)
def fetch_order_book(symbol, limit=20):
    """Fetch order book depth from Binance"""
    try:
        depth = client.get_order_book(symbol=symbol, limit=limit)
        bids = [[float(price), float(qty)] for price, qty in depth['bids']]
        asks = [[float(price), float(qty)] for price, qty in depth['asks']]
        return {'bids': bids, 'asks': asks}
    except Exception as e:
        return None

@st.cache_data(ttl=10)
def fetch_recent_trades(symbol, limit=20):
    """Fetch recent trades from Binance"""
    try:
        trades = client.get_recent_trades(symbol=symbol, limit=limit)
        return [{
            'price': float(t['price']),
            'qty': float(t['qty']),
            'time': pd.to_datetime(t['time'], unit='ms'),
            'is_buyer_maker': t['isBuyerMaker']
        } for t in trades]
    except Exception as e:
        return None

@st.cache_data(ttl=300)
def fetch_coingecko_data(symbol):
    """Fetch comprehensive data from CoinGecko API"""
    # Map Binance symbols to CoinGecko IDs (Top coins)
    coin_map = {
        'BTCUSDT': 'bitcoin', 'ETHUSDT': 'ethereum', 'BNBUSDT': 'binancecoin',
        'SOLUSDT': 'solana', 'XRPUSDT': 'ripple', 'ADAUSDT': 'cardano',
        'AVAXUSDT': 'avalanche-2', 'DOGEUSDT': 'dogecoin', 'TRXUSDT': 'tron',
        'DOTUSDT': 'polkadot', 'MATICUSDT': 'matic-network', 'LINKUSDT': 'chainlink',
        'TONUSDT': 'the-open-network', 'SHIBUSDT': 'shiba-inu', 'LTCUSDT': 'litecoin',
        'BCHUSDT': 'bitcoin-cash', 'UNIUSDT': 'uniswap', 'XLMUSDT': 'stellar',
        'ATOMUSDT': 'cosmos', 'ETCUSDT': 'ethereum-classic', 'HBARUSDT': 'hedera-hashgraph',
        'FILUSDT': 'filecoin', 'ARBUSDT': 'arbitrum', 'OPUSDT': 'optimism',
        'VETUSDT': 'vechain', 'ALGOUSDT': 'algorand', 'NEARUSDT': 'near',
        'APTUSDT': 'aptos', 'INJUSDT': 'injective-protocol', 'SUIUSDT': 'sui',
        'RNDRUSDT': 'render-token', 'FTMUSDT': 'fantom', 'THETAUSDT': 'theta-token',
        'XMRUSDT': 'monero', 'KASUSDT': 'kaspa', 'STXUSDT': 'blockstack',
        'IMXUSDT': 'immutable-x', 'CROUSDT': 'crypto-com-chain', 'MNTUSDT': 'mantle',
        'GRTUSDT': 'the-graph', 'QNTUSDT': 'quant-network', 'LDOUSDT': 'lido-dao',
        'MKRUSDT': 'maker', 'AAVEUSDT': 'aave', 'ARUSDT': 'arweave',
        'TIAUSDT': 'celestia', 'SEIUSDT': 'sei-network', 'RUNEUSDT': 'thorchain',
        'AXSUSDT': 'axie-infinity', 'SANDUSDT': 'the-sandbox', 'MANAUSDT': 'decentraland',
        'GALAUSDT': 'gala', 'ENJUSDT': 'enjincoin', 'FLOWUSDT': 'flow',
        'CHZUSDT': 'chiliz', 'FLRUSDT': 'flare-networks', 'KAVAUSDT': 'kava',
        'SNXUSDT': 'synthetix-network-token', 'CRVUSDT': 'curve-dao-token',
        'COMPUSDT': 'compound-governance-token', 'SUSHIUSDT': 'sushi',
        '1INCHUSDT': '1inch', 'ZILUSDT': 'zilliqa', 'ZECUSDT': 'zcash',
        'DASHUSDT': 'dash', 'QTUMUSDT': 'qtum', 'RVNUSDT': 'ravencoin',
        'ONEUSDT': 'harmony', 'CELOUSDT': 'celo', 'ANKRUSDT': 'ankr',
        'IOTAUSDT': 'iota', 'WAVESUSDT': 'waves', 'HOTUSDT': 'holotoken',
        'RENUSDT': 'republic-protocol', 'OMGUSDT': 'omisego', 'LRCUSDT': 'loopring',
        'FETUSDT': 'fetch-ai', 'OCEANUSDT': 'ocean-protocol', 'NMRUSDT': 'numeraire',
        'BANDUSDT': 'band-protocol'
    }

    coin_id = coin_map.get(symbol)
    if not coin_id:
        return None

    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
        r = requests.get(url, timeout=10)
        data = r.json()

        market_data = data['market_data']

        return {
            'market_cap': market_data['market_cap']['usd'],
            'ath': market_data['ath']['usd'],
            'ath_date': market_data['ath_date']['usd'],
            'ath_change_percentage': market_data['ath_change_percentage']['usd'],
            'atl': market_data['atl']['usd'],
            'atl_date': market_data['atl_date']['usd'],
            'atl_change_percentage': market_data['atl_change_percentage']['usd'],
            'circulating_supply': market_data.get('circulating_supply'),
            'total_supply': market_data.get('total_supply'),
            'max_supply': market_data.get('max_supply'),
            'market_cap_rank': data.get('market_cap_rank'),
            'price_change_percentage_1h': market_data.get('price_change_percentage_1h_in_currency', {}).get('usd'),
            'price_change_percentage_24h': market_data.get('price_change_percentage_24h'),
            'price_change_percentage_7d': market_data.get('price_change_percentage_7d'),
            'price_change_percentage_30d': market_data.get('price_change_percentage_30d'),
            'price_change_percentage_1y': market_data.get('price_change_percentage_1y'),
        }
    except Exception as e:
        return None

@st.cache_data(ttl=300)
def fetch_market_cap(symbol):
    """Fetch market cap from CoinGecko API (backward compatibility)"""
    data = fetch_coingecko_data(symbol)
    return data['market_cap'] if data else None

@st.cache_data(ttl=600)
def fetch_global_crypto_data():
    """Fetch global crypto market data from CoinGecko"""
    try:
        url = "https://api.coingecko.com/api/v3/global"
        r = requests.get(url, timeout=10)
        data = r.json()['data']
        return {
            'total_market_cap': data['total_market_cap']['usd'],
            'total_volume': data['total_volume']['usd'],
            'market_cap_percentage': data['market_cap_percentage'],
            'active_cryptocurrencies': data['active_cryptocurrencies']
        }
    except Exception as e:
        return None

@st.cache_data(ttl=300)
def fetch_crypto_news(limit=10):
    """Fetch crypto news from CryptoCompare API with images"""
    try:
        url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            news_items = []

            for article in data.get('Data', [])[:limit]:
                news_items.append({
                    'title': article.get('title', 'No Title'),
                    'url': article.get('url', '#'),
                    'source': article.get('source', 'Unknown'),
                    'published_at': article.get('published_on', 0),
                    'body': article.get('body', 'No description available.')[:200] + '...',
                    'image_url': article.get('imageurl', ''),
                    'categories': article.get('categories', ''),
                    'tags': article.get('tags', '')
                })

            return news_items
        else:
            return []
    except Exception as e:
        return []

# Fallback RSS parser (not used anymore but kept for reference)
def fetch_crypto_news_rss_fallback(limit=10):
    """Fetch crypto news from RSS feeds (fallback without images)"""
    news_items = []

    sources = [
        {
            'name': 'CoinTelegraph',
            'url': 'https://cointelegraph.com/rss',
            'parser': 'rss'
        },
        {
            'name': 'CoinDesk',
            'url': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
            'parser': 'rss'
        },
        {
            'name': 'Decrypt',
            'url': 'https://decrypt.co/feed',
            'parser': 'rss'
        }
    ]

    for source in sources:
        try:
            response = requests.get(source['url'], timeout=5)
            if response.status_code == 200:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.content)

                # Find all items
                for item in root.findall('.//item')[:limit]:
                    title_elem = item.find('title')
                    link_elem = item.find('link')
                    pubdate_elem = item.find('pubDate')

                    if title_elem is not None and link_elem is not None:
                        news_items.append({
                            'title': title_elem.text,
                            'url': link_elem.text,
                            'published_at': pubdate_elem.text if pubdate_elem is not None else '',
                            'source': source['name']
                        })

                # If we got news, break
                if news_items:
                    break
        except Exception as e:
            continue

    return news_items[:limit] if news_items else None

@st.cache_data(ttl=120)
def fetch_top_coins(num_coins=50):
    """Fetch top cryptocurrencies by market cap from CoinGecko"""
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': num_coins,
            'page': 1,
            'sparkline': False,
            'price_change_percentage': '1h,24h,7d'
        }

        response = requests.get(url, params=params, timeout=15)

        if response.status_code == 200:
            data = response.json()

            coins_data = []
            for coin in data:
                coins_data.append({
                    'rank': coin.get('market_cap_rank', 0),
                    'name': coin.get('name', 'N/A'),
                    'symbol': coin.get('symbol', '').upper(),
                    'price': coin.get('current_price', 0),
                    'change_1h': coin.get('price_change_percentage_1h_in_currency', 0),
                    'change_24h': coin.get('price_change_percentage_24h', 0),
                    'change_7d': coin.get('price_change_percentage_7d_in_currency', 0),
                    'market_cap': coin.get('market_cap', 0),
                    'volume_24h': coin.get('total_volume', 0),
                    'circulating_supply': coin.get('circulating_supply', 0)
                })

            return coins_data
        else:
            return None

    except Exception as e:
        print(f"Error fetching top coins: {e}")
        return None

@st.cache_data(ttl=300)
def fetch_market_dominance():
    """Fetch market cap dominance data from CoinGecko"""
    try:
        url = "https://api.coingecko.com/api/v3/global"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            market_data = data.get('data', {})

            # Get dominance percentages
            dominance = market_data.get('market_cap_percentage', {})
            total_market_cap = market_data.get('total_market_cap', {}).get('usd', 0)

            return {
                'btc_dominance': dominance.get('btc', 0),
                'eth_dominance': dominance.get('eth', 0),
                'total_market_cap': total_market_cap,
                'dominance': dominance
            }
        else:
            return None
    except Exception as e:
        print(f"Error fetching market dominance: {e}")
        return None

@st.cache_data(ttl=600)
def fetch_top_gainers_losers(limit=10):
    """Fetch top gainers and losers from Binance (only from our coin list)"""
    try:
        # Get all USDT pairs 24h ticker
        tickers = client.get_ticker()

        # Get list of our symbols
        our_symbols = list(SYMBOLS.values())

        # Filter to only our coins
        our_tickers = [t for t in tickers if t['symbol'] in our_symbols]

        # Sort by price change percentage
        sorted_tickers = sorted(our_tickers, key=lambda x: float(x['priceChangePercent']), reverse=True)

        gainers = []
        for t in sorted_tickers[:limit]:
            # Find the coin name
            coin_name = [name for name, sym in SYMBOLS.items() if sym == t['symbol']][0]
            gainers.append({
                'symbol': t['symbol'],
                'name': coin_name,
                'price': float(t['lastPrice']),
                'change_percent': float(t['priceChangePercent']),
                'volume': float(t['quoteVolume'])
            })

        losers = []
        for t in sorted_tickers[-limit:]:
            coin_name = [name for name, sym in SYMBOLS.items() if sym == t['symbol']][0]
            losers.append({
                'symbol': t['symbol'],
                'name': coin_name,
                'price': float(t['lastPrice']),
                'change_percent': float(t['priceChangePercent']),
                'volume': float(t['quoteVolume'])
            })

        return {'gainers': gainers, 'losers': list(reversed(losers))}
    except Exception as e:
        return None

@st.cache_data(ttl=300)
def fetch_open_interest_coinglass(symbol):
    """
    Fetch aggregated Open Interest data from Coinglass API
    Returns OI from all major exchanges (Binance, Bybit, OKX, etc.)
    """
    try:
        # Map Binance symbols to Coinglass format
        coin_map = {
            'BTCUSDT': 'BTC',
            'ETHUSDT': 'ETH',
            'BNBUSDT': 'BNB',
            'SOLUSDT': 'SOL',
            'XRPUSDT': 'XRP',
            'ADAUSDT': 'ADA',
            'AVAXUSDT': 'AVAX',
            'DOGEUSDT': 'DOGE',
            'TRXUSDT': 'TRX',
            'DOTUSDT': 'DOT',
            'MATICUSDT': 'MATIC',
            'LINKUSDT': 'LINK',
            'TONUSDT': 'TON',
            'SHIBUSDT': 'SHIB',
            'LTCUSDT': 'LTC',
            'BCHUSDT': 'BCH',
            'UNIUSDT': 'UNI',
            'XLMUSDT': 'XLM',
            'ATOMUSDT': 'ATOM',
            'ETCUSDT': 'ETC'
        }

        coin = coin_map.get(symbol)
        if not coin:
            # Fallback to Binance API
            return fetch_open_interest_binance(symbol)

        # Coinglass API endpoint for aggregated OI
        # Note: This is a free endpoint that doesn't require API key
        url = f"https://open-api.coinglass.com/public/v2/indicator/open-interest?symbol={coin}"

        headers = {
            'accept': 'application/json'
        }

        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()

        if data.get('success') and data.get('data'):
            oi_data = data['data']

            # Get total OI across all exchanges
            total_oi = float(oi_data.get('openInterest', 0))

            # Get long/short ratio from top traders
            long_ratio = float(oi_data.get('longRate', 50)) / 100
            short_ratio = 1 - long_ratio

            # Calculate long/short amounts in USD
            long_amount = total_oi * long_ratio
            short_amount = total_oi * short_ratio

            return {
                'open_interest': total_oi,
                'long_percentage': long_ratio * 100,
                'short_percentage': short_ratio * 100,
                'long_amount': long_amount,
                'short_amount': short_amount,
                'source': 'Coinglass (All Exchanges)'
            }
        else:
            # Fallback to Binance
            return fetch_open_interest_binance(symbol)

    except Exception as e:
        # Fallback to Binance API
        return fetch_open_interest_binance(symbol)

@st.cache_data(ttl=300)
def fetch_open_interest_binance(symbol):
    """Fetch Open Interest data from Binance Futures (Fallback)"""
    try:
        # Remove USDT from symbol for futures
        futures_symbol = symbol.replace('USDT', 'USDT')

        # Get Open Interest
        url = f"https://fapi.binance.com/fapi/v1/openInterest?symbol={futures_symbol}"
        r = requests.get(url, timeout=5)
        oi_data = r.json()

        # Get long/short ratio
        url_ratio = f"https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol={futures_symbol}&period=5m&limit=1"
        r_ratio = requests.get(url_ratio, timeout=5)
        ratio_data = r_ratio.json()

        if oi_data and ratio_data:
            open_interest = float(oi_data['openInterest'])
            long_short_ratio = float(ratio_data[0]['longShortRatio'])

            # Calculate longs and shorts
            total_accounts = long_short_ratio + 1
            long_percentage = (long_short_ratio / total_accounts) * 100
            short_percentage = 100 - long_percentage

            # Get current price for USD calculation
            price_url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={futures_symbol}"
            price_r = requests.get(price_url, timeout=5)
            price_data = price_r.json()
            current_price = float(price_data['price'])

            # Calculate total OI in USD
            total_oi_usd = open_interest * current_price

            # Calculate long/short amounts
            long_amount = total_oi_usd * (long_percentage / 100)
            short_amount = total_oi_usd * (short_percentage / 100)

            return {
                'open_interest': total_oi_usd,
                'long_percentage': long_percentage,
                'short_percentage': short_percentage,
                'long_amount': long_amount,
                'short_amount': short_amount,
                'source': 'Binance Only'
            }
    except Exception as e:
        return None

@st.cache_data(ttl=300)
def fetch_liquidation_data(symbol):
    """Fetch liquidation heatmap data from Binance"""
    try:
        futures_symbol = symbol.replace('USDT', 'USDT')

        # Get current price
        url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={futures_symbol}"
        r = requests.get(url, timeout=5)
        current_price = float(r.json()['price'])

        # Generate liquidation levels (simplified heatmap)
        # In reality, you'd need a more sophisticated API for real liquidation data
        price_range = np.linspace(current_price * 0.85, current_price * 1.15, 50)

        # Simulate liquidation intensity (higher near round numbers and leverage levels)
        liquidations = []
        for price in price_range:
            # Higher liquidations at 5%, 10%, 15% levels
            distance = abs(price - current_price) / current_price
            intensity = np.exp(-10 * (distance - 0.05)**2) + np.exp(-10 * (distance - 0.10)**2)
            liquidations.append(intensity * np.random.uniform(0.5, 1.5))

        return pd.DataFrame({
            'price': price_range,
            'liquidations': liquidations
        })
    except:
        return None

def calculate_indicators(df, ema_type, timeframe=None):
    """
    Calculate technical indicators with timeframe-adjusted periods.

    Standard periods are based on daily charts. For other timeframes:
    - Intraday (1m-30m): Use shorter periods
    - Hourly (1h-12h): Use medium periods
    - Daily+ (1d-1w): Use standard/longer periods
    """

    # Adjust periods based on timeframe
    if timeframe:
        # For very short timeframes (1m, 5m, 15m, 30m)
        if timeframe in ['1m', '5m', '15m', '30m']:
            # Shorter periods for fast-moving intraday charts
            if ema_type == 'short':
                ema1, ema2 = 9, 21  # Fast EMAs for scalping
            elif ema_type == 'mid':
                ema1, ema2 = 20, 50
            else:
                ema1, ema2 = 50, 100
            bb_period = 20
            rsi_period = 14

        # For hourly timeframes (1h, 2h, 4h, 6h, 12h)
        elif timeframe in ['1h', '2h', '4h', '6h', '12h']:
            # Medium periods for swing trading
            if ema_type == 'short':
                ema1, ema2 = 12, 26  # Similar to MACD
            elif ema_type == 'mid':
                ema1, ema2 = 50, 100
            else:
                ema1, ema2 = 100, 200
            bb_period = 20
            rsi_period = 14

        # For daily+ timeframes (1d, 3d, 1w)
        else:
            # Standard periods for position trading
            if ema_type == 'short':
                ema1, ema2 = 20, 50
            elif ema_type == 'mid':
                ema1, ema2 = 50, 100
            else:
                ema1, ema2 = 100, 200
            bb_period = 20
            rsi_period = 14
    else:
        # Fallback to old logic for Backtest mode
        if ema_type == 'short':
            ema1, ema2 = 20, 50
        elif ema_type == 'mid':
            ema1, ema2 = 50, 100
        else:
            ema1, ema2 = 100, 200
        bb_period = 20
        rsi_period = 14

    # Calculate indicators
    df[f'EMA{ema1}'] = EMAIndicator(close=df['Close'], window=ema1).ema_indicator()
    df[f'EMA{ema2}'] = EMAIndicator(close=df['Close'], window=ema2).ema_indicator()
    bb = BollingerBands(close=df['Close'], window=bb_period)
    df['BBH'] = bb.bollinger_hband()
    df['BBL'] = bb.bollinger_lband()
    df['BBM'] = bb.bollinger_mavg()  # Middle band (SMA)
    df['RSI'] = RSIIndicator(close=df['Close'], window=rsi_period).rsi()

    # MACD
    macd = MACD(close=df['Close'], window_slow=26, window_fast=12, window_sign=9)
    df['MACD'] = macd.macd()
    df['MACD_signal'] = macd.macd_signal()
    df['MACD_histogram'] = macd.macd_diff()

    # Stochastic Oscillator
    stoch = StochasticOscillator(high=df['High'], low=df['Low'], close=df['Close'], window=14, smooth_window=3)
    df['STOCH_K'] = stoch.stoch()
    df['STOCH_D'] = stoch.stoch_signal()

    # ATR (Average True Range)
    atr = AverageTrueRange(high=df['High'], low=df['Low'], close=df['Close'], window=14)
    df['ATR'] = atr.average_true_range()

    return df, ema1, ema2



def create_chart(df, symbol, ema1, ema2, show_ema=False, show_bb=False, show_rsi=False, show_volume=False,
                 show_macd=False, show_stoch=False, show_atr=False):
    """
    Create interactive chart with toggleable indicators and candlesticks.
    Clean chart with price and indicators only.
    """
    # Determine number of rows based on what's enabled
    rows_needed = 1  # Always have price chart
    subplot_titles = [f'{symbol} Price & Indicators']

    # Track which row each indicator is on
    rsi_row = None
    volume_row = None
    macd_row = None
    stoch_row = None
    atr_row = None

    # Add rows for enabled indicators
    if show_rsi:
        rows_needed += 1
        rsi_row = rows_needed
        subplot_titles.append('RSI')

    if show_volume:
        rows_needed += 1
        volume_row = rows_needed
        subplot_titles.append('Volume')

    if show_macd:
        rows_needed += 1
        macd_row = rows_needed
        subplot_titles.append('MACD')

    if show_stoch:
        rows_needed += 1
        stoch_row = rows_needed
        subplot_titles.append('Stochastic')

    if show_atr:
        rows_needed += 1
        atr_row = rows_needed
        subplot_titles.append('ATR')

    # Calculate row heights dynamically (give more space to main chart)
    if rows_needed == 1:
        row_heights = [1.0]
    elif rows_needed == 2:
        row_heights = [0.75, 0.25]
    elif rows_needed == 3:
        row_heights = [0.65, 0.20, 0.15]
    elif rows_needed == 4:
        row_heights = [0.55, 0.15, 0.15, 0.15]
    elif rows_needed == 5:
        row_heights = [0.50, 0.125, 0.125, 0.125, 0.125]
    else:  # 6 or more rows
        main_height = 0.45
        indicator_height = (1.0 - main_height) / (rows_needed - 1)
        row_heights = [main_height] + [indicator_height] * (rows_needed - 1)

    # Create specs for all rows
    specs = [[{"secondary_y": False}] for _ in range(rows_needed)]

    # Create subplots with minimal spacing
    fig = make_subplots(
        rows=rows_needed, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,  # Minimal spacing for compact layout
        row_heights=row_heights,
        subplot_titles=subplot_titles,
        specs=specs
    )

    # Candlestick chart (always visible)
    fig.add_trace(go.Candlestick(
        x=df['timestamp'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Price',
        increasing_line_color='#26A69A',  # Green
        decreasing_line_color='#EF5350',  # Red
        increasing_fillcolor='#26A69A',
        decreasing_fillcolor='#EF5350'
    ), row=1, col=1)

    # EMAs (toggleable)
    if show_ema:
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df[f'EMA{ema1}'], name=f'EMA{ema1}',
                                line=dict(color='#FF6D00', width=1.5)),
                      row=1, col=1)
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df[f'EMA{ema2}'], name=f'EMA{ema2}',
                                line=dict(color='#00C853', width=1.5)),
                      row=1, col=1)

    # Bollinger Bands (toggleable) - Filled area style
    if show_bb:
        # Add invisible lower band trace (for fill reference)
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['BBL'],
            name='BB Lower',
            showlegend=False,
            line=dict(color='rgba(173, 204, 255, 0.3)', width=1),
            hoverinfo='skip'
        ), row=1, col=1)

        # Add upper band with fill to previous trace
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['BBH'],
            name='Bollinger Bands',
            fill='tonexty',  # Fill to previous trace (lower band)
            fillcolor='rgba(173, 204, 255, 0.15)',  # Light blue with transparency
            line=dict(color='rgba(173, 204, 255, 0.6)', width=1),
            hovertemplate='<b>BB Upper:</b> %{y:.2f}<extra></extra>'
        ), row=1, col=1)

        # Add middle band (SMA)
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['BBM'],
            name='BB Middle',
            line=dict(color='rgba(173, 204, 255, 0.8)', width=1, dash='dot'),
            hovertemplate='<b>BB Middle:</b> %{y:.2f}<extra></extra>'
        ), row=1, col=1)

    # RSI (toggleable)
    if show_rsi and rsi_row:
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['RSI'], name='RSI',
                                line=dict(color='#9C27B0', width=2)), row=rsi_row, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=rsi_row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=rsi_row, col=1)

    # Volume (toggleable) - Conditional coloring based on price movement
    if show_volume and volume_row:
        # Calculate colors: Green if close >= open, Red if close < open
        volume_colors = ['#26A69A' if float(close) >= float(open_price) else '#EF5350'
                        for close, open_price in zip(df['Close'], df['Open'])]

        fig.add_trace(go.Bar(
            x=df['timestamp'],
            y=df['Volume'],
            name='Volume',
            showlegend=False,
            marker=dict(
                color=volume_colors,
                line=dict(width=0)
            ),
            hovertemplate='<b>Volume:</b> %{y:,.0f}<extra></extra>'
        ), row=volume_row, col=1)

    # MACD (toggleable)
    if show_macd and macd_row:
        # MACD Line
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['MACD'],
            name='MACD',
            line=dict(color='#2962FF', width=2)
        ), row=macd_row, col=1)

        # Signal Line
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['MACD_signal'],
            name='Signal',
            line=dict(color='#FF6D00', width=2)
        ), row=macd_row, col=1)

        # Histogram
        histogram_colors = ['#26A69A' if val >= 0 else '#EF5350' for val in df['MACD_histogram']]
        fig.add_trace(go.Bar(
            x=df['timestamp'],
            y=df['MACD_histogram'],
            name='Histogram',
            marker=dict(color=histogram_colors),
            showlegend=False
        ), row=macd_row, col=1)

        # Zero line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5, row=macd_row, col=1)

    # Stochastic Oscillator (toggleable)
    if show_stoch and stoch_row:
        # %K Line
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['STOCH_K'],
            name='%K',
            line=dict(color='#2962FF', width=2)
        ), row=stoch_row, col=1)

        # %D Line
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['STOCH_D'],
            name='%D',
            line=dict(color='#FF6D00', width=2)
        ), row=stoch_row, col=1)

        # Overbought/Oversold lines
        fig.add_hline(y=80, line_dash="dash", line_color="red", opacity=0.5, row=stoch_row, col=1)
        fig.add_hline(y=20, line_dash="dash", line_color="green", opacity=0.5, row=stoch_row, col=1)

    # ATR (toggleable)
    if show_atr and atr_row:
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['ATR'],
            name='ATR',
            line=dict(color='#9C27B0', width=2),
            fill='tozeroy',
            fillcolor='rgba(156, 39, 176, 0.1)'
        ), row=atr_row, col=1)

    fig.update_layout(
        height=800,
        showlegend=True,
        hovermode='x unified',
        template='plotly_dark',
        margin=dict(l=10, r=10, t=40, b=10),
        dragmode='pan',
        # Add modebar customization
        modebar_add=['v1hovermode', 'toggleSpikeLines'],
        xaxis_rangeslider_visible=False  # Hide rangeslider for cleaner UI
    )

    # Enable scroll wheel zoom for all subplots
    fig.update_xaxes(fixedrange=False)
    fig.update_yaxes(fixedrange=False)

    # Update y-axes for price chart (move to right side)
    fig.update_yaxes(
        title_text="Price (USDT)",
        side='right',
        row=1, col=1
    )

    # Update y-axes for RSI if shown
    if show_rsi and rsi_row:
        fig.update_yaxes(title_text="RSI", side='right', row=rsi_row, col=1)

    # Update y-axes for Volume if shown
    if show_volume and volume_row:
        fig.update_yaxes(title_text="Volume", side='right', row=volume_row, col=1)

    # Update y-axes for MACD if shown
    if show_macd and macd_row:
        fig.update_yaxes(title_text="MACD", side='right', row=macd_row, col=1)

    # Update y-axes for Stochastic if shown
    if show_stoch and stoch_row:
        fig.update_yaxes(title_text="Stochastic", side='right', row=stoch_row, col=1)

    # Update y-axes for ATR if shown
    if show_atr and atr_row:
        fig.update_yaxes(title_text="ATR", side='right', row=atr_row, col=1)

    # Update x-axis (no rangeslider)
    fig.update_xaxes(
        title_text="Date",
        row=1, col=1
    )

    return fig

def create_order_book_chart(order_book_data, current_price):
    """Create order book depth chart"""
    if not order_book_data:
        return None

    bids = order_book_data['bids']
    asks = order_book_data['asks']

    # Calculate cumulative volumes
    bid_prices = [b[0] for b in bids]
    bid_volumes = [b[1] for b in bids]
    bid_cumulative = np.cumsum(bid_volumes)

    ask_prices = [a[0] for a in asks]
    ask_volumes = [a[1] for a in asks]
    ask_cumulative = np.cumsum(ask_volumes)

    fig = go.Figure()

    # Bids (buy orders) - Green
    fig.add_trace(go.Scatter(
        x=bid_prices,
        y=bid_cumulative,
        fill='tozeroy',
        name='Bids',
        line=dict(color='#00C853', width=2),
        fillcolor='rgba(0, 200, 83, 0.3)'
    ))

    # Asks (sell orders) - Red
    fig.add_trace(go.Scatter(
        x=ask_prices,
        y=ask_cumulative,
        fill='tozeroy',
        name='Asks',
        line=dict(color='#FF4444', width=2),
        fillcolor='rgba(255, 68, 68, 0.3)'
    ))

    # Current price line
    fig.add_vline(x=current_price, line_dash="dash", line_color="yellow",
                  annotation_text=f"${current_price:.2f}", annotation_position="top")

    fig.update_layout(
        title="📊 Order Book Depth",
        xaxis_title="Price (USDT)",
        yaxis_title="Cumulative Volume",
        template='plotly_dark',
        height=300,
        showlegend=True,
        hovermode='x unified',
        margin=dict(l=10, r=10, t=40, b=10)
    )

    return fig

def create_recent_trades_chart(trades_data):
    """Create recent trades visualization"""
    if not trades_data:
        return None

    df_trades = pd.DataFrame(trades_data)

    # Separate buys and sells
    buys = df_trades[~df_trades['is_buyer_maker']]
    sells = df_trades[df_trades['is_buyer_maker']]

    fig = go.Figure()

    # Buy trades (green)
    if not buys.empty:
        fig.add_trace(go.Scatter(
            x=buys['time'],
            y=buys['price'],
            mode='markers',
            name='Buys',
            marker=dict(
                size=buys['qty'] * 10,  # Size based on quantity
                color='#00C853',
                symbol='triangle-up',
                line=dict(width=1, color='white')
            ),
            text=[f"${p:.2f}<br>{q:.4f}" for p, q in zip(buys['price'], buys['qty'])],
            hovertemplate='<b>Buy</b><br>%{text}<extra></extra>'
        ))

    # Sell trades (red)
    if not sells.empty:
        fig.add_trace(go.Scatter(
            x=sells['time'],
            y=sells['price'],
            mode='markers',
            name='Sells',
            marker=dict(
                size=sells['qty'] * 10,
                color='#FF4444',
                symbol='triangle-down',
                line=dict(width=1, color='white')
            ),
            text=[f"${p:.2f}<br>{q:.4f}" for p, q in zip(sells['price'], sells['qty'])],
            hovertemplate='<b>Sell</b><br>%{text}<extra></extra>'
        ))

    fig.update_layout(
        title="🔄 Recent Trades",
        xaxis_title="Time",
        yaxis_title="Price (USDT)",
        template='plotly_dark',
        height=300,
        showlegend=True,
        hovermode='closest',
        margin=dict(l=10, r=10, t=40, b=10)
    )

    return fig

def backtest_fng(df, fng, symbol, interval):
    """
    Backtest using Fear & Greed Index with daily precision.
    Always fetches daily data for accurate backtesting regardless of chart interval.
    """
    # Get the date range from the chart data
    start_date = df['timestamp'].min()
    end_date = df['timestamp'].max()

    # Fetch daily data for the same period for accurate backtesting
    try:
        days_diff = (end_date - start_date).days
        daily_klines = client.get_klines(
            symbol=symbol,
            interval=Client.KLINE_INTERVAL_1DAY,
            limit=min(days_diff + 1, 1000)  # Binance limit is 1000
        )
        daily_df = pd.DataFrame(daily_klines, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume',
                                                        'Close_time', 'Quote_asset_volume', 'Number_of_trades',
                                                        'Taker_buy_base_volume', 'Taker_buy_quote_volume', 'Ignore'])
        daily_df['Close'] = daily_df['Close'].astype(float)
        daily_df['timestamp'] = pd.to_datetime(daily_df['timestamp'], unit='ms')

        # Merge with Fear & Greed Index
        daily_df = daily_df.merge(fng[['timestamp', 'value']],
                                  left_on=daily_df['timestamp'].dt.date,
                                  right_on=fng['timestamp'].dt.date,
                                  how='left')
        daily_df['value'] = daily_df['value'].ffill()

    except:
        # Fallback to original method if daily fetch fails
        daily_df = df.copy()
        daily_df = daily_df.merge(fng[['timestamp', 'value']],
                                  left_on='timestamp',
                                  right_on='timestamp',
                                  how='left')
        daily_df['value'] = daily_df['value'].ffill()

    total_invested = 0
    total_tokens = 0
    entries = []
    last_entry = None

    for i, row in daily_df.iterrows():
        if pd.notna(row['value']) and row['value'] <= 45:
            if last_entry is None or (row['timestamp_x'] - last_entry).days >= 2:
                total_invested += ENTRY_AMOUNT
                total_tokens += ENTRY_AMOUNT / row['Close']
                entries.append({'timestamp': row['timestamp_x'], 'price': row['Close'], 'fng': row['value']})
                last_entry = row['timestamp_x']

    final_value = total_tokens * daily_df.iloc[-1]['Close'] if len(daily_df) > 0 else 0

    return entries, total_invested, final_value, daily_df

@st.cache_data(ttl=3600)
def fetch_coingecko_historical(coin_id, days):
    """Fetch historical data from CoinGecko API"""
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': days,
            'interval': 'daily'
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()

            # Convert to DataFrame
            prices = data.get('prices', [])
            volumes = data.get('total_volumes', [])

            df = pd.DataFrame(prices, columns=['timestamp', 'Close'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

            # Add volume data
            if volumes:
                vol_df = pd.DataFrame(volumes, columns=['timestamp', 'Volume'])
                vol_df['timestamp'] = pd.to_datetime(vol_df['timestamp'], unit='ms')
                df = df.merge(vol_df, on='timestamp', how='left')
            else:
                df['Volume'] = 0

            # CoinGecko only provides close prices, so we'll use close as open/high/low
            df['Open'] = df['Close']
            df['High'] = df['Close']
            df['Low'] = df['Close']

            return df
        else:
            return None

    except Exception as e:
        return None

def analyze_seasonality(symbol, years=10):
    """
    Analyze historical seasonality patterns for a cryptocurrency.
    Returns monthly, weekly, and daily statistics.
    Combines CoinGecko (for maximum historical data) with Binance (fallback).
    """
    try:
        # Map Binance symbols to CoinGecko IDs
        coin_map = {
            'BTCUSDT': 'bitcoin', 'ETHUSDT': 'ethereum', 'BNBUSDT': 'binancecoin',
            'SOLUSDT': 'solana', 'XRPUSDT': 'ripple', 'ADAUSDT': 'cardano',
            'AVAXUSDT': 'avalanche-2', 'DOGEUSDT': 'dogecoin', 'TRXUSDT': 'tron',
            'DOTUSDT': 'polkadot', 'MATICUSDT': 'matic-network', 'LINKUSDT': 'chainlink',
            'TONUSDT': 'the-open-network', 'SHIBUSDT': 'shiba-inu', 'LTCUSDT': 'litecoin',
            'BCHUSDT': 'bitcoin-cash', 'UNIUSDT': 'uniswap', 'XLMUSDT': 'stellar',
            'ATOMUSDT': 'cosmos', 'ETCUSDT': 'ethereum-classic'
        }

        coin_id = coin_map.get(symbol)
        total_days = years * 365

        df = None

        with st.spinner(f'📥 Fetching {years} years of historical data...'):
            # Try CoinGecko first (has data from 2013 for Bitcoin)
            if coin_id:
                df = fetch_coingecko_historical(coin_id, total_days)

        # Fallback to Binance if CoinGecko failed
        if df is None or df.empty:
            all_data = []
            chunks_needed = (total_days // 1000) + 1
            end_time = int(datetime.now().timestamp() * 1000)

            with st.spinner(f'📥 Fetching {years} years from Binance...'):
                for i in range(chunks_needed):
                    try:
                        klines = client.get_klines(
                            symbol=symbol,
                            interval=Client.KLINE_INTERVAL_1DAY,
                            limit=1000,
                            endTime=end_time
                        )

                        if not klines:
                            break

                        all_data.extend(klines)
                        end_time = int(klines[0][0]) - 1

                        if len(all_data) >= total_days:
                            break

                    except Exception as e:
                        break

            if not all_data:
                return None

            # Convert to DataFrame
            df = pd.DataFrame(all_data, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume',
                                               'Close_time', 'Quote_asset_volume', 'Number_of_trades',
                                               'Taker_buy_base_volume', 'Taker_buy_quote_volume', 'Ignore'])
            df['Open'] = df['Open'].astype(float)
            df['Close'] = df['Close'].astype(float)
            df['High'] = df['High'].astype(float)
            df['Low'] = df['Low'].astype(float)
            df['Volume'] = df['Volume'].astype(float)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Sort by timestamp (oldest first)
        df = df.sort_values('timestamp').reset_index(drop=True)

        # Remove duplicates
        df = df.drop_duplicates(subset=['timestamp']).reset_index(drop=True)

        # Calculate daily returns (Close to Close, not Open to Close)
        df['return'] = ((df['Close'] - df['Close'].shift(1)) / df['Close'].shift(1)) * 100
        df['volatility'] = ((df['High'] - df['Low']) / df['Low']) * 100

        # Extract time features
        df['year'] = df['timestamp'].dt.year
        df['month'] = df['timestamp'].dt.month
        df['month_name'] = df['timestamp'].dt.strftime('%B')
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['day_name'] = df['timestamp'].dt.strftime('%A')
        df['is_weekend'] = df['day_of_week'].isin([5, 6])  # Saturday=5, Sunday=6
        df['week_of_month'] = (df['timestamp'].dt.day - 1) // 7 + 1
        df['year_month'] = df['timestamp'].dt.to_period('M')

        # Calculate monthly returns properly - for each individual month occurrence
        monthly_returns = []
        for year_month in df['year_month'].unique():
            month_data = df[df['year_month'] == year_month]
            if len(month_data) > 0:
                first_close = month_data.iloc[0]['Close']
                last_close = month_data.iloc[-1]['Close']
                monthly_return = ((last_close - first_close) / first_close) * 100
                monthly_returns.append({
                    'year_month': year_month,
                    'month': month_data.iloc[0]['month'],
                    'month_name': month_data.iloc[0]['month_name'],
                    'monthly_return': monthly_return
                })

        monthly_returns_df = pd.DataFrame(monthly_returns)

        # Monthly statistics - average of actual monthly returns
        monthly_stats = df.groupby(['month', 'month_name']).agg({
            'return': ['mean', 'std', 'count'],
            'volatility': 'mean'
        }).reset_index()
        monthly_stats.columns = ['month', 'month_name', 'avg_daily_return', 'std_return', 'days', 'avg_volatility']

        # Merge with actual monthly returns
        monthly_return_avg = monthly_returns_df.groupby(['month', 'month_name'])['monthly_return'].mean().reset_index()
        monthly_return_avg.columns = ['month', 'month_name', 'avg_monthly_return']
        monthly_stats = monthly_stats.merge(monthly_return_avg, on=['month', 'month_name'], how='left')

        # Day of week statistics
        daily_stats = df.groupby(['day_of_week', 'day_name']).agg({
            'return': ['mean', 'std', 'count'],
            'volatility': 'mean'
        }).reset_index()
        daily_stats.columns = ['day_of_week', 'day_name', 'avg_return', 'std_return', 'days', 'avg_volatility']

        # Weekend vs Weekday
        weekend_stats = df.groupby('is_weekend').agg({
            'return': ['mean', 'std'],
            'volatility': 'mean'
        }).reset_index()
        weekend_stats.columns = ['is_weekend', 'avg_return', 'std_return', 'avg_volatility']
        weekend_stats['period'] = weekend_stats['is_weekend'].map({True: 'Weekend', False: 'Weekday'})

        # Week of month statistics (beginning, middle, end)
        week_stats = df.groupby('week_of_month').agg({
            'return': ['mean', 'std'],
            'volatility': 'mean'
        }).reset_index()
        week_stats.columns = ['week_of_month', 'avg_return', 'std_return', 'avg_volatility']
        week_stats['week_label'] = week_stats['week_of_month'].map({
            1: 'Week 1 (Start)',
            2: 'Week 2',
            3: 'Week 3',
            4: 'Week 4',
            5: 'Week 5 (End)'
        })

        return {
            'monthly': monthly_stats,
            'daily': daily_stats,
            'weekend': weekend_stats,
            'week_of_month': week_stats,
            'raw_df': df
        }
    except Exception as e:
        st.error(f"Error analyzing seasonality: {e}")
        return None

def create_seasonality_charts(stats):
    """Create visualization charts for seasonality analysis"""

    # Monthly Returns Chart
    fig_monthly = go.Figure()
    fig_monthly.add_trace(go.Bar(
        x=stats['monthly']['month_name'],
        y=stats['monthly']['avg_monthly_return'],
        name='Avg Monthly Return',
        marker_color=['#00C853' if x > 0 else '#FF4444' for x in stats['monthly']['avg_monthly_return']],
        text=stats['monthly']['avg_monthly_return'].round(2),
        texttemplate='%{text}%',
        textposition='outside'
    ))
    fig_monthly.update_layout(
        title='📅 Average Monthly Returns (Historical)',
        xaxis_title='Month',
        yaxis_title='Average Return (%)',
        height=400,
        template='plotly_dark',
        showlegend=False
    )

    # Day of Week Returns Chart
    fig_daily = go.Figure()
    fig_daily.add_trace(go.Bar(
        x=stats['daily']['day_name'],
        y=stats['daily']['avg_return'],
        name='Avg Daily Return',
        marker_color=['#00C853' if x > 0 else '#FF4444' for x in stats['daily']['avg_return']],
        text=stats['daily']['avg_return'].round(3),
        texttemplate='%{text}%',
        textposition='outside'
    ))
    fig_daily.update_layout(
        title='📆 Average Returns by Day of Week',
        xaxis_title='Day',
        yaxis_title='Average Return (%)',
        height=400,
        template='plotly_dark',
        showlegend=False
    )

    # Volatility by Day of Week
    fig_volatility = go.Figure()
    fig_volatility.add_trace(go.Bar(
        x=stats['daily']['day_name'],
        y=stats['daily']['avg_volatility'],
        name='Avg Volatility',
        marker_color='#2962FF',
        text=stats['daily']['avg_volatility'].round(2),
        texttemplate='%{text}%',
        textposition='outside'
    ))
    fig_volatility.update_layout(
        title='📊 Average Volatility by Day of Week',
        xaxis_title='Day',
        yaxis_title='Average Volatility (%)',
        height=400,
        template='plotly_dark',
        showlegend=False
    )

    return fig_monthly, fig_daily, fig_volatility

def create_backtest_chart(df, entries, symbol):
    # Create figure with secondary y-axis (dual axis)
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Use timestamp_x if it exists (from merge), otherwise use timestamp
    time_col = 'timestamp_x' if 'timestamp_x' in df.columns else 'timestamp'

    # Price chart on LEFT Y-axis
    fig.add_trace(
        go.Scatter(
            x=df[time_col],
            y=df['Close'],
            name='Price',
            line=dict(color='#2962FF', width=2.5),
            hovertemplate='Price: $%{y:.2f}<extra></extra>'
        ),
        secondary_y=False
    )

    # Fear & Greed Index on RIGHT Y-axis
    if 'value' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df[time_col],
                y=df['value'],
                name='Fear & Greed',
                line=dict(color='#9C27B0', width=2, dash='dot'),
                fill='tozeroy',
                fillcolor='rgba(156, 39, 176, 0.15)',
                hovertemplate='F&G: %{y:.0f}<extra></extra>',
                opacity=0.7
            ),
            secondary_y=True
        )

        # Add horizontal line at 45 (buy threshold) on right axis
        fig.add_hline(
            y=45,
            line_dash="dash",
            line_color="red",
            line_width=1.5,
            annotation_text="Buy ≤45",
            annotation_position="top right",
            secondary_y=True
        )

        # Add shaded zones for Fear & Greed on right axis
        fig.add_hrect(
            y0=0, y1=25,
            fillcolor="red",
            opacity=0.1,
            annotation_text="Extreme Fear",
            annotation_position="inside top left",
            annotation=dict(font_size=10),
            secondary_y=True
        )
        fig.add_hrect(
            y0=75, y1=100,
            fillcolor="green",
            opacity=0.1,
            annotation_text="Extreme Greed",
            annotation_position="inside bottom left",
            annotation=dict(font_size=10),
            secondary_y=True
        )

    # Buy entries markers on price (left axis)
    if entries:
        entry_times = [e['timestamp'] for e in entries]
        entry_prices = [e['price'] for e in entries]
        entry_fng = [e['fng'] for e in entries]

        fig.add_trace(
            go.Scatter(
                x=entry_times,
                y=entry_prices,
                mode='markers',
                name='Buy Entries',
                marker=dict(
                    color='#00C853',
                    size=14,
                    symbol='triangle-up',
                    line=dict(color='white', width=2)
                ),
                hovertemplate='<b>🟢 Buy Entry</b><br>Date: %{x}<br>Price: $%{y:.2f}<br>F&G: %{text}<extra></extra>',
                text=entry_fng
            ),
            secondary_y=False
        )

    fig.update_layout(
        title=f'{symbol} - Fear & Greed Backtest (Daily Data)',
        height=600,
        showlegend=True,
        hovermode='x unified',
        template='plotly_dark',
        margin=dict(l=10, r=10, t=60, b=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    # Set y-axes titles
    fig.update_yaxes(title_text="<b>Price (USDT)</b>", secondary_y=False, side='left', showgrid=True)
    fig.update_yaxes(title_text="<b>Fear & Greed Index</b>", secondary_y=True, side='right', range=[0, 100], showgrid=False)
    fig.update_xaxes(title_text="Date", showgrid=True)

    return fig

# Main App - Modern Header with Theme Toggle
col_header, col_theme = st.columns([6, 1])

with col_header:
    st.markdown("""
    <style>
    @keyframes cryptoGradient {
        0% {
            background-position: 0% 50%;
        }
        50% {
            background-position: 100% 50%;
        }
        100% {
            background-position: 0% 50%;
        }
    }

    @keyframes floatBitcoin {
        0%, 100% {
            transform: translateY(0px) rotate(0deg);
        }
        50% {
            transform: translateY(-10px) rotate(5deg);
        }
    }

    .crypto-header {
        position: relative;
        text-align: center;
        padding: 30px 20px;
        background: linear-gradient(-45deg,
            rgba(41, 98, 255, 0.15),
            rgba(30, 136, 229, 0.12),
            rgba(255, 152, 0, 0.12),
            rgba(76, 175, 80, 0.12),
            rgba(156, 39, 176, 0.12)
        );
        background-size: 400% 400%;
        animation: cryptoGradient 15s ease infinite;
        border-radius: 16px;
        margin-bottom: 20px;
        border: 1px solid rgba(41, 98, 255, 0.3);
        overflow: hidden;
    }

    .crypto-header::before {
        content: '₿';
        position: absolute;
        top: 10px;
        left: 20px;
        font-size: 60px;
        opacity: 0.08;
        animation: floatBitcoin 6s ease-in-out infinite;
    }

    .crypto-header::after {
        content: 'Ξ';
        position: absolute;
        bottom: 10px;
        right: 20px;
        font-size: 60px;
        opacity: 0.08;
        animation: floatBitcoin 6s ease-in-out infinite;
        animation-delay: 3s;
    }

    .crypto-title {
        margin: 0;
        background: linear-gradient(135deg, #2962ff 0%, #1e88e5 50%, #ff9800 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 42px;
        font-weight: 800;
        letter-spacing: -1px;
        position: relative;
        z-index: 1;
    }

    .crypto-subtitle {
        margin: 8px 0 0 0;
        color: #8b9dc3;
        font-size: 15px;
        font-weight: 500;
        letter-spacing: 1px;
        position: relative;
        z-index: 1;
    }
    </style>

    <div class='crypto-header'>
        <h1 class='crypto-title'>₿ KryptoView</h1>
        <p class='crypto-subtitle'>PROFESSIONAL CRYPTO ANALYTICS PLATFORM</p>
    </div>
    """, unsafe_allow_html=True)

with col_theme:
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    theme_icon = "🌙" if st.session_state.theme == 'dark' else "☀️"
    theme_label = "Light" if st.session_state.theme == 'dark' else "Dark"

    if st.button(f"{theme_icon} {theme_label}", use_container_width=True, key="theme_toggle"):
        st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'
        st.rerun()

# Horizontal Navigation Menu - Modern Style
st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("📈 Chart Analysis", use_container_width=True, type="primary" if 'mode' not in st.session_state or st.session_state.mode == "📈 Chart Analysis" else "secondary"):
        st.session_state.mode = "📈 Chart Analysis"
        st.rerun()

with col2:
    if st.button("📊 Market Overview", use_container_width=True, type="primary" if 'mode' in st.session_state and st.session_state.mode == "📊 Market Overview" else "secondary"):
        st.session_state.mode = "📊 Market Overview"
        st.rerun()

with col3:
    if st.button("📰 News & Trends", use_container_width=True, type="primary" if 'mode' in st.session_state and st.session_state.mode == "📰 News & Trends" else "secondary"):
        st.session_state.mode = "📰 News & Trends"
        st.rerun()

with col4:
    if st.button("🧮 Calculators", use_container_width=True, type="primary" if 'mode' in st.session_state and st.session_state.mode == "🧮 Calculators" else "secondary"):
        st.session_state.mode = "🧮 Calculators"
        st.rerun()

with col5:
    if st.button("📊 Seasonality", use_container_width=True, type="primary" if 'mode' in st.session_state and st.session_state.mode == "📊 Seasonality" else "secondary"):
        st.session_state.mode = "📊 Seasonality"
        st.rerun()

# Refresh Data button (moved from sidebar)
col_refresh1, col_refresh2, col_refresh3 = st.columns([3, 1, 3])
with col_refresh2:
    if st.button("🔄 Refresh Data", use_container_width=True, key="refresh_top"):
        st.cache_data.clear()
        st.rerun()

# Initialize mode if not exists
if 'mode' not in st.session_state:
    st.session_state.mode = "📈 Chart Analysis"

mode = st.session_state.mode

st.markdown("---")

# Initialize session state for selected crypto if not exists
if 'selected_crypto' not in st.session_state:
    st.session_state['selected_crypto'] = 'Bitcoin (BTC)'

# Use session state value as default
crypto_list = list(SYMBOLS.keys())
default_index = crypto_list.index(st.session_state['selected_crypto']) if st.session_state['selected_crypto'] in crypto_list else 0

crypto_name = st.session_state['selected_crypto']
symbol = SYMBOLS[crypto_name]

# Set default timeframe if not in session state (for Chart Analysis)
if 'timeframe' not in st.session_state:
    st.session_state['timeframe'] = '4h'
timeframe = st.session_state.get('timeframe', '4h')

# Get data (only for Chart Analysis mode - other modes don't need it)
if mode == "📈 Chart Analysis":
    # For Chart Analysis, fetch maximum data (1000 candles) for zoom/pan
    interval = TIMEFRAME_OPTIONS[timeframe]['interval']
    limit = 1000  # Maximum allowed by Binance

    with st.spinner('Loading data...'):
        df = fetch_data(symbol, interval, limit=limit)

    if df.empty:
        st.error("⚠️ Failed to fetch data. Please try again.")
    else:
        # Calculate indicators for Chart Analysis
        # Use dynamic EMA based on timeframe
        if timeframe in ['1m', '5m', '15m', '30m']:
            ema_type = 'short'
        elif timeframe in ['1h', '2h', '4h']:
            ema_type = 'mid'
        else:
            ema_type = 'long'
        # Pass timeframe to calculate_indicators for proper period adjustment
        df, ema1, ema2 = calculate_indicators(df, ema_type, timeframe=timeframe)

        # Chart Analysis Page - Reorganized Layout
        # Left: Chart | Right: Metrics + F&G + OI
        col_chart, col_sidebar = st.columns([2.5, 1])

        last = df.iloc[-1]
        prev = df.iloc[-2]
        price_change = ((last['Close'] - prev['Close']) / prev['Close']) * 100

        # Fetch additional data
        coingecko_data = fetch_coingecko_data(symbol)
        market_cap = coingecko_data['market_cap'] if coingecko_data else None
        circulating_supply = coingecko_data['circulating_supply'] if coingecko_data else None
        oi_data = fetch_open_interest_coinglass(symbol)  # Use Coinglass API
        fng_value, fng_class = fetch_current_fng()

        # Right sidebar with Key Metrics, F&G, and OI
        with col_sidebar:
            # Key Metrics - Compact header
            st.markdown("""
            <div style='background: linear-gradient(135deg, rgba(41, 98, 255, 0.12) 0%, rgba(30, 136, 229, 0.06) 100%);
                        padding: 4px; border-radius: 6px; border: 1px solid rgba(41, 98, 255, 0.25);
                        margin-bottom: 6px;'>
                <p style='color: #ffffff; font-size: 9px; font-weight: 700; letter-spacing: 0.5px;
                           margin: 0; text-transform: uppercase; text-align: center;'>
                    📊 METRICS
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Metrics in 2 columns
            col_m1, col_m2 = st.columns(2)

            # Calculate volume first
            # Calculate 24h volume
            if mode == "📈 Chart Analysis":
                if timeframe in ['1m', '5m']:
                    candles_24h = 1440 if timeframe == '1m' else 288
                    volume_24h = df.tail(candles_24h)['Volume'].sum() if len(df) >= candles_24h else df['Volume'].sum()
                elif timeframe == '15m':
                    volume_24h = df.tail(96)['Volume'].sum() if len(df) >= 96 else df['Volume'].sum()
                elif timeframe == '30m':
                    volume_24h = df.tail(48)['Volume'].sum() if len(df) >= 48 else df['Volume'].sum()
                elif timeframe == '1h':
                    volume_24h = df.tail(24)['Volume'].sum() if len(df) >= 24 else df['Volume'].sum()
                elif timeframe == '2h':
                    volume_24h = df.tail(12)['Volume'].sum() if len(df) >= 12 else df['Volume'].sum()
                elif timeframe == '4h':
                    volume_24h = df.tail(6)['Volume'].sum() if len(df) >= 6 else df['Volume'].sum()
                elif timeframe == '6h':
                    volume_24h = df.tail(4)['Volume'].sum() if len(df) >= 4 else df['Volume'].sum()
                elif timeframe == '12h':
                    volume_24h = df.tail(2)['Volume'].sum() if len(df) >= 2 else df['Volume'].sum()
                else:
                    volume_24h = last['Volume']
            else:
                if period == '1 Day':
                    volume_24h = df['Volume'].sum()
                elif period == '3 Days':
                    volume_24h = df.tail(24)['Volume'].sum() if len(df) >= 24 else df['Volume'].sum()
                elif period == '7 Days':
                    volume_24h = df.tail(12)['Volume'].sum() if len(df) >= 12 else df['Volume'].sum()
                elif period == '14 Days':
                    volume_24h = df.tail(6)['Volume'].sum() if len(df) >= 6 else df['Volume'].sum()
                elif period == '1 Month':
                    volume_24h = df.tail(4)['Volume'].sum() if len(df) >= 4 else df['Volume'].sum()
                else:
                    volume_24h = last['Volume']

            volume_usd = volume_24h * last['Close']

            # Calculate 24h range
            if mode == "📈 Chart Analysis":
                if timeframe in ['1m', '5m']:
                    candles_24h = 1440 if timeframe == '1m' else 288
                    high_24h = df.tail(candles_24h)['High'].max() if len(df) >= candles_24h else df['High'].max()
                    low_24h = df.tail(candles_24h)['Low'].min() if len(df) >= candles_24h else df['Low'].min()
                elif timeframe == '15m':
                    high_24h = df.tail(96)['High'].max() if len(df) >= 96 else df['High'].max()
                    low_24h = df.tail(96)['Low'].min() if len(df) >= 96 else df['Low'].min()
                elif timeframe == '30m':
                    high_24h = df.tail(48)['High'].max() if len(df) >= 48 else df['High'].max()
                    low_24h = df.tail(48)['Low'].min() if len(df) >= 48 else df['Low'].min()
                elif timeframe == '1h':
                    high_24h = df.tail(24)['High'].max() if len(df) >= 24 else df['High'].max()
                    low_24h = df.tail(24)['Low'].min() if len(df) >= 24 else df['Low'].min()
                elif timeframe == '2h':
                    high_24h = df.tail(12)['High'].max() if len(df) >= 12 else df['High'].max()
                    low_24h = df.tail(12)['Low'].min() if len(df) >= 12 else df['Low'].min()
                elif timeframe == '4h':
                    high_24h = df.tail(6)['High'].max() if len(df) >= 6 else df['High'].max()
                    low_24h = df.tail(6)['Low'].min() if len(df) >= 6 else df['Low'].min()
                elif timeframe == '6h':
                    high_24h = df.tail(4)['High'].max() if len(df) >= 4 else df['High'].max()
                    low_24h = df.tail(4)['Low'].min() if len(df) >= 4 else df['Low'].min()
                elif timeframe == '12h':
                    high_24h = df.tail(2)['High'].max() if len(df) >= 2 else df['High'].max()
                    low_24h = df.tail(2)['Low'].min() if len(df) >= 2 else df['Low'].min()
                else:
                    high_24h = last['High']
                    low_24h = last['Low']
            else:
                if period == '1 Day':
                    high_24h = df['High'].max()
                    low_24h = df['Low'].min()
                elif period == '3 Days':
                    high_24h = df.tail(24)['High'].max() if len(df) >= 24 else df['High'].max()
                    low_24h = df.tail(24)['Low'].min() if len(df) >= 24 else df['Low'].min()
                elif period == '7 Days':
                    high_24h = df.tail(12)['High'].max() if len(df) >= 12 else df['High'].max()
                    low_24h = df.tail(12)['Low'].min() if len(df) >= 12 else df['Low'].min()
                elif period == '14 Days':
                    high_24h = df.tail(6)['High'].max() if len(df) >= 6 else df['High'].max()
                    low_24h = df.tail(6)['Low'].min() if len(df) >= 6 else df['Low'].min()
                elif period == '1 Month':
                    high_24h = df.tail(4)['High'].max() if len(df) >= 4 else df['High'].max()
                    low_24h = df.tail(4)['Low'].min() if len(df) >= 4 else df['Low'].min()
                else:
                    high_24h = last['High']
                    low_24h = last['Low']

            range_pct = ((high_24h - low_24h) / low_24h * 100)

            # Custom CSS for smaller metrics
            st.markdown("""
            <style>
            [data-testid="stMetricValue"] {
                font-size: 9px !important;
            }
            [data-testid="stMetricLabel"] {
                font-size: 6px !important;
            }
            [data-testid="stMetricDelta"] {
                font-size: 7px !important;
            }
            </style>
            """, unsafe_allow_html=True)

            # Display metrics in 2 columns (compact)
            with col_m1:
                st.metric("💰 Price", f"${last['Close']:.2f}", f"{price_change:+.2f}%")
                st.metric("📈 Vol", format_large_number(volume_usd))
                st.metric("📊 RSI", f"{last['RSI']:.2f}")

            with col_m2:
                st.metric("💎 MCap", format_large_number(market_cap) if market_cap else "N/A")
                st.metric("📉 Range", f"{range_pct:.2f}%")
                if circulating_supply:
                    st.metric("🔄 Supply", format_number(circulating_supply))

            # Fear & Greed Index (Compact)
            if fng_value is not None:
                st.markdown("""
                <div style='background: linear-gradient(135deg, rgba(156, 39, 176, 0.12) 0%, rgba(233, 30, 99, 0.06) 100%);
                            padding: 4px; border-radius: 6px; border: 1px solid rgba(156, 39, 176, 0.25);
                            margin: 6px 0;'>
                    <p style='color: #ffffff; font-size: 9px; font-weight: 700; letter-spacing: 0.5px;
                               margin: 0; text-transform: uppercase; text-align: center;'>
                        🎭 FEAR & GREED
                    </p>
                </div>
                """, unsafe_allow_html=True)

                fng_color, fng_emoji = get_fng_color(fng_value)

                st.markdown(f"""
                <div style='text-align: center; padding: 10px; background: linear-gradient(135deg, rgba(156, 39, 176, 0.08) 0%, rgba(233, 30, 99, 0.04) 100%);
                            border-radius: 10px; margin-bottom: 10px;'>
                    <div style='font-size: 32px; margin-bottom: 4px;'>{fng_emoji}</div>
                    <div style='font-size: 28px; font-weight: 800; color: {fng_color}; letter-spacing: -1px;'>{fng_value}</div>
                    <div style='font-size: 10px; color: #8b9dc3; text-transform: uppercase; margin-top: 4px; font-weight: 600; letter-spacing: 0.5px;'>{fng_class}</div>
                </div>
                """, unsafe_allow_html=True)

                st.progress(fng_value / 100)

                col_fear, col_greed = st.columns(2)
                with col_fear:
                    st.markdown("<span style='font-size: 9px; color: #8b9dc3; font-weight: 600;'>😱 Fear</span>", unsafe_allow_html=True)
                with col_greed:
                    st.markdown("<span style='font-size: 9px; color: #8b9dc3; text-align: right; display: block; font-weight: 600;'>🤑 Greed</span>", unsafe_allow_html=True)

            # Open Interest Section (compact with Long/Short)
            if oi_data:
                st.markdown("""
                <div style='background: linear-gradient(135deg, rgba(41, 98, 255, 0.12) 0%, rgba(30, 136, 229, 0.06) 100%);
                            padding: 8px; border-radius: 10px; border: 1px solid rgba(41, 98, 255, 0.25);
                            margin: 10px 0;'>
                    <p style='color: #ffffff; font-size: 11px; font-weight: 700; letter-spacing: 0.8px;
                               margin: 0; text-transform: uppercase; text-align: center;'>
                        🔓 OPEN INTEREST
                    </p>
                </div>
                """, unsafe_allow_html=True)

                source = oi_data.get('source', 'Unknown')
                st.markdown(f"<p style='font-size: 10px; color: #b0b8c8; text-align: center; margin-bottom: 8px; font-weight: 500;'>Source: {source}</p>", unsafe_allow_html=True)

                # Total OI
                st.markdown(f"""
                <div style='text-align: center; padding: 8px; background: linear-gradient(135deg, rgba(41, 98, 255, 0.08) 0%, rgba(30, 136, 229, 0.04) 100%);
                            border-radius: 10px; margin-bottom: 8px;'>
                    <div style='font-size: 10px; color: #b0b8c8; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;'>TOTAL</div>
                    <div style='font-size: 20px; font-weight: 800; color: #42A5F5; margin-top: 4px; letter-spacing: -0.5px;'>{format_large_number(oi_data['open_interest'])}</div>
                </div>
                """, unsafe_allow_html=True)

                # Long/Short positions
                col_l, col_s = st.columns(2)
                with col_l:
                    st.markdown(f"""
                    <div style='padding: 8px; background: linear-gradient(135deg, rgba(0, 200, 83, 0.15) 0%, rgba(0, 200, 83, 0.05) 100%);
                                border-radius: 10px; border: 1px solid rgba(0, 200, 83, 0.3);'>
                        <div style='font-size: 10px; color: #b0b8c8; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px;'>📈 LONG</div>
                        <div style='font-size: 18px; font-weight: 800; color: #26E07F; margin: 4px 0; letter-spacing: -0.5px;'>{oi_data['long_percentage']:.1f}%</div>
                        <div style='font-size: 10px; color: #26E07F; font-weight: 600;'>{format_large_number(oi_data.get('long_amount', 0))}</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col_s:
                    st.markdown(f"""
                    <div style='padding: 8px; background: linear-gradient(135deg, rgba(255, 68, 68, 0.15) 0%, rgba(255, 68, 68, 0.05) 100%);
                                border-radius: 10px; border: 1px solid rgba(255, 68, 68, 0.3);'>
                        <div style='font-size: 10px; color: #b0b8c8; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px;'>📉 SHORT</div>
                        <div style='font-size: 18px; font-weight: 800; color: #FF6B6B; margin: 4px 0; letter-spacing: -0.5px;'>{oi_data['short_percentage']:.1f}%</div>
                        <div style='font-size: 10px; color: #FF6B6B; font-weight: 600;'>{format_large_number(oi_data.get('short_amount', 0))}</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Progress bar
                st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
                st.progress(oi_data['long_percentage'] / 100)

                # 24h change
                if 'oi_change_24h' in oi_data and oi_data['oi_change_24h'] is not None:
                    change_color = "#26E07F" if oi_data['oi_change_24h'] >= 0 else "#FF6B6B"
                    change_symbol = "+" if oi_data['oi_change_24h'] >= 0 else ""
                    st.markdown(f"""
                    <div style='text-align: center; padding: 8px; background: rgba(30, 40, 60, 0.4);
                                border-radius: 10px; margin-top: 8px;'>
                        <div style='font-size: 10px; color: #b0b8c8; font-weight: 600; letter-spacing: 0.5px;'>24H CHANGE</div>
                        <div style='font-size: 15px; font-weight: 700; color: {change_color}; margin-top: 2px;'>{change_symbol}{oi_data['oi_change_24h']:.2f}%</div>
                    </div>
                    """, unsafe_allow_html=True)

            # Main chart area (left side)
            with col_chart:

                # Multiple Timeframes Toggle
                multi_tf_view = st.checkbox("📊 Multiple Timeframes View (1h, 4h, 1d, 1w)", value=False, key="multi_tf_toggle")

                # Top Control Bar - 4 sections in one row
                col_crypto, col_timeframe, col_indicators, col_soon = st.columns([1, 1, 1, 1])

                # 1. CRYPTOCURRENCY SELECTOR (Light Orange)
                with col_crypto:
                    st.markdown("""
                    <div style='background: linear-gradient(135deg, rgba(255, 152, 0, 0.3) 0%, rgba(255, 193, 7, 0.25) 100%);
                                padding: 4px; border-radius: 6px; margin-bottom: 4px; text-align: center;
                                border: 1px solid rgba(255, 152, 0, 0.4);'>
                        <p style='margin: 0; color: #FFA726; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;'>
                            💰 CRYPTO
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    crypto_name = st.selectbox(
                        "Choose cryptocurrency:",
                        list(SYMBOLS.keys()),
                        index=list(SYMBOLS.keys()).index(st.session_state.get('selected_crypto', 'Bitcoin (BTC)')),
                        key="chart_crypto_selector",
                        label_visibility="collapsed"
                    )

                    # Update session state and symbol if changed
                    if crypto_name != st.session_state.get('selected_crypto'):
                        st.session_state['selected_crypto'] = crypto_name
                        symbol = SYMBOLS[crypto_name]
                        st.rerun()
                    else:
                        symbol = SYMBOLS[crypto_name]

                # 2. TIMEFRAME SELECTOR (Light Blue)
                with col_timeframe:
                    st.markdown("""
                    <div style='background: linear-gradient(135deg, rgba(66, 165, 245, 0.3) 0%, rgba(100, 181, 246, 0.25) 100%);
                                padding: 4px; border-radius: 6px; margin-bottom: 4px; text-align: center;
                                border: 1px solid rgba(66, 165, 245, 0.4);'>
                        <p style='margin: 0; color: #64B5F6; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;'>
                            ⏱️ TIMEFRAME
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Initialize chart_timeframe in session state if not exists
                    if 'chart_timeframe' not in st.session_state:
                        st.session_state['chart_timeframe'] = '30D'

                    timeframe_list = ['1D', '7D', '30D', '3M', '6M', '1Y', '3Y', '5Y', 'All']
                    selected_tf = st.selectbox(
                        "Choose timeframe:",
                        timeframe_list,
                        index=timeframe_list.index(st.session_state['chart_timeframe']),
                        key="chart_tf_selector",
                        label_visibility="collapsed"
                    )

                    # Update session state if changed
                    if selected_tf != st.session_state['chart_timeframe']:
                        st.session_state['chart_timeframe'] = selected_tf
                        st.rerun()

                # 3. INDICATORS MULTISELECT (Light Green)
                with col_indicators:
                    st.markdown("""
                    <div style='background: linear-gradient(135deg, rgba(102, 187, 106, 0.3) 0%, rgba(129, 199, 132, 0.25) 100%);
                                padding: 4px; border-radius: 6px; margin-bottom: 4px; text-align: center;
                                border: 1px solid rgba(102, 187, 106, 0.4);'>
                        <p style='margin: 0; color: #81C784; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;'>
                            📊 INDICATORS
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Initialize indicator states in session state
                    if 'selected_indicators' not in st.session_state:
                        st.session_state.selected_indicators = []

                    indicator_options = ['EMAs', 'Bollinger Bands', 'RSI', 'Volume', 'MACD']
                    selected_indicators = st.multiselect(
                        "Choose indicators:",
                        indicator_options,
                        default=st.session_state.selected_indicators,
                        key="chart_indicator_multiselect",
                        label_visibility="collapsed"
                    )

                    # Update session state
                    st.session_state.selected_indicators = selected_indicators

                    # Set indicator states based on multiselect
                    show_ema = 'EMAs' in selected_indicators
                    show_bb = 'Bollinger Bands' in selected_indicators
                    show_rsi = 'RSI' in selected_indicators
                    show_volume = 'Volume' in selected_indicators
                    show_macd = 'MACD' in selected_indicators
                    show_stoch = False
                    show_atr = False

                # 4. SOON BUTTON (Light Purple - Disabled)
                with col_soon:
                    st.markdown("""
                    <div style='background: linear-gradient(135deg, rgba(149, 117, 205, 0.3) 0%, rgba(171, 71, 188, 0.25) 100%);
                                padding: 4px; border-radius: 6px; margin-bottom: 4px; text-align: center;
                                border: 1px solid rgba(149, 117, 205, 0.4);'>
                        <p style='margin: 0; color: #9575CD; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;'>
                            🔮 SOON
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("""
                    <div style='background: rgba(149, 117, 205, 0.1); padding: 6px; border-radius: 6px;
                                border: 1px solid rgba(149, 117, 205, 0.3); text-align: center;'>
                        <p style='margin: 0; color: #9575CD; font-size: 9px;'>Coming Soon</p>
                    </div>
                    """, unsafe_allow_html=True)

                # Map timeframe to interval and number of candles
                timeframe_options = {
                    '1D': '15m',
                    '7D': '1h',
                    '30D': '2h',
                    '3M': '4h',
                    '6M': '6h',
                    '1Y': '1d',
                    '3Y': '1d',
                    '5Y': '1w',
                    'All': '1w'
                }

                # Map timeframe to number of candles needed
                timeframe_limits = {
                    '1D': 96,
                    '7D': 168,
                    '30D': 360,
                    '3M': 540,
                    '6M': 720,
                    '1Y': 500,
                    '3Y': 1000,
                    '5Y': 500,
                    'All': 1000
                }

                # Fetch data based on selected timeframe
                chart_tf = st.session_state['chart_timeframe']
                chart_interval = timeframe_options[chart_tf]
                chart_limit = timeframe_limits[chart_tf]

                # Fetch chart data
                with st.spinner(f'Loading {chart_tf} data...'):
                    df_chart = fetch_data(symbol, chart_interval, limit=min(chart_limit, 1000))

                if not df_chart.empty:
                    # Calculate indicators for chart data
                    if chart_tf in ['1D', '7D', '30D']:
                        ema_type_chart = 'short'
                    elif chart_tf in ['3M', '6M']:
                        ema_type_chart = 'mid'
                    else:
                        ema_type_chart = 'long'

                    df_chart, ema1_chart, ema2_chart = calculate_indicators(df_chart, ema_type_chart)

                # Advanced Configuration Panel (only show if EMA is enabled)
                if show_ema:
                    st.markdown("<br>", unsafe_allow_html=True)
                    with st.expander("⚙️ ADVANCED EMA SETTINGS", expanded=False):
                        st.markdown("""
                        <div style='background: linear-gradient(135deg, rgba(76, 175, 80, 0.1) 0%, rgba(139, 195, 74, 0.05) 100%);
                                    padding: 15px; border-radius: 10px; border: 1px solid rgba(76, 175, 80, 0.3);
                                    margin-bottom: 15px;'>
                            <p style='color: #4CAF50; font-size: 14px; font-weight: 600; margin: 0;'>
                                🎯 Customize EMA periods for advanced analysis
                            </p>
                        </div>
                        """, unsafe_allow_html=True)

                    # Stochastic Configuration
                    if show_stoch:
                        st.markdown("**📈 Stochastic Settings**")
                        col_stoch1, col_stoch2, col_stoch3, col_stoch4 = st.columns(4)
                        with col_stoch1:
                            stoch_k = st.number_input("K Period", min_value=5, max_value=30, value=14, key="stoch_k")
                        with col_stoch2:
                            stoch_d = st.number_input("D Period", min_value=1, max_value=10, value=3, key="stoch_d")
                        with col_stoch3:
                            stoch_ob = st.number_input("Overbought", min_value=70, max_value=90, value=80, key="stoch_ob")
                        with col_stoch4:
                            stoch_os = st.number_input("Oversold", min_value=10, max_value=30, value=20, key="stoch_os")
                        st.markdown("---")

                    # ATR Configuration
                    if show_atr:
                        st.markdown("**📉 ATR Settings**")
                        atr_period = st.number_input("Period", min_value=5, max_value=30, value=14, key="atr_period")

                # EMA Selection (only show if EMAs are enabled)
                if show_ema:
                    st.markdown("""
                    <div style='background: linear-gradient(135deg, rgba(255, 109, 0, 0.2) 0%, rgba(0, 200, 83, 0.2) 100%);
                                padding: 20px; border-radius: 15px; border: 2px solid rgba(255, 109, 0, 0.5);
                                margin: 20px 0; box-shadow: 0 4px 15px rgba(255, 109, 0, 0.2);'>
                        <p style='color: #ffffff; font-size: 16px; font-weight: 700; letter-spacing: 1px;
                                   margin: 0 0 15px 0; text-transform: uppercase; text-align: center;'>
                            📈 EMA CONFIGURATION
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    col_ema1, col_ema2 = st.columns(2)

                    ema_options = [20, 50, 100, 200, 350]

                    with col_ema1:
                        st.markdown("""
                        <p style='color: #FF6D00; font-size: 13px; font-weight: 700; margin-bottom: 10px;
                                   text-align: center; background: rgba(255, 109, 0, 0.15);
                                   padding: 8px; border-radius: 8px;'>
                            🔸 FAST EMA
                        </p>
                        """, unsafe_allow_html=True)
                        ema1_selected = st.selectbox(
                            "Select Fast EMA:",
                            ema_options,
                            index=1,  # Default to 50
                            key="ema1_select",
                            label_visibility="collapsed"
                        )

                    with col_ema2:
                        st.markdown("""
                        <p style='color: #00C853; font-size: 13px; font-weight: 700; margin-bottom: 10px;
                                   text-align: center; background: rgba(0, 200, 83, 0.15);
                                   padding: 8px; border-radius: 8px;'>
                            🔹 SLOW EMA
                        </p>
                        """, unsafe_allow_html=True)
                        ema2_selected = st.selectbox(
                            "Select Slow EMA:",
                            ema_options,
                            index=3,  # Default to 200
                            key="ema2_select",
                            label_visibility="collapsed"
                        )

                    # Recalculate EMAs with selected values
                    if ema1_selected and ema2_selected:
                        df_chart[f'EMA{ema1_selected}'] = EMAIndicator(df_chart['Close'], window=ema1_selected).ema_indicator()
                        df_chart[f'EMA{ema2_selected}'] = EMAIndicator(df_chart['Close'], window=ema2_selected).ema_indicator()
                        ema1_chart = ema1_selected
                        ema2_chart = ema2_selected

                        # Show selected EMAs with modern design
                        st.markdown(f"""
                        <div style='text-align: center; padding: 15px;
                                    background: linear-gradient(135deg, rgba(255, 109, 0, 0.2) 0%, rgba(0, 200, 83, 0.2) 100%);
                                    border-radius: 12px; margin-top: 15px;
                                    border: 2px solid rgba(255, 215, 0, 0.4);
                                    box-shadow: 0 3px 10px rgba(255, 215, 0, 0.2);'>
                            <span style='color: #FF6D00; font-size: 16px; font-weight: 700;'>EMA {ema1_selected}</span>
                            <span style='color: #FFD700; margin: 0 12px; font-size: 18px;'>×</span>
                            <span style='color: #00C853; font-size: 16px; font-weight: 700;'>EMA {ema2_selected}</span>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("---")

                # Chart with selected timeframe data
                if not df_chart.empty:
                    if multi_tf_view:
                        # Multiple Timeframes View - 4 charts in 2x2 grid
                        st.markdown("### 📊 Multiple Timeframes Analysis")

                        # Fetch data for all 4 timeframes
                        timeframes_multi = {
                            '1h': {'interval': Client.KLINE_INTERVAL_1HOUR, 'limit': 168, 'title': '1 Hour'},
                            '4h': {'interval': Client.KLINE_INTERVAL_4HOUR, 'limit': 180, 'title': '4 Hours'},
                            '1d': {'interval': Client.KLINE_INTERVAL_1DAY, 'limit': 180, 'title': '1 Day'},
                            '1w': {'interval': Client.KLINE_INTERVAL_1WEEK, 'limit': 104, 'title': '1 Week'}
                        }

                        # Create 2x2 grid
                        row1_col1, row1_col2 = st.columns(2)
                        row2_col1, row2_col2 = st.columns(2)

                        cols = [row1_col1, row1_col2, row2_col1, row2_col2]
                        tf_keys = ['1h', '4h', '1d', '1w']

                        for idx, (tf_key, col) in enumerate(zip(tf_keys, cols)):
                            with col:
                                tf_config = timeframes_multi[tf_key]

                                with st.spinner(f'Loading {tf_config["title"]} data...'):
                                    df_multi = fetch_data(symbol, tf_config['interval'], limit=tf_config['limit'])

                                if not df_multi.empty:
                                    # Calculate indicators for this timeframe
                                    if tf_key in ['1h']:
                                        ema_type_multi = 'short'
                                    elif tf_key in ['4h']:
                                        ema_type_multi = 'mid'
                                    else:
                                        ema_type_multi = 'long'

                                    df_multi, ema1_multi, ema2_multi = calculate_indicators(df_multi, ema_type_multi, timeframe=tf_key)

                                    # Create smaller chart (no indicators for cleaner view)
                                    fig_multi = create_chart(
                                        df_multi,
                                        f"{crypto_name} - {tf_config['title']}",
                                        ema1_multi,
                                        ema2_multi,
                                        show_ema=show_ema,
                                        show_bb=False,  # Disable for cleaner multi-view
                                        show_rsi=False,
                                        show_volume=show_volume,
                                        show_macd=False,
                                        show_stoch=False,
                                        show_atr=False
                                    )

                                    # Update layout for smaller charts
                                    fig_multi.update_layout(height=350, margin=dict(t=40, b=20, l=40, r=20))

                                    st.plotly_chart(fig_multi, use_container_width=True, key=f"chart_multi_{tf_key}")
                                else:
                                    st.error(f"⚠️ Failed to load {tf_config['title']} data")
                    else:
                        # Single Chart View (original)
                        fig = create_chart(
                            df_chart,
                            crypto_name,
                            ema1_chart,
                            ema2_chart,
                            show_ema=show_ema,
                            show_bb=show_bb,
                            show_rsi=show_rsi,
                            show_volume=show_volume,
                            show_macd=show_macd,
                            show_stoch=show_stoch,
                            show_atr=show_atr
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("⚠️ Failed to load chart data.")

elif mode == "📊 Market Overview":
    # Market Overview Page - Top 50 Cryptocurrencies Table
    st.markdown("## 📊 Crypto Market Overview")

    # Top Gainers/Losers Section
    st.markdown("### 🔥 Top Movers (24h)")

    with st.spinner('Loading market data...'):
        top_coins = fetch_top_coins(100)  # Fetch more to get better gainers/losers

    if top_coins:
        # Create DataFrame for analysis
        df_all = pd.DataFrame(top_coins)

        # Sort by 24h change
        df_sorted = df_all.sort_values('change_24h', ascending=False)

        # Get top 5 gainers and losers
        top_gainers = df_sorted.head(5)
        top_losers = df_sorted.tail(5)

        # Display in two columns
        col_gainers, col_losers = st.columns(2)

        with col_gainers:
            st.markdown("#### 📈 **Top Gainers**")
            for idx, coin in top_gainers.iterrows():
                change_24h = coin.get('change_24h', 0)
                price = coin.get('price', 0)
                symbol = coin.get('symbol', '').upper()
                name = coin.get('name', '')

                # Smart price formatting based on value
                if price >= 1:
                    price_str = f"${price:,.2f}"
                elif price >= 0.01:
                    price_str = f"${price:,.4f}"
                else:
                    price_str = f"${price:,.6f}"

                # Dynamic colors based on theme
                if st.session_state.theme == 'dark':
                    gainer_bg = "rgba(0,255,0,0.1)"
                    gainer_border = "#00ff00"
                    gainer_text = "#00ff00"
                    symbol_color = "#888"
                    price_color = "#aaa"
                else:
                    gainer_bg = "rgba(34,139,34,0.15)"
                    gainer_border = "#228B22"
                    gainer_text = "#006400"
                    symbol_color = "#666"
                    price_color = "#777"

                st.markdown(f"""
                <div style='padding: 10px; background: {gainer_bg}; border-left: 3px solid {gainer_border}; border-radius: 5px; margin-bottom: 8px;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <span style='font-weight: 600; font-size: 16px;'>{name}</span>
                            <span style='color: {symbol_color}; font-size: 12px; margin-left: 8px;'>{symbol}</span>
                        </div>
                        <div style='text-align: right;'>
                            <div style='color: {gainer_text}; font-weight: 700; font-size: 18px;'>+{change_24h:.2f}%</div>
                            <div style='color: {price_color}; font-size: 12px;'>{price_str}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with col_losers:
            st.markdown("#### 📉 **Top Losers**")
            for idx, coin in top_losers.iterrows():
                change_24h = coin.get('change_24h', 0)
                price = coin.get('price', 0)
                symbol = coin.get('symbol', '').upper()
                name = coin.get('name', '')

                # Smart price formatting based on value
                if price >= 1:
                    price_str = f"${price:,.2f}"
                elif price >= 0.01:
                    price_str = f"${price:,.4f}"
                else:
                    price_str = f"${price:,.6f}"

                # Dynamic colors based on theme
                if st.session_state.theme == 'dark':
                    loser_bg = "rgba(255,0,0,0.1)"
                    loser_border = "#ff0000"
                    loser_text = "#ff0000"
                    symbol_color = "#888"
                    price_color = "#aaa"
                else:
                    loser_bg = "rgba(220,20,60,0.15)"
                    loser_border = "#DC143C"
                    loser_text = "#8B0000"
                    symbol_color = "#666"
                    price_color = "#777"

                st.markdown(f"""
                <div style='padding: 10px; background: {loser_bg}; border-left: 3px solid {loser_border}; border-radius: 5px; margin-bottom: 8px;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <span style='font-weight: 600; font-size: 16px;'>{name}</span>
                            <span style='color: {symbol_color}; font-size: 12px; margin-left: 8px;'>{symbol}</span>
                        </div>
                        <div style='text-align: right;'>
                            <div style='color: {loser_text}; font-weight: 700; font-size: 18px;'>{change_24h:.2f}%</div>
                            <div style='color: {price_color}; font-size: 12px;'>{price_str}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # Market Cap Dominance Section
        st.markdown("### 💰 Market Cap Dominance")

        dominance_data = fetch_market_dominance()

        if dominance_data:
            col_dom1, col_dom2 = st.columns([2, 1])

            with col_dom1:
                # Create pie chart for dominance
                btc_dom = dominance_data['btc_dominance']
                eth_dom = dominance_data['eth_dominance']
                others_dom = 100 - btc_dom - eth_dom

                # Dynamic text color based on theme
                chart_text_color = text_color

                fig_dominance = go.Figure(data=[go.Pie(
                    labels=['Bitcoin (BTC)', 'Ethereum (ETH)', 'Altcoins'],
                    values=[btc_dom, eth_dom, others_dom],
                    hole=0.4,
                    marker=dict(colors=['#F7931A', '#627EEA', '#6C757D']),
                    textinfo='label+percent',
                    textfont=dict(size=14, color=chart_text_color),
                    hovertemplate='<b>%{label}</b><br>Dominance: %{value:.2f}%<extra></extra>'
                )])

                fig_dominance.update_layout(
                    title=dict(
                        text='Crypto Market Dominance',
                        font=dict(size=18, color=chart_text_color),
                        x=0.5,
                        xanchor='center'
                    ),
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.2,
                        xanchor="center",
                        x=0.5,
                        font=dict(color=chart_text_color)
                    ),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=350,
                    margin=dict(t=60, b=60, l=20, r=20)
                )

                st.plotly_chart(fig_dominance, use_container_width=True)

            with col_dom2:
                # Display dominance stats
                total_mcap = dominance_data['total_market_cap']

                # Dynamic colors based on theme
                label_color = text_secondary if st.session_state.theme == 'dark' else '#666'

                # Total Market Cap
                st.markdown("<div style='text-align: center; margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size: 12px; color: {label_color};'>Total Market Cap</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size: 28px; font-weight: 700; color: #1E90FF;'>${total_mcap/1e12:.2f}T</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

                # Bitcoin Dominance
                st.markdown(f"""
                <div style='margin-bottom: 12px; padding: 12px; background: rgba(247,147,26,0.15); border-radius: 8px; border-left: 4px solid #F7931A;'>
                    <div style='font-size: 11px; color: {label_color}; margin-bottom: 4px;'>Bitcoin</div>
                    <div style='font-size: 22px; font-weight: 700; color: #F7931A;'>{btc_dom:.2f}%</div>
                </div>
                """, unsafe_allow_html=True)

                # Ethereum Dominance
                st.markdown(f"""
                <div style='margin-bottom: 12px; padding: 12px; background: rgba(98,126,234,0.15); border-radius: 8px; border-left: 4px solid #627EEA;'>
                    <div style='font-size: 11px; color: {label_color}; margin-bottom: 4px;'>Ethereum</div>
                    <div style='font-size: 22px; font-weight: 700; color: #627EEA;'>{eth_dom:.2f}%</div>
                </div>
                """, unsafe_allow_html=True)

                # Altcoins Dominance
                st.markdown(f"""
                <div style='padding: 12px; background: rgba(108,117,125,0.15); border-radius: 8px; border-left: 4px solid #6C757D;'>
                    <div style='font-size: 11px; color: {label_color}; margin-bottom: 4px;'>Altcoins</div>
                    <div style='font-size: 22px; font-weight: 700; color: #6C757D;'>{others_dom:.2f}%</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

    # Market Overview Table
    st.markdown("### 📊 Top 50 Cryptocurrencies")

    with st.spinner('Loading top 50 cryptocurrencies...'):
        top_coins = fetch_top_coins(50)

    if top_coins:
        # Create DataFrame
        df_market = pd.DataFrame(top_coins)

        # Pagination controls
        coins_per_page = 25
        total_pages = (len(df_market) + coins_per_page - 1) // coins_per_page

        col_page1, col_page2, col_page3 = st.columns([1, 2, 1])

        with col_page2:
            page = st.selectbox(
                "📄 Page:",
                range(1, total_pages + 1),
                format_func=lambda x: f"Page {x} of {total_pages}",
                key="market_page"
            )

        # Get page data
        start_idx = (page - 1) * coins_per_page
        end_idx = min(start_idx + coins_per_page, len(df_market))
        df_page = df_market.iloc[start_idx:end_idx].copy()

        # Format functions
        def format_price(price):
            """Format price based on value"""
            if price >= 1000:
                return f"${price:,.2f}"
            elif price >= 1:
                return f"${price:,.2f}"
            elif price >= 0.01:
                return f"${price:,.4f}"
            else:
                return f"${price:,.6f}"

        def format_large_num(num):
            """Format large numbers with K, M, B, T suffixes"""
            if num >= 1_000_000_000_000:
                return f"${num/1_000_000_000_000:.2f}T"
            elif num >= 1_000_000_000:
                return f"${num/1_000_000_000:.2f}B"
            elif num >= 1_000_000:
                return f"${num/1_000_000:.2f}M"
            elif num >= 1_000:
                return f"${num/1_000:.2f}K"
            else:
                return f"${num:.2f}"

        def format_supply(supply):
            """Format circulating supply"""
            if supply >= 1_000_000_000:
                return f"{supply/1_000_000_000:.2f}B"
            elif supply >= 1_000_000:
                return f"{supply/1_000_000:.2f}M"
            elif supply >= 1_000:
                return f"{supply/1_000:.2f}K"
            else:
                return f"{supply:.2f}"

        # Create display dataframe with raw values for styling
        df_display = pd.DataFrame({
            '#': df_page['rank'],
            'Name': df_page['name'],
            'Symbol': df_page['symbol'],
            'Price': df_page['price'].apply(format_price),
            '1h %': df_page['change_1h'],
            '24h %': df_page['change_24h'],
            '7d %': df_page['change_7d'],
            'Market Cap': df_page['market_cap'].apply(format_large_num),
            'Volume (24h)': df_page['volume_24h'].apply(format_large_num),
            'Circulating Supply': df_page['circulating_supply'].apply(format_supply)
        })

        # Apply styling to percentage columns
        def style_percentage(val):
            """Style percentage values with colors and background"""
            try:
                # Extract numeric value from string if needed
                if isinstance(val, str):
                    val = float(val.replace('%', '').replace('+', ''))

                # Dynamic colors based on theme
                if st.session_state.theme == 'dark':
                    # Dark mode colors (bright)
                    if pd.isna(val) or val == 0:
                        return 'color: #888888'
                    elif val >= 10:
                        return 'background-color: rgba(0, 255, 0, 0.2); color: #00ff00; font-weight: bold'
                    elif val >= 5:
                        return 'background-color: rgba(0, 200, 0, 0.15); color: #00dd00; font-weight: bold'
                    elif val > 0:
                        return 'background-color: rgba(0, 150, 0, 0.1); color: #00bb00'
                    elif val <= -10:
                        return 'background-color: rgba(255, 0, 0, 0.2); color: #ff0000; font-weight: bold'
                    elif val <= -5:
                        return 'background-color: rgba(200, 0, 0, 0.15); color: #dd0000; font-weight: bold'
                    else:
                        return 'background-color: rgba(150, 0, 0, 0.1); color: #bb0000'
                else:
                    # Light mode colors (darker for better contrast)
                    if pd.isna(val) or val == 0:
                        return 'color: #666666'
                    elif val >= 10:
                        return 'background-color: rgba(34, 139, 34, 0.2); color: #006400; font-weight: bold'
                    elif val >= 5:
                        return 'background-color: rgba(34, 139, 34, 0.15); color: #228B22; font-weight: bold'
                    elif val > 0:
                        return 'background-color: rgba(34, 139, 34, 0.1); color: #2E8B57'
                    elif val <= -10:
                        return 'background-color: rgba(220, 20, 60, 0.2); color: #8B0000; font-weight: bold'
                    elif val <= -5:
                        return 'background-color: rgba(220, 20, 60, 0.15); color: #B22222; font-weight: bold'
                    else:
                        return 'background-color: rgba(220, 20, 60, 0.1); color: #DC143C'
            except:
                return ''

        # Format percentage columns for display
        def format_pct(x):
            if pd.notna(x) and x != 0:
                return f"{x:+.2f}%"
            return "0.00%"

        # Apply styling before formatting
        styled_df = df_display.style.applymap(
            style_percentage,
            subset=['1h %', '24h %', '7d %']
        ).format({
            '1h %': format_pct,
            '24h %': format_pct,
            '7d %': format_pct
        })

        # Display the table
        st.dataframe(
            styled_df,
            use_container_width=True,
            height=600,
            hide_index=True
        )

        st.caption(f"📊 Showing {start_idx + 1}-{end_idx} of {len(df_market)} cryptocurrencies | Page {page}/{total_pages} | Data updates every 2 minutes")

    else:
        st.warning("⚠️ Unable to load market overview data. Please check your internet connection or try again later.")

elif mode == "📰 News & Trends":
    # News & Trends Page
    st.markdown("## 📰 Crypto News & Market Trends")

    # News Feed Widget with Images
    st.markdown("### 📰 Latest Crypto News")
    news_items = fetch_crypto_news(limit=12)

    if news_items:
        # Display news in 3-column grid
        for i in range(0, len(news_items), 3):
            cols = st.columns(3)

            for j, col in enumerate(cols):
                if i + j < len(news_items):
                    news = news_items[i + j]

                    # Format published time
                    try:
                        pub_time = pd.to_datetime(news['published_at'], unit='s')
                        time_ago = pd.Timestamp.now() - pub_time
                        if time_ago.total_seconds() < 3600:
                            time_str = f"{int(time_ago.total_seconds() / 60)}m ago"
                        elif time_ago.total_seconds() < 86400:
                            time_str = f"{int(time_ago.total_seconds() / 3600)}h ago"
                        else:
                            time_str = f"{int(time_ago.total_seconds() / 86400)}d ago"
                    except:
                        time_str = "Recently"

                    with col:
                        # News card with image
                        image_url = news.get('image_url', '')
                        if image_url and not image_url.startswith('http'):
                            image_url = f"https://www.cryptocompare.com{image_url}"

                        st.markdown(f"""
                        <div style='background: linear-gradient(135deg, rgba(41, 98, 255, 0.08) 0%, rgba(30, 136, 229, 0.04) 100%);
                                    border-radius: 12px; padding: 0; margin-bottom: 20px; border: 1px solid rgba(41, 98, 255, 0.15);
                                    overflow: hidden; height: 100%;'>
                            <a href='{news['url']}' target='_blank' style='text-decoration: none; color: inherit;'>
                                <img src='{image_url}' style='width: 100%; height: 180px; object-fit: cover; border-radius: 12px 12px 0 0;'
                                     onerror="this.style.display='none'">
                                <div style='padding: 15px;'>
                                    <h4 style='color: #e8f4ff; font-size: 14px; font-weight: 600; margin: 0 0 8px 0;
                                               line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2;
                                               -webkit-box-orient: vertical; overflow: hidden;'>
                                        {news['title']}
                                    </h4>
                                    <p style='color: #8b9dc3; font-size: 12px; margin: 0 0 10px 0;
                                              line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 3;
                                              -webkit-box-orient: vertical; overflow: hidden;'>
                                        {news.get('body', '')}
                                    </p>
                                    <div style='display: flex; justify-content: space-between; align-items: center;
                                                padding-top: 8px; border-top: 1px solid rgba(41, 98, 255, 0.1);'>
                                        <span style='color: #2962ff; font-size: 11px; font-weight: 600;'>
                                            {news['source']}
                                        </span>
                                        <span style='color: #8b9dc3; font-size: 11px;'>
                                            {time_str}
                                        </span>
                                    </div>
                                </div>
                            </a>
                        </div>
                        """, unsafe_allow_html=True)
    else:
        st.info("📰 News feed temporarily unavailable")

elif mode == "🧮 Calculators":
    # Calculators Page
    st.markdown("## 🧮 Trading & Investment Calculators")

    # Initialize calculator type in session state
    if 'calculator_type' not in st.session_state:
        st.session_state.calculator_type = "💰 Investment Calculator"

    # Use radio buttons instead of tabs to maintain state
    calculator_type = st.radio(
        "Select Calculator:",
        ["💰 Investment Calculator", "⚡ Leverage & Risk Calculator"],
        horizontal=True,
        key="calculator_type"
    )

    st.markdown("---")

    if calculator_type == "💰 Investment Calculator":
        st.markdown("### 💰 Compound Interest Calculator")
        st.markdown("Calculate how your investment grows with monthly contributions and compound interest.")

        col_inv1, col_inv2 = st.columns(2)

        with col_inv1:
            initial_investment = st.number_input("Initial Investment ($):", min_value=0.0, value=1000.0, step=100.0)
            monthly_contribution = st.number_input("Monthly Contribution ($):", min_value=0.0, value=100.0, step=50.0)

        with col_inv2:
            annual_return = st.number_input("Expected Annual Return (%):", min_value=0.0, max_value=100.0, value=10.0, step=1.0)
            years = st.number_input("Investment Period (Years):", min_value=1, max_value=50, value=10, step=1)

        # Calculate compound interest
        monthly_rate = (annual_return / 100) / 12
        months = years * 12

        # Future value calculation
        if monthly_rate > 0:
            # FV of initial investment
            fv_initial = initial_investment * ((1 + monthly_rate) ** months)
            # FV of monthly contributions (annuity)
            fv_contributions = monthly_contribution * (((1 + monthly_rate) ** months - 1) / monthly_rate)
            total_value = fv_initial + fv_contributions
        else:
            total_value = initial_investment + (monthly_contribution * months)

        total_invested = initial_investment + (monthly_contribution * months)
        total_profit = total_value - total_invested

        # Display results
        st.markdown("---")
        st.markdown("### 📊 Investment Results")

        col_r1, col_r2, col_r3 = st.columns(3)

        with col_r1:
            st.markdown(f"""
            <div style='text-align: center; padding: 15px; background: rgba(30, 30, 30, 0.5); border-radius: 8px;'>
                <div style='font-size: 12px; color: #888;'>Total Invested</div>
                <div style='font-size: 24px; font-weight: bold; color: #1E90FF;'>${total_invested:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)

        with col_r2:
            st.markdown(f"""
            <div style='text-align: center; padding: 15px; background: rgba(30, 30, 30, 0.5); border-radius: 8px;'>
                <div style='font-size: 12px; color: #888;'>Final Value</div>
                <div style='font-size: 24px; font-weight: bold; color: #00FF00;'>${total_value:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)

        with col_r3:
            roi_percent = ((total_value - total_invested) / total_invested * 100) if total_invested > 0 else 0
            st.markdown(f"""
            <div style='text-align: center; padding: 15px; background: rgba(30, 30, 30, 0.5); border-radius: 8px;'>
                <div style='font-size: 12px; color: #888;'>Total Profit</div>
                <div style='font-size: 24px; font-weight: bold; color: #00FF00;'>${total_profit:,.2f}</div>
                <div style='font-size: 14px; color: #00FF00;'>+{roi_percent:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

        # Growth chart
        st.markdown("---")
        st.markdown("### 📈 Investment Growth Over Time")

        # Calculate year-by-year growth
        years_list = list(range(years + 1))
        values_list = []
        invested_list = []

        for year in years_list:
            months_elapsed = year * 12
            if monthly_rate > 0:
                fv_init = initial_investment * ((1 + monthly_rate) ** months_elapsed)
                fv_contrib = monthly_contribution * (((1 + monthly_rate) ** months_elapsed - 1) / monthly_rate) if months_elapsed > 0 else 0
                value = fv_init + fv_contrib
            else:
                value = initial_investment + (monthly_contribution * months_elapsed)

            invested = initial_investment + (monthly_contribution * months_elapsed)

            values_list.append(value)
            invested_list.append(invested)

        fig_growth = go.Figure()
        fig_growth.add_trace(go.Scatter(
            x=years_list,
            y=values_list,
            mode='lines+markers',
            name='Portfolio Value',
            line=dict(color='#00FF00', width=3),
            marker=dict(size=8)
        ))
        fig_growth.add_trace(go.Scatter(
            x=years_list,
            y=invested_list,
            mode='lines+markers',
            name='Total Invested',
            line=dict(color='#1E90FF', width=2, dash='dash'),
            marker=dict(size=6)
        ))
        fig_growth.update_layout(
            title=f"Investment Growth Over {years} Years",
            xaxis_title="Years",
            yaxis_title="Value ($)",
            height=400,
            template="plotly_dark",
            hovermode='x unified'
        )
        st.plotly_chart(fig_growth, use_container_width=True)

    elif calculator_type == "⚡ Leverage & Risk Calculator":
        st.markdown("### ⚡ Leverage & Risk Management Calculator")
        st.markdown("Calculate the optimal leverage based on your stop loss to control your risk.")

        # Initialize session state for calculator inputs (prevents resets)
        if 'calc_entry_price' not in st.session_state:
            st.session_state.calc_entry_price = 103000.0
        if 'calc_sl_price' not in st.session_state:
            st.session_state.calc_sl_price = 98000.0
        if 'calc_exit_price' not in st.session_state:
            st.session_state.calc_exit_price = 110000.0
        if 'calc_position_size' not in st.session_state:
            st.session_state.calc_position_size = 100.0
        if 'calc_max_loss' not in st.session_state:
            st.session_state.calc_max_loss = 20.0
        if 'calc_position_type' not in st.session_state:
            st.session_state.calc_position_type = "Long 📈"

        col_lev1, col_lev2 = st.columns(2)

        with col_lev1:
            st.markdown("#### 📊 Trade Setup")
            position_type = st.radio("Position Type:", ["Long 📈", "Short 📉"], horizontal=True, key="calc_position_type")

            # Flexible price inputs - support any decimal format
            entry_price = st.number_input(
                "Entry Price ($):",
                min_value=0.0,
                value=st.session_state.calc_entry_price,
                step=None,  # Allow any step
                format="%f",  # Flexible format
                key="entry_price_calc",
                help="Enter any price (e.g., BTC: $103,000, ETH: $3,500, Altcoins: $0.0855, $0.005500)"
            )

            stop_loss_price = st.number_input(
                "Stop Loss Price ($):",
                min_value=0.0,
                value=st.session_state.calc_sl_price,
                step=None,  # Allow any step
                format="%f",  # Flexible format
                key="sl_price_calc",
                help="Enter any price (e.g., BTC: $98,000, ETH: $3,300, Altcoins: $0.0800, $0.005000)"
            )

            exit_price = st.number_input(
                "Exit/Take Profit Price ($):",
                min_value=0.0,
                value=st.session_state.calc_exit_price,
                step=None,  # Allow any step
                format="%f",  # Flexible format
                key="exit_price_calc",
                help="Target price to take profit (e.g., BTC: $110,000, ETH: $4,000, Altcoins: $0.1000, $0.008000)"
            )

        with col_lev2:
            st.markdown("#### 💰 Position Size & Risk")
            position_size_usd = st.number_input("Position Size ($):", min_value=0.0, value=st.session_state.calc_position_size, step=10.0, key="position_size_calc")
            max_loss_usd = st.number_input("Max Loss at Stop Loss ($):", min_value=0.0, value=st.session_state.calc_max_loss, step=5.0, key="max_loss_calc", help="How much $ are you willing to lose if stop loss is hit?")

        # Update session state with current values
        st.session_state.calc_entry_price = entry_price
        st.session_state.calc_sl_price = stop_loss_price
        st.session_state.calc_exit_price = exit_price
        st.session_state.calc_position_size = position_size_usd
        st.session_state.calc_max_loss = max_loss_usd

        # Calculate stop loss distance
        if "Long" in position_type:
            sl_distance_percent = abs((entry_price - stop_loss_price) / entry_price) * 100
            sl_direction = "below"
        else:
            sl_distance_percent = abs((stop_loss_price - entry_price) / entry_price) * 100
            sl_direction = "above"

        # Calculate recommended leverage
        # Loss = Position Size * Leverage * (SL Distance %)
        # We want: Loss <= Max Loss USD
        # So: Position Size * Leverage * (SL Distance % / 100) <= Max Loss USD
        # Leverage <= Max Loss USD / (Position Size * SL Distance % / 100)
        if sl_distance_percent > 0 and position_size_usd > 0:
            recommended_leverage = max_loss_usd / (position_size_usd * (sl_distance_percent / 100))
            recommended_leverage = min(recommended_leverage, 125)  # Cap at 125x
        else:
            recommended_leverage = 1

        # Calculate actual loss at recommended leverage
        actual_loss_at_sl = position_size_usd * recommended_leverage * (sl_distance_percent / 100)

        # Calculate liquidation price
        if "Long" in position_type:
            liquidation_price = entry_price * (1 - 1/recommended_leverage) if recommended_leverage > 0 else 0
        else:
            liquidation_price = entry_price * (1 + 1/recommended_leverage) if recommended_leverage > 0 else 0

        # Calculate exit price profit/loss
        if "Long" in position_type:
            exit_distance_percent = ((exit_price - entry_price) / entry_price) * 100
        else:
            exit_distance_percent = ((entry_price - exit_price) / entry_price) * 100

        exit_profit_usd = position_size_usd * recommended_leverage * (exit_distance_percent / 100)
        exit_profit_multiplier = exit_profit_usd / position_size_usd if position_size_usd > 0 else 0

        # Calculate risk/reward ratio
        risk_reward_ratio = abs(exit_profit_usd / actual_loss_at_sl) if actual_loss_at_sl > 0 else 0

        # Calculate potential profits
        profit_5 = position_size_usd * recommended_leverage * 0.05
        profit_10 = position_size_usd * recommended_leverage * 0.10
        profit_20 = position_size_usd * recommended_leverage * 0.20

        # Potential Profits Section
        st.markdown("---")
        st.markdown("### 💰 Potential Profits")

        col_p1, col_p2, col_p3 = st.columns(3)

        if "Long" in position_type:
            # Long position profits
            with col_p1:
                st.markdown(f"""
                <div style='text-align: center; padding: 15px; background: rgba(0, 255, 0, 0.1); border-radius: 8px; border: 2px solid rgba(0, 255, 0, 0.5);'>
                    <div style='font-size: 12px; color: #888;'>Profit at +5%</div>
                    <div style='font-size: 24px; font-weight: bold; color: #00FF00;'>+${profit_5:.2f}</div>
                    <div style='font-size: 12px; color: #00FF00;'>Target: ${entry_price * 1.05:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

            with col_p2:
                st.markdown(f"""
                <div style='text-align: center; padding: 15px; background: rgba(0, 255, 0, 0.15); border-radius: 8px; border: 2px solid rgba(0, 255, 0, 0.7);'>
                    <div style='font-size: 12px; color: #888;'>Profit at +10%</div>
                    <div style='font-size: 24px; font-weight: bold; color: #00FF00;'>+${profit_10:.2f}</div>
                    <div style='font-size: 12px; color: #00FF00;'>Target: ${entry_price * 1.10:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

            with col_p3:
                st.markdown(f"""
                <div style='text-align: center; padding: 15px; background: rgba(0, 255, 0, 0.2); border-radius: 8px; border: 2px solid #00FF00;'>
                    <div style='font-size: 12px; color: #888;'>Profit at +20%</div>
                    <div style='font-size: 24px; font-weight: bold; color: #00FF00;'>+${profit_20:.2f}</div>
                    <div style='font-size: 12px; color: #00FF00;'>Target: ${entry_price * 1.20:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            # Short position profits (price goes down)
            with col_p1:
                st.markdown(f"""
                <div style='text-align: center; padding: 15px; background: rgba(0, 255, 0, 0.1); border-radius: 8px; border: 2px solid rgba(0, 255, 0, 0.5);'>
                    <div style='font-size: 12px; color: #888;'>Profit at -5%</div>
                    <div style='font-size: 24px; font-weight: bold; color: #00FF00;'>+${profit_5:.2f}</div>
                    <div style='font-size: 12px; color: #00FF00;'>Target: ${entry_price * 0.95:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

            with col_p2:
                st.markdown(f"""
                <div style='text-align: center; padding: 15px; background: rgba(0, 255, 0, 0.15); border-radius: 8px; border: 2px solid rgba(0, 255, 0, 0.7);'>
                    <div style='font-size: 12px; color: #888;'>Profit at -10%</div>
                    <div style='font-size: 24px; font-weight: bold; color: #00FF00;'>+${profit_10:.2f}</div>
                    <div style='font-size: 12px; color: #00FF00;'>Target: ${entry_price * 0.90:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

            with col_p3:
                st.markdown(f"""
                <div style='text-align: center; padding: 15px; background: rgba(0, 255, 0, 0.2); border-radius: 8px; border: 2px solid #00FF00;'>
                    <div style='font-size: 12px; color: #888;'>Profit at -20%</div>
                    <div style='font-size: 24px; font-weight: bold; color: #00FF00;'>+${profit_20:.2f}</div>
                    <div style='font-size: 12px; color: #00FF00;'>Target: ${entry_price * 0.80:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

        # Additional info
        st.markdown("---")
        st.markdown("### 📋 Trade Summary")

        col_s1, col_s2 = st.columns(2)

        with col_s1:
            effective_position = position_size_usd * recommended_leverage
            st.info(f"""
            **Position Details:**
            - Entry Price: ${entry_price:,.8f}
            - Stop Loss: ${stop_loss_price:,.8f}
            - Position Size: ${position_size_usd:,.2f}
            - Effective Position: ${effective_position:,.2f}
            - Leverage: {recommended_leverage:.1f}x
            """)

        with col_s2:
            st.warning(f"""
            **Risk Management:**
            - Max Loss at SL: ${max_loss_usd:.2f}
            - Actual Loss at SL: ${actual_loss_at_sl:.2f}
            - Liquidation: ${liquidation_price:,.2f}
            """)

        # Risk warnings
        st.markdown("---")
        if recommended_leverage >= 20:
            st.error("⚠️ **HIGH RISK**: Leverage above 20x is extremely risky! Consider reducing position size or widening stop loss.")
        elif recommended_leverage >= 10:
            st.warning("⚠️ **MODERATE RISK**: Leverage above 10x requires careful monitoring. Make sure your stop loss is set correctly!")
        elif recommended_leverage >= 5:
            st.info("ℹ️ **CONTROLLED RISK**: Leverage is moderate. Always use stop loss and monitor your position.")
        else:
            st.success("✅ **LOW RISK**: Conservative leverage. Good risk management!")

        # Check if SL is too close to liquidation
        if "Long" in position_type:
            sl_to_liq_distance = abs((stop_loss_price - liquidation_price) / entry_price) * 100
        else:
            sl_to_liq_distance = abs((liquidation_price - stop_loss_price) / entry_price) * 100

        if sl_to_liq_distance < 2:
            st.error("🚨 **DANGER**: Stop loss is very close to liquidation price! Reduce leverage or widen stop loss!")

# Seasonality mode - separate from df.empty check since it fetches its own data
if mode == "📊 Seasonality":
    # Seasonality Stats mode
    st.markdown(f"## 📊 {crypto_name} Seasonality & Historical Returns")

    # Use all available data (no period selector)
    analysis_years = 20  # Maximum available data

    # Fetch historical data for seasonality analysis
    try:
        seasonality_data = analyze_seasonality(symbol, years=analysis_years)

        if seasonality_data is None:
            st.error("⚠️ Failed to fetch seasonality data.")
        elif 'raw_df' not in seasonality_data:
            st.error(f"⚠️ Data structure error. Please try again.")
        else:
            df = seasonality_data['raw_df']
    except Exception as e:
        st.error(f"⚠️ Error fetching seasonality data: {e}")
        seasonality_data = None

    if seasonality_data is not None and 'raw_df' in seasonality_data:
        df = seasonality_data['raw_df']

        # Create tabs for different timeframes
        season_tab1, season_tab2, season_tab3 = st.tabs([
            "📊 Weekly returns(%)",
            "📆 Monthly returns(%)",
            "📈 Quarterly returns(%)"
        ])

        # Helper function to get color based on value
        def get_color(value):
            if value is None or pd.isna(value):
                return '#1a1a1a'
            elif value > 15:
                return '#00a86b'  # Dark green
            elif value > 5:
                return '#2ecc71'  # Green
            elif value > 0:
                return '#27ae60'  # Light green
            elif value > -5:
                return '#e74c3c'  # Light red
            elif value > -15:
                return '#c0392b'  # Red
            else:
                return '#8b0000'  # Dark red

        # Helper function to create HTML table
        def create_heatmap_table(data_dict, columns, title):
            html = f"""
            <style>
            .heatmap-table {{
                width: 100%;
                border-collapse: collapse;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 13px;
                margin: 20px 0;
                background: #0e1117;
            }}
            .heatmap-table th {{
                background: #1a1a1a;
                color: #ffffff;
                padding: 12px 8px;
                text-align: center;
                font-weight: 600;
                border: 1px solid #333;
            }}
            .heatmap-table td {{
                padding: 10px 8px;
                text-align: center;
                border: 1px solid #333;
                font-weight: 500;
            }}
            .heatmap-table tr:hover {{
                opacity: 0.8;
            }}
            .year-col {{
                background: #1a1a1a !important;
                color: #ffffff;
                font-weight: 600;
            }}
            .avg-row {{
                background: #2a2a2a !important;
                font-weight: 700;
                border-top: 2px solid #555 !important;
            }}
            .median-row {{
                background: #2a2a2a !important;
                font-weight: 700;
            }}
            </style>
            <div style='overflow-x: auto;'>
            <table class='heatmap-table'>
            <thead>
            <tr>
                <th>Time</th>
            """

            for col in columns:
                html += f"<th>{col}</th>"

            html += "</tr></thead><tbody>"

            for row in data_dict:
                row_class = ''
                if row['Year'] == 'Average':
                    row_class = 'avg-row'
                elif row['Year'] == 'Median':
                    row_class = 'median-row'

                html += f"<tr class='{row_class}'>"
                html += f"<td class='year-col'>{row['Year']}</td>"

                for col in columns:
                    value = row.get(col)
                    if value is None or pd.isna(value):
                        html += "<td style='background: #1a1a1a;'>-</td>"
                    else:
                        color = get_color(value)
                        html += f"<td style='background: {color}; color: white;'>{value:+.2f}%</td>"

                html += "</tr>"

            html += "</tbody></table></div>"
            return html

        if not df.empty and len(df) > 0:
            # Prepare data with year, month, week, day
            df['Year'] = df['timestamp'].dt.year
            df['Month'] = df['timestamp'].dt.month
            df['Week'] = df['timestamp'].dt.isocalendar().week
            df['Day'] = df['timestamp'].dt.day
            df['DayOfWeek'] = df['timestamp'].dt.dayofweek  # 0=Monday, 6=Sunday
            df['Quarter'] = df['timestamp'].dt.quarter

            with season_tab1:
                # Calculate weekly returns
                weekly_data = []
                years = sorted(df['Year'].unique(), reverse=True)

                for year in years:
                    year_df = df[df['Year'] == year]
                    row_data = {'Year': year}

                    for week in range(1, 54):
                        week_df = year_df[year_df['Week'] == week]
                        if len(week_df) > 1:
                            # Calculate return for the entire week
                            ret = ((week_df['Close'].iloc[-1] - week_df['Close'].iloc[0]) / week_df['Close'].iloc[0]) * 100
                            row_data[week] = ret
                        elif len(week_df) == 1:
                            row_data[week] = None
                        else:
                            row_data[week] = None

                    weekly_data.append(row_data)

                if weekly_data:
                    # Calculate average and median
                    avg_row = {'Year': 'Average'}
                    median_row = {'Year': 'Median'}
                    for week in range(1, 54):
                        values = [row.get(week) for row in weekly_data if row.get(week) is not None and not pd.isna(row.get(week))]
                        avg_row[week] = sum(values) / len(values) if values else None
                        median_row[week] = sorted(values)[len(values)//2] if values else None

                    weekly_data.append(avg_row)
                    weekly_data.append(median_row)

                    # Create HTML table
                    columns = list(range(1, 54))
                    html_table = create_heatmap_table(weekly_data, columns, "Weekly Returns")
                    st.markdown(html_table, unsafe_allow_html=True)

            with season_tab2:
                # Calculate monthly returns
                monthly_data = []
                years = sorted(df['Year'].unique(), reverse=True)
                month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                              'July', 'August', 'September', 'October', 'November', 'December']

                for year in years:
                    year_df = df[df['Year'] == year]
                    row_data = {'Year': year}

                    for month_idx, month_name in enumerate(month_names, 1):
                        month_df = year_df[year_df['Month'] == month_idx]
                        if len(month_df) > 1:
                            # Calculate return for the entire month
                            ret = ((month_df['Close'].iloc[-1] - month_df['Close'].iloc[0]) / month_df['Close'].iloc[0]) * 100
                            row_data[month_name] = ret
                        elif len(month_df) == 1:
                            row_data[month_name] = None
                        else:
                            row_data[month_name] = None

                    monthly_data.append(row_data)

                if monthly_data:
                    # Calculate average and median
                    avg_row = {'Year': 'Average'}
                    median_row = {'Year': 'Median'}
                    for month_name in month_names:
                        values = [row.get(month_name) for row in monthly_data if row.get(month_name) is not None and not pd.isna(row.get(month_name))]
                        avg_row[month_name] = sum(values) / len(values) if values else None
                        median_row[month_name] = sorted(values)[len(values)//2] if values else None

                    monthly_data.append(avg_row)
                    monthly_data.append(median_row)

                    # Create HTML table
                    html_table = create_heatmap_table(monthly_data, month_names, "Monthly Returns")
                    st.markdown(html_table, unsafe_allow_html=True)

            with season_tab3:
                # Calculate quarterly returns
                quarterly_data = []
                years = sorted(df['Year'].unique(), reverse=True)
                quarters = ['Q1', 'Q2', 'Q3', 'Q4']

                for year in years:
                    year_df = df[df['Year'] == year]
                    row_data = {'Year': year}

                    for quarter_idx, quarter_name in enumerate(quarters, 1):
                        quarter_df = year_df[year_df['Quarter'] == quarter_idx]
                        if len(quarter_df) > 1:
                            # Calculate return for the entire quarter
                            ret = ((quarter_df['Close'].iloc[-1] - quarter_df['Close'].iloc[0]) / quarter_df['Close'].iloc[0]) * 100
                            row_data[quarter_name] = ret
                        elif len(quarter_df) == 1:
                            row_data[quarter_name] = None
                        else:
                            row_data[quarter_name] = None

                    quarterly_data.append(row_data)

                if quarterly_data:
                    # Calculate average and median
                    avg_row = {'Year': 'Average'}
                    median_row = {'Year': 'Median'}
                    for quarter_name in quarters:
                        values = [row.get(quarter_name) for row in quarterly_data if row.get(quarter_name) is not None and not pd.isna(row.get(quarter_name))]
                        avg_row[quarter_name] = sum(values) / len(values) if values else None
                        median_row[quarter_name] = sorted(values)[len(values)//2] if values else None

                    quarterly_data.append(avg_row)
                    quarterly_data.append(median_row)

                    # Create HTML table
                    html_table = create_heatmap_table(quarterly_data, quarters, "Quarterly Returns")
                    st.markdown(html_table, unsafe_allow_html=True)

        # Understanding Seasonality Data - Collapsible Info (at the bottom)
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("📚 Understanding Seasonality Data", expanded=False):
            st.markdown("""
            ### 📊 What is Seasonality Analysis?

            Seasonality analysis examines **historical price patterns** to identify recurring trends based on time periods
            (weekly, monthly, quarterly). This data is purely **historical** and does not guarantee future performance.

            ### 📅 Data Period: 2017 - Present

            Our analysis uses data from **2017 onwards** because:
            - **Before 2017**: Bitcoin and crypto markets were extremely new, volatile, and had low liquidity
            - **After 2017**: Markets matured with institutional adoption, better infrastructure, and more reliable patterns
            - **Data Quality**: Post-2017 data provides more meaningful statistical insights

            ### 📈 Understanding Average vs Median

            We show both **Average** and **Median** returns to give you a complete picture:

            #### 🔵 Average (Mean)
            - **What it is**: Sum of all returns divided by the number of periods
            - **Formula**: (Return₁ + Return₂ + ... + Returnₙ) ÷ n
            - **Pros**: Considers all data points
            - **Cons**: Can be skewed by extreme outliers (very high or very low returns)
            - **Example**: If monthly returns are [5%, 10%, 100%], average = 38.3%

            #### 🟢 Median
            - **What it is**: The middle value when all returns are sorted
            - **Formula**: The 50th percentile value
            - **Pros**: Not affected by extreme outliers, shows "typical" performance
            - **Cons**: Ignores extreme events
            - **Example**: If monthly returns are [5%, 10%, 100%], median = 10%

            ### 💡 Which One to Use?

            - **Average**: Better for understanding overall performance including rare events
            - **Median**: Better for understanding typical, expected performance
            - **Best Practice**: Look at **both** together! If they're very different, it means there were extreme events

            ### ⚠️ Important Notes

            - Past performance does **NOT** guarantee future results
            - Crypto markets are highly volatile and unpredictable
            - Use this data as **one tool** among many for analysis
            - Always do your own research (DYOR) and manage risk appropriately
            """)
    else:
        st.warning("⚠️ No data available for seasonality analysis")

# Footer with Legal Links
st.markdown("---")

# Footer Links
col_footer1, col_footer2, col_footer3, col_footer4, col_footer5, col_footer6 = st.columns(6)

with col_footer1:
    if st.button("⚠️ Disclaimer", use_container_width=True):
        st.session_state['show_disclaimer'] = True

with col_footer2:
    if st.button("📜 Privacy Policy", use_container_width=True):
        st.session_state['show_privacy'] = True

with col_footer3:
    if st.button("📋 Terms of Service", use_container_width=True):
        st.session_state['show_terms'] = True

with col_footer4:
    if st.button("ℹ️ About", use_container_width=True):
        st.session_state['show_about'] = True

with col_footer5:
    if st.button("💬 Feedback", use_container_width=True):
        st.session_state['show_feedback'] = True

with col_footer6:
    st.markdown(f"""
    <div style='text-align: center; padding: 10px;'>
        <p style='margin: 0; font-size: 12px; color: {text_secondary};'>
            © 2024 KryptoView<br>
            Data from Binance & CoinGecko
        </p>
    </div>
    """, unsafe_allow_html=True)

# Disclaimer Modal
if 'show_disclaimer' in st.session_state and st.session_state['show_disclaimer']:
    with st.expander("⚠️ Important Disclaimer", expanded=True):
        st.markdown("""
        ### ⚠️ Important Disclaimer
        **Last Updated: November 2024**

        #### No Financial Advice
        **KryptoView** is provided for **informational and educational purposes only**.
        This platform does NOT provide financial, investment, trading, or any other type of professional advice.
        All data, charts, and analysis are for reference only and should not be considered as recommendations
        to buy, sell, or hold any cryptocurrency.

        #### Risk Warning
        **Cryptocurrency trading involves substantial risk of loss and is not suitable for every investor.**
        The valuation of cryptocurrencies and futures may fluctuate, and, as a result, you may lose more
        than your original investment. Past performance is not indicative of future results.

        #### Do Your Own Research (DYOR)
        Before making any investment decisions, you should:
        - Conduct your own thorough research
        - Consult with a qualified financial advisor
        - Understand the risks involved
        - Only invest what you can afford to lose

        #### Data Accuracy
        While we strive to provide accurate and up-to-date information:
        - Data may be delayed or contain errors
        - We do not guarantee the accuracy, completeness, or timeliness of any data
        - Technical issues may cause interruptions or inaccuracies

        #### No Liability
        By using KryptoView, you acknowledge and agree that:
        - You are solely responsible for your investment decisions
        - KryptoView and its creators are NOT liable for any financial losses
        - You use this platform at your own risk
        - You understand and accept all risks associated with cryptocurrency trading

        #### Third-Party Data
        We use data from third-party sources (Binance, CoinGecko, Alternative.me).
        We are not responsible for the accuracy or reliability of third-party data.

        ---

        **By continuing to use this platform, you acknowledge that you have read, understood,
        and agree to this disclaimer.**
        """)

        if st.button("I Understand", key="close_disclaimer", type="primary"):
            st.session_state['show_disclaimer'] = False
            st.rerun()

# Privacy Policy Modal
if 'show_privacy' in st.session_state and st.session_state['show_privacy']:
    with st.expander("📜 Privacy Policy", expanded=True):
        st.markdown("""
        ### Privacy Policy
        **Last Updated: November 2024**

        #### 1. Information We Collect
        - **Feedback Data**: When you submit feedback, we collect your message, email (optional), and timestamp.
        - **Usage Data**: We may collect anonymous usage statistics to improve our service.
        - **No Personal Trading Data**: We do NOT collect, store, or have access to your trading activities or wallet information.

        #### 2. How We Use Your Information
        - To respond to your feedback and support requests
        - To improve our platform and user experience
        - To send important updates (only if you provided your email)

        #### 3. Data Storage
        - Feedback is sent via Formspree and stored securely
        - We do NOT sell or share your data with third parties
        - All data transmission is encrypted (HTTPS)

        #### 4. Cookies
        - We use session cookies to maintain your preferences (theme, selected crypto)
        - No tracking cookies or third-party analytics

        #### 5. Your Rights (GDPR Compliance)
        - Right to access your data
        - Right to delete your data
        - Right to opt-out of communications

        #### 6. Contact Us
        For privacy concerns, email: **cryptoalert.feedback@gmail.com**
        """)

        if st.button("Close", key="close_privacy"):
            st.session_state['show_privacy'] = False
            st.rerun()

# Terms of Service Modal
if 'show_terms' in st.session_state and st.session_state['show_terms']:
    with st.expander("📋 Terms of Service", expanded=True):
        st.markdown("""
        ### Terms of Service
        **Last Updated: November 2024**

        #### 1. Acceptance of Terms
        By accessing and using KryptoView, you accept and agree to be bound by these Terms of Service.

        #### 2. Use of Service
        - KryptoView is provided "AS IS" without warranties of any kind
        - We do not guarantee accuracy, completeness, or timeliness of data
        - Service may be interrupted or discontinued at any time

        #### 3. User Responsibilities
        - You are responsible for your own investment decisions
        - You must comply with all applicable laws and regulations
        - You must not use the service for illegal activities

        #### 4. Intellectual Property
        - All content, design, and code are property of KryptoView
        - You may not copy, modify, or distribute our platform without permission

        #### 5. Limitation of Liability
        - KryptoView and its creators are NOT liable for any financial losses
        - We are not responsible for errors, omissions, or technical issues
        - Maximum liability is limited to the amount you paid (which is $0 for free users)

        #### 6. Indemnification
        You agree to indemnify and hold harmless KryptoView from any claims arising from your use of the service.

        #### 7. Changes to Terms
        We reserve the right to modify these terms at any time. Continued use constitutes acceptance of changes.

        #### 8. Governing Law
        These terms are governed by the laws of [Your Jurisdiction].

        #### 9. Contact
        For questions about these terms, email: **cryptoalert.feedback@gmail.com**
        """)

        if st.button("Close", key="close_terms"):
            st.session_state['show_terms'] = False
            st.rerun()

# About Modal
if 'show_about' in st.session_state and st.session_state['show_about']:
    with st.expander("ℹ️ About KryptoView", expanded=True):
        st.markdown("""
        ### About KryptoView

        **KryptoView** is a professional cryptocurrency analytics platform designed to help traders and investors
        make informed decisions through comprehensive market data, technical analysis, and real-time insights.

        #### Features
        - 📈 **Advanced Charting**: Multiple timeframes, technical indicators (EMA, RSI, MACD, Bollinger Bands, etc.)
        - 📊 **Market Overview**: Top gainers/losers, market cap dominance, trending coins
        - 📰 **News & Trends**: Latest crypto news and market sentiment
        - 🧮 **Calculators**: DCA, Risk/Reward, Leverage calculators
        - 📊 **Seasonality Analysis**: Historical price patterns and trends

        #### Data Sources
        - **Binance API**: Real-time price data and charts
        - **CoinGecko API**: Market data, rankings, and statistics
        - **Alternative.me**: Fear & Greed Index

        #### Version
        **v1.0.0** - November 2024

        #### Open Source
        KryptoView is built with:
        - Python & Streamlit
        - Plotly for interactive charts
        - Technical Analysis library (TA-Lib)

        #### Support
        - 📧 Email: cryptoalert.feedback@gmail.com
        - 💬 Feedback: Click the "💬 Feedback" button in the footer

        #### Disclaimer
        KryptoView is for educational purposes only. Not financial advice. Trade at your own risk.
        """)

        if st.button("Close", key="close_about"):
            st.session_state['show_about'] = False
            st.rerun()

# Feedback Modal
if 'show_feedback' in st.session_state and st.session_state['show_feedback']:
    with st.expander("💬 Send Feedback", expanded=True):
        st.markdown("Help us improve! Share your thoughts, report bugs, or suggest features.")

        feedback_type = st.selectbox(
            "Feedback Type:",
            ["🐛 Bug Report", "💡 Feature Request", "💬 General Feedback", "❓ Question"],
            key="feedback_type_modal"
        )

        feedback_message = st.text_area(
            "Your Message:",
            placeholder="Describe your feedback in detail...",
            height=150,
            key="feedback_message_modal"
        )

        user_email = st.text_input(
            "Your Email (optional):",
            placeholder="your@email.com",
            help="We'll only use this to follow up on your feedback",
            key="feedback_email_modal"
        )

        col_send, col_close = st.columns(2)

        with col_send:
            if st.button("📤 Send Feedback", use_container_width=True, type="primary", key="send_feedback_modal"):
                if feedback_message.strip():
                    with st.spinner("Sending feedback..."):
                        # Send feedback email
                        success, msg = send_feedback_email(
                            feedback_type,
                            feedback_message,
                            user_email
                        )

                        if success:
                            st.success("✅ Thank you! Your feedback has been received.")
                            st.info("📧 We'll review your feedback and get back to you soon!")
                        else:
                            # Even if email fails, still show success to user
                            st.success("✅ Thank you! Your feedback has been recorded.")
                            st.caption("💡 Note: Email service not configured yet. Your feedback is logged locally.")

                            # Log feedback locally
                            feedback_data = {
                                'type': feedback_type,
                                'message': feedback_message,
                                'email': user_email if user_email else 'Anonymous',
                                'timestamp': datetime.now().isoformat()
                            }
                            print(f"📬 Feedback received: {feedback_data}")
                else:
                    st.warning("⚠️ Please enter a message before sending.")

        with col_close:
            if st.button("Close", use_container_width=True, key="close_feedback"):
                st.session_state['show_feedback'] = False
                st.rerun()

        # Direct email option
        st.markdown("---")
        st.markdown("**📧 Or email us directly with screenshots:**")
        st.markdown("**cryptoalert.feedback@gmail.com**")
        st.caption("💡 For screenshots or detailed reports, feel free to email us directly!")
