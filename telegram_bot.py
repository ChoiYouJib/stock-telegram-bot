import warnings, os, yfinance as yf, requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import telegram, asyncio

warnings.filterwarnings("ignore", category=UserWarning)
TOKEN, CHAT_ID = os.environ.get("TOKEN"), os.environ.get("CHAT_ID")

MY_KOR = {"기아": "000270.KS", "두산로보틱스": "454910.KS", "로보스타": "090360.KQ", "오스테오닉": "226400.KQ"}
MY_USA = {"QQQM": "QQQM", "SPYM": "SPYM"}
# 지수 항목 추가
INDEXES = {"코스피": "^KS11", "코스닥": "^KQ11", "다우존스": "^DJI", "나스닥": "^IXIC", "S&P500": "^GSPC"}
MACRO = {"환율(원/달러)": "KRW=X", "미국 10년물 국채금리": "^TNX"}

def get_data(ticker):
    try:
        s = yf.Ticker(ticker).history(period="5d") # 기간을 5일로 늘려 데이터 안정성 확보
        curr, prev = s['Close'].iloc[-1], s['Close'].iloc[-2]
        return curr, ((curr - prev) / prev) * 100
    except: return None, None

def get_news():
    try:
        # 브라우저인 척 위장하여 차단 방지
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = "https://finance.naver.com/news/main.naver"
        soup = BeautifulSoup(requests.get(url, headers=headers).text, 'html.parser')
        headlines = soup.select('.articleSubject a')
        return "".join([f"• {h.text.strip()}\n" for h in headlines[:5]])
    except: return "뉴스 수집 실패\n"

def get_market_data():
    now = datetime.now() + timedelta(hours=9)
    hour = now.hour
    msg = f"📈 [주식 비서 리포트] ({now.strftime('%H:%M')} 기준)\n\n"
    
    msg += "🌍 [중요 매크로 지표]\n"
    for n, t in MACRO.items():
        v, _ = get_data(t)
        if v: msg += f"- {n}: {v:,.2f}\n"

    # 한국/미국 구분 로직
    is_kor = 9 <= hour < 16
    target = MY_KOR if is_kor else MY_USA
    msg += f"\n{'🇰🇷 [한국장' if is_kor else '🇺🇸 [미국장'} 중심 리포트]\n"
        
    for n, t in target.items():
        v, c = get_data(t)
        if v: 
            symbol = "$" if not is_kor else "원"
            msg += f"- {n}: {symbol}{v:,.2f} ({c:+.2f}%)\n"
    
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
