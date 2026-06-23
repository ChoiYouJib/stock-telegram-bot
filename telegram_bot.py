import warnings
import telegram
import asyncio
import yfinance as yf
import pandas_market_calendars as pmc
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 경고 메시지(UserWarning)가 터미널을 막지 않도록 억제
warnings.filterwarnings("ignore", category=UserWarning)

# 설정
TOKEN = "8939072148:AAGGQa2ygvC1mFuZpdHPzab94MmWy0d3bcs"
CHAT_ID = "8840190327"

MY_KOR = {"기아": "000270.KS", "두산로보틱스": "454910.KS", "로보스타": "090360.KQ", "오스테오닉": "226400.KQ"}
MY_USA = {"QQQM": "QQQM", "SPYM": "SPYM"}
INDEXES = {"코스피": "^KS11", "코스닥": "^KQ11", "S&P500": "^GSPC", "나스닥100": "^NDX"}
MACRO = {"환율(원/달러)": "KRW=X", "미국 10년물 국채금리": "^TNX"}

def get_market_status():
    today = datetime.now()
    try:
        krx = pmc.get_calendar('XKRX')
        nyse = pmc.get_calendar('NYSE')
        kr_open = not krx.schedule(start_date=today, end_date=today).empty
        us_open = not nyse.schedule(start_date=today, end_date=today).empty
        return f"📅 한국: {'개장' if kr_open else '휴장'} | 미국: {'개장' if us_open else '휴장'}"
    except:
        return "📅 증시 운영 확인 불가"

def get_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="2d")
        if len(data) < 2: return None, None
        curr = data['Close'].iloc[-1]
        prev = data['Close'].iloc[-2]
        change = ((curr - prev) / prev) * 100
        return curr, change
    except:
        return None, None

def get_market_news():
    try:
        url = "https://finance.naver.com/news/main.naver"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        headlines = soup.select('.articleSubject a')
        return "".join([f"• {h.text.strip()}\n" for h in headlines[:5]])
    except:
        return "• 뉴스 정보를 가져올 수 없습니다.\n"

def get_market_data():
    msg = f"📈 [주식 비서 일일 보고]\n{get_market_status()}\n\n🌍 [매크로 지표]\n"
    for name, ticker in MACRO.items():
        curr, _ = get_price(ticker)
        if curr: msg += f"- {name}: {curr:,.2f}\n"

    msg += "\n💰 [보유 종목]\n"
    for name, ticker in MY_KOR.items():
        curr, change = get_price(ticker)
        if curr: msg += f"- {name}: {curr:,.0f}원 ({change:+.2f}%)\n"
    for name, ticker in MY_USA.items():
        curr, change = get_price(ticker)
        if curr: msg += f"- {name}: ${curr:,.2f} ({change:+.2f}%)\n"
    
    msg += "\n📊 [주요 지수]\n"
    for name, ticker in INDEXES.items():
        curr, change = get_price(ticker)
        if curr: msg += f"- {name}: {curr:,.0f} ({change:+.2f}%)\n"
        
    msg += "\n📰 [시장 주요 흐름]\n"
    msg += get_market_news()
    msg += "\n💡 오늘도 성공적인 투자 하세요!"
    return msg

async def main():
    bot = telegram.Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=get_market_data())

if __name__ == "__main__":
    asyncio.run(main())