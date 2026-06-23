import warnings, os, yfinance as yf, requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import telegram, asyncio

warnings.filterwarnings("ignore", category=UserWarning)
TOKEN, CHAT_ID = os.environ.get("TOKEN"), os.environ.get("CHAT_ID")

MY_KOR = {"기아": "000270.KS", "두산로보틱스": "454910.KS", "로보스타": "090360.KQ", "오스테오닉": "226400.KQ"}
MY_USA = {"QQQM": "QQQM", "SPYM": "SPYM"}
INDEXES = {"코스피": "^KS11", "코스닥": "^KQ11", "S&P500": "^GSPC", "나스닥100": "^NDX"}
MACRO = {"환율(원/달러)": "KRW=X", "미국 10년물 국채금리": "^TNX"}

def get_data(ticker):
    try:
        s = yf.Ticker(ticker).history(period="2d")
        return s['Close'].iloc[-1], ((s['Close'].iloc[-1]-s['Close'].iloc[-2])/s['Close'].iloc[-2])*100
    except: return None, None

def get_news():
    try:
        url = "https://finance.naver.com/news/main.naver"
        return "".join([f"• {h.text.strip()}\n" for h in BeautifulSoup(requests.get(url).text, 'html.parser').select('.articleSubject a')[:5]])
    except: return "뉴스 수집 실패\n"

def get_market_data():
    now = datetime.now() + timedelta(hours=9) # UTC to KST
    hour = now.hour
    msg = f"📈 [주식 비서 리포트] ({now.strftime('%H:%M')} 기준)\n\n"
    
    # 1. 지표(항상 포함)
    msg += "🌍 [중요 매크로 지표]\n"
    for n, t in MACRO.items():
        val, _ = get_data(t)
        if val: msg += f"- {n}: {val:,.2f}\n"

    # 2. 시간대별 로직
    if hour == 9: # 09:00
        msg += "\n🇰🇷 [한국장 개장] 보유 종목 확인하세요!\n"
        target = MY_KOR
    elif 11 <= hour < 13: # 11:30
        msg += "\n🇰🇷 [한국장 장중 흐름]\n"
        target = MY_KOR
    elif hour == 15: # 15:30
        msg += "\n🏁 [한국장 마감] 결과 및 미국 준비\n"
        target = MY_KOR
    else: # 22:00 or 07:00
        msg += "\n🇺🇸 [미국장 중심 리포트]\n"
        target = MY_USA
        
    for n, t in target.items():
        v, c = get_data(t)
        if v: msg += f"- {n}: {'$' if 'USA' in str(target) else ''}{v:,.0f} ({c:+.2f}%)\n"
    
    msg += "\n📊 [주요 지수]\n"
    for n, t in INDEXES.items():
        v, c = get_data(t)
        if v: msg += f"- {n}: {v:,.0f} ({c:+.2f}%)\n"
        
    msg += "\n📰 [오늘의 시장 이슈]\n" + get_news()
    return msg

async def main():
    bot = telegram.Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=get_market_data())

if __name__ == "__main__":
    asyncio.run(main())
