import warnings, os, yfinance as yf, requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import telegram, asyncio

warnings.filterwarnings("ignore", category=UserWarning)
TOKEN, CHAT_ID = os.environ.get("TOKEN"), os.environ.get("CHAT_ID")

# 티커 수정: 인덱스는 yfinance에서 더 안정적인 티커로 변경
MY_KOR = {"기아": "000270.KS", "두산로보틱스": "454910.KS", "로보스타": "090360.KQ", "오스테오닉": "226400.KQ"}
MY_USA = {"QQQM": "QQQM", "SPYM": "SPYM"}
INDEXES = {"코스피": "^KS11", "코스닥": "^KQ11", "다우": "^DJI", "나스닥": "^IXIC", "S&P500": "^GSPC", "나스닥100": "^NDX"}
MACRO = {"환율(원/달러)": "KRW=X", "미국 10년물 국채금리": "^TNX"}

def get_data(ticker):
    try:
        # 데이터가 없을 경우를 대비해 기간을 늘리고, 유효 데이터 확인
        s = yf.Ticker(ticker).history(period="5d")
        if s.empty: return None, None
        curr, prev = s['Close'].iloc[-1], s['Close'].iloc[-2]
        return curr, ((curr - prev) / prev) * 100
    except: return None, None

def get_news():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = "https://finance.naver.com/news/main.naver"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        # 뉴스 제목이 없는 경우 방지
        headlines = soup.select('.articleSubject a')
        return "".join([f"• {h.text.strip()}\n" for h in headlines[:5] if h.text.strip()])
    except: return "뉴스 수집 실패\n"

def get_market_data():
    now = datetime.now() + timedelta(hours=9)
    hour = now.hour
    msg = f"📈 [주식 비서 리포트] ({now.strftime('%H:%M')} 기준)\n\n"
    
    # 매크로
    msg += "🌍 [중요 매크로 지표]\n"
    for n, t in MACRO.items():
        v, _ = get_data(t)
        msg += f"- {n}: {v:,.2f if '국채' not in n else 3.2f}\n"

    # 구분
    is_kor = 9 <= hour < 16
    target = MY_KOR if is_kor else MY_USA
    msg += f"\n{'🇰🇷 [한국장' if is_kor else '🇺🇸 [미국장'} 보유 종목]\n"
        
    for n, t in target.items():
        v, c = get_data(t)
        if v:
            # 원화/달러 구분
            unit = "원" if is_kor else "$"
            msg += f"- {n}: {unit}{v:,.2f} ({c:+.2f}%)\n"
    
    msg += "\n📊 [주요 지수]\n"
    for n, t in INDEXES.items():
        v, c = get_data(t)
        if v: msg += f"- {n}: {v:,.0f} ({c:+.2f}%)\n"
        
    msg += "\n📰 [시장 주요 이슈]\n" + get_news()
    return msg

async def main():
    if not TOKEN or not CHAT_ID: return
    bot = telegram.Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=get_market_data())

if __name__ == "__main__":
    asyncio.run(main())
