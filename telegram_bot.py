import warnings, os, yfinance as yf, feedparser
from datetime import datetime, timedelta
import telegram, asyncio

warnings.filterwarnings("ignore", category=UserWarning)
TOKEN, CHAT_ID = os.environ.get("TOKEN"), os.environ.get("CHAT_ID")

# 종목 및 지수 정의
MY_KOR = {"기아": "000270.KS", "두산로보틱스": "454910.KS", "로보스타": "090360.KQ", "오스테오닉": "226400.KQ"}
MY_USA = {"QQQM": "QQQM", "SPYM": "SPYM"}
INDEXES = {"코스피": "^KS11", "코스닥": "^KQ11", "다우존스": "^DJI", "나스닥": "^IXIC", "나스닥100": "^NDX", "S&P500": "^GSPC"}
MACRO = {"환율": "KRW=X", "국채10년": "^TNX"}

# 휴장일 데이터베이스 (날짜 형식: YYYY-MM-DD)
# 실제 공휴일과 증시 휴장일은 다를 수 있으니 증권사 일정에 맞춰 업데이트하세요.
HOLIDAYS_KOR = ["2026-06-06"] 
HOLIDAYS_USA = ["2026-07-03"]

def get_market_status():
    today = datetime.now().strftime('%Y-%m-%d')
    # 한국장/미국장 휴장 여부 확인
    kor_status = "휴장" if today in HOLIDAYS_KOR else "개장/운영"
    usa_status = "휴장" if today in HOLIDAYS_USA else "개장/운영"
    return kor_status, usa_status

def get_data(ticker):
    try:
        ticker_obj = yf.Ticker(ticker)
        s = ticker_obj.history(period="1d", include_prepost=True)
        if s.empty: return None, 0
        curr = s['Close'].iloc[-1]
        prev = ticker_obj.history(period="5d")['Close'].iloc[-2]
        change = ((curr - prev) / prev) * 100
        return curr, change
    except: return None, 0

def check_risk(n, v):
    if "환율" in n and v >= 1400: return " [⚠️ 위험: 고환율]"
    if "국채10년" in n and v >= 4.5: return " [⚠️ 위험: 고금리]"
    return ""

def get_market_news():
    try:
        url = "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(url)
        return "\n".join([f"• {item.title}" for item in feed.entries[:3]])
    except: return "• 시장 이슈 수집 실패"

def get_market_data():
    now = datetime.now() + timedelta(hours=9)
    kor_stat, usa_stat = get_market_status()
    is_kor = 9 <= now.hour < 16
    
    msg = f"🕒 [{now.strftime('%H:%M')} 시장 리포트]\n"
    msg += f"🇰🇷 한국장: {kor_stat} | 🇺🇸 미국장: {usa_stat}\n"
    msg += "(데이터 기준: 종가 및 정규장 외 포함 최신가)\n\n"
    
    msg += "💰 환율&국채\n"
    for n, t in MACRO.items():
        v, c = get_data(t)
        if v: msg += f"- {n}: {v:,.2f} ({c:+.2f}%){check_risk(n, v)}\n"
        
    msg += "\n📊 주요지수\n"
    for n, t in INDEXES.items():
        v, c = get_data(t)
        if v: msg += f"- {n}: {v:,.0f} ({c:+.2f}%)\n"
        
    msg += f"\n{'🇰🇷' if is_kor else '🇺🇸'} 보유종목\n"
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
