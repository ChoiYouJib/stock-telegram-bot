import warnings, os, yfinance as yf, feedparser
from datetime import datetime, timedelta
import telegram, asyncio

warnings.filterwarnings("ignore", category=UserWarning)
TOKEN, CHAT_ID = os.environ.get("TOKEN"), os.environ.get("CHAT_ID")

# 데이터 정의
MY_KOR = {"기아": "000270.KS", "두산로보틱스": "454910.KS", "로보스타": "090360.KQ", "오스테오닉": "226400.KQ"}
MY_USA = {"QQQM": "QQQM", "SPYM": "SPYM"}
INDEXES = {"코스피": "^KS11", "코스닥": "^KQ11", "다우존스": "^DJI", "나스닥": "^IXIC", "나스닥100": "^NDX", "S&P500": "^GSPC"}

# 경제 지표 명칭 변경
ECONOMIC_INDICATORS = {"환율(원/달러)": "KRW=X", "10년채 금리": "^TNX"}

# 휴장일 데이터 (YYYY-MM-DD)
HOLIDAYS_KOR = ["2026-06-06"] 
HOLIDAYS_USA = ["2026-07-03"]
MONTHLY_HOLIDAYS = {6: "06일(한국:현충일)", 7: "03일(미국:독립기념일)", 8: "15일(한국:광복절)"}

def get_market_status():
    now = datetime.now() + timedelta(hours=9)
    today = now.strftime('%Y-%m-%d')
    
    # 한국장 상태 판별
    if today in HOLIDAYS_KOR: kor_stat = "휴장"
    elif now.hour < 9: kor_stat = "장 시작 전"
    elif 9 <= now.hour < 15: kor_stat = "개장 중"
    else: kor_stat = "장 종료"
    
    # 미국장 상태 판별
    if today in HOLIDAYS_USA: usa_stat = "휴장"
    elif 5 <= now.hour < 22: usa_stat = "장 시작 전"
    elif 22 <= now.hour or now.hour < 5: usa_stat = "개장 중"
    else: usa_stat = "장 종료"
    
    return kor_stat, usa_stat

def get_data(ticker):
    try:
        t = yf.Ticker(ticker)
        # period를 5d(5일)로 늘려 데이터가 없는 날이 있더라도 최근 값을 확실히 잡도록 함
        df = t.history(period="5d")
        if df.empty: return None, 0
        
        # 유효한 마지막 데이터 가져오기
        curr = df['Close'].dropna().iloc[-1]
        prev = df['Close'].dropna().iloc[-2]
        
        return curr, ((curr - prev) / prev) * 100
    except Exception as e:
        # 오류가 나면 None을 반환하여 리스트에서 제외
        return None, 0

def get_market_data():
    now = datetime.now() + timedelta(hours=9)
    kor_stat, usa_stat = get_market_status()
    
    msg = f"🕒 [{now.strftime('%H:%M')} 시장 리포트]\n"
    msg += f"🇰🇷 한국장: {kor_stat} | 🇺🇸 미국장: {usa_stat}\n\n"
    
    msg += "💰 환율 & 10년채\n"
    for n, t in ECONOMIC_INDICATORS.items():
        v, c = get_data(t)
        if v: msg += f"- {n}: {v:,.2f} ({c:+.2f}%)\n"
        
    msg += "\n📊 주요 지수 (지연 20분)\n"
    for n, t in INDEXES.items():
        v, c = get_data(t)
        if v: msg += f"- {n}: {v:,.0f} ({c:+.2f}%)\n"
        
    msg += "\n📈 보유 종목 (종가 기준)\n"
    target = MY_KOR if (9 <= now.hour < 16) else MY_USA
    for n, t in target.items():
        v, c = get_data(t)
        if v: msg += f"- {n}: {v:,.2f} ({c:+.2f}%)\n"
        
    msg += f"\n📅 {now.month}월 휴장 예정일\n"
    msg += f"- {MONTHLY_HOLIDAYS.get(now.month, '없음')}\n"
    
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
