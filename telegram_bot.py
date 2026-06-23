import warnings, os, yfinance as yf, requests, feedparser
from datetime import datetime, timedelta
import telegram, asyncio

warnings.filterwarnings("ignore", category=UserWarning)
TOKEN, CHAT_ID = os.environ.get("TOKEN"), os.environ.get("CHAT_ID")

# 종목 및 지수 정의
MY_KOR = {"기아": "000270.KS", "두산로보틱스": "454910.KS", "로보스타": "090360.KQ", "오스테오닉": "226400.KQ"}
MY_USA = {"QQQM": "QQQM", "SPYM": "SPYM"}
INDEXES = {"코스피": "^KS11", "코스닥": "^KQ11", "다우존스": "^DJI", "나스닥": "^IXIC", "나스닥100": "^NDX", "S&P500": "^GSPC"}
MACRO = {"환율(원/달러)": "KRW=X", "미국 10년물 국채금리": "^TNX"}

def get_data(ticker):
    try:
        # 실시간에 가장 가까운 최신 호가 데이터 수집
        s = yf.Ticker(ticker).history(period="1d", interval="1m")
        if s.empty: return None, 0
        curr = s['Close'].iloc[-1]
        prev = yf.Ticker(ticker).history(period="5d")['Close'].iloc[-2]
        return curr, ((curr - prev) / prev) * 100
    except: return None, 0

def get_market_news():
    # 구글 뉴스 RSS를 통해 시장 전반의 주요 이슈 수집
    try:
        url = "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(url)
        return "\n".join([f"• {item.title}" for item in feed.entries[:4]])
    except: return "• 시장 이슈 수집 실패"

def get_market_data():
    now = datetime.now() + timedelta(hours=9)
    hour = now.hour
    is_kor = 9 <= hour < 16
    
    msg = f"🕒 [{now.strftime('%H:%M')} 시장 리포트]\n\n"
    
    msg += "💰 환율 & 국채\n"
    for n, t in MACRO.items():
        v, _ = get_data(t)
        if v: msg += f"- {n}: {v:,.2f}\n"
        
    msg += "\n📊 주요지수\n"
    for n, t in INDEXES.items():
        v, c = get_data(t)
        if v: msg += f"- {n}: {v:,.0f} ({c:+.2f}%)\n"
        
    msg += f"\n{'🇰🇷' if is_kor else '🇺🇸'} 시간별 증시 보유종목\n"
    target = MY_KOR if is_kor else MY_USA
    for n, t in target.items():
        v, c = get_data(t)
        if v: msg += f"- {n}: {'원' if is_kor else '$'}{v:,.2f} ({c:+.2f}%)\n"
        
    msg += "\n📰 시장 이슈\n" + get_market_news()
    return msg

async def main():
    if not TOKEN or not CHAT_ID: return
    bot = telegram.Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=get_market_data())

if __name__ == "__main__":
    asyncio.run(main())
