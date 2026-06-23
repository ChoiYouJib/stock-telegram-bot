import warnings, os, yfinance as yf, feedparser
from datetime import datetime, timedelta
import telegram, asyncio

warnings.filterwarnings("ignore", category=UserWarning)
TOKEN, CHAT_ID = os.environ.get("TOKEN"), os.environ.get("CHAT_ID")

# 데이터 정의
MY_KOR = {"기아": "000270.KS", "두산로보틱스": "454910.KS", "로보스타": "090360.KQ", "오스테오닉": "226400.KQ"}
MY_USA = {"QQQM": "QQQM", "SPYM": "SPYM"}
INDEXES = {"코스피": "^KS11", "코스닥": "^KQ11", "다우존스": "^DJI", "나스닥": "^IXIC", "나스닥100": "^NDX", "S&P500": "^GSPC"}
# 헤더 이름 변경: 매크로 -> 경제 핵심 지표
ECONOMIC_INDICATORS = {"환율": "KRW=X", "국채10년": "^TNX"}

# 휴장일 안내를 위한 데이터
HOLIDAYS_INFO = {
    6: "06일(현충일)",
    7: "03일(미국 독립기념일 대체)",
    8: "15일(광복절)"
}

def get_market_status():
    now = datetime.now() + timedelta(hours=9)
    # 09:00~15:30 한국장, 22:30~05:00 미국장 기준
    kor_open = (9 <= now.hour < 15)
    usa_open = (now.hour >= 22 or now.hour < 5)
    return ("🇰🇷 한국장: 개장 중" if kor_open else "🇰🇷 한국장: 종료/휴장"), \
           ("🇺🇸 미국장: 개장 중" if usa_open else "🇺🇸 미국장: 종료/휴장")

def get_data(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="2d")
        if df.empty: return None, 0
        curr = df['Close'].iloc[-1]
        prev = df['Close'].iloc[-2]
        return curr, ((curr - prev) / prev) * 100
    except: return None, 0

def get_market_data():
    now = datetime.now() + timedelta(hours=9)
    kor_stat, usa_stat = get_market_status()
    
    msg = f"🕒 [{now.strftime('%H:%M')} 시장 리포트]\n"
    msg += f"{kor_stat} | {usa_stat}\n\n"
    
    # 1. 경제 핵심 지표
    msg += "💰 경제 핵심 지표 (지연 20분)\n"
    for n, t in ECONOMIC_INDICATORS.items():
        v, c = get_data(t)
        if v: msg += f"- {n}: {v:,.2f} ({c:+.2f}%)\n"
        
    # 2. 주요 지수
    msg += "\n📊 주요 지수 (지연 20분)\n"
    for n, t in INDEXES.items():
        v, c = get_data(t)
        if v: msg += f"- {n}: {v:,.0f} ({c:+.2f}%)\n"
        
    # 3. 보유 종목
    msg += "\n📈 보유 종목 (종가 기준)\n"
    target = MY_KOR if (9 <= now.hour < 16) else MY_USA
    for n, t in target.items():
        v, c = get_data(t)
        if v: msg += f"- {n}: {v:,.2f} ({c:+.2f}%)\n"
        
    # 4. 휴장일 안내 (새로운 UI 섹션)
    msg += f"\n📅 {now.month}월 휴장 예정일\n"
    msg += f"- {HOLIDAYS_INFO.get(now.month, '이번 달 휴장일 없음')}\n"
    
    # 5. 시장 이슈
    try:
        news = feedparser.parse("https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=ko&gl=KR&ceid=KR:ko")
        msg += "\n📰 시장 주요 이슈\n" + "\n".join([f"• {i.title}" for i in news.entries[:3]])
    except: msg += "\n📰 시장 주요 이슈: 정보 없음"
    
    return msg

async def main():
    if not TOKEN or not CHAT_ID: return
    bot = telegram.Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=get_market_data())

if __name__ == "__main__":
    asyncio.run(main())
