import warnings, os, yfinance as yf, requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import telegram, asyncio

warnings.filterwarnings("ignore", category=UserWarning)
TOKEN, CHAT_ID = os.environ.get("TOKEN"), os.environ.get("CHAT_ID")

MY_KOR = {"기아": "000270.KS", "두산로보틱스": "454910.KS", "로보스타": "090360.KQ", "오스테오닉": "226400.KQ"}
MY_USA = {"QQQM": "QQQM", "SPYM": "SPYM"}
INDEXES = {"코스피": "^KS11", "코스닥": "^KQ11", "다우": "^DJI", "나스닥": "^IXIC", "S&P500": "^GSPC"}
MACRO = {"환율": "KRW=X", "국채10년": "^TNX"}

def get_data(ticker):
    try:
        s = yf.Ticker(ticker).history(period="5d")
        if s.empty: return None, 0
        curr, prev = s['Close'].iloc[-1], s['Close'].iloc[-2]
        return curr, ((curr - prev) / prev) * 100
    except: return None, 0

def get_news():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        soup = BeautifulSoup(requests.get("https://finance.naver.com/news/main.naver", headers=headers).text, 'html.parser')
        return "".join([f"• {h.text.strip()}\n" for h in soup.select('.articleSubject a')[:5]])
    except: return "뉴스 수집 실패\n"

def get_market_data():
    now = datetime.now() + timedelta(hours=9)
    hour = now.hour
    msg = f"📈 [주식 비서] ({now.strftime('%H:%M')} 기준)\n\n"
    
    # 매크로
    msg += "🌍 [매크로]\n"
    for n, t in MACRO.items():
        v, _ = get_data(t)
        if v: msg += f"- {n}: {v:,.2f}\n"

    # 종목 (미국주식은 티커 그대로 잘 가져옵니다)
    is_kor = 9 <= hour < 16
    target = MY_KOR if is_kor else MY_USA
    msg += f"\n{'🇰🇷 [한국장]' if is_kor else '🇺🇸 [미국장]'}\n"
    for n, t in target.items():
        v, c = get_data(t)
        if v: msg += f"- {n}: {v:,.2f} ({c:+.2f}%)\n"
    
    # 지수
    msg += "\n📊 [주요 지수]\n"
    for n, t in INDEXES.items():
        v, c = get_data(t)
        if v: msg += f"- {n}: {v:,.0f} ({c:+.2f}%)\n"
        
    msg += "\n📰 [시장 이슈]\n" + get_news()
    return msg

async def main():
    bot = telegram.Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=get_market_data())

if __name__ == "__main__":
    asyncio.run(main())
