import warnings, os, yfinance as yf
from datetime import datetime, timedelta
import telegram, asyncio

# 경고 무시 및 환경변수 설정
warnings.filterwarnings("ignore", category=UserWarning)
TOKEN, CHAT_ID = os.environ.get("TOKEN"), os.environ.get("CHAT_ID")

# 종목 및 지수 정의
MY_KOR = {"기아": "000270.KS", "두산로보틱스": "454910.KS", "로보스타": "090360.KQ", "오스테오닉": "226400.KQ"}
MY_USA = {"QQQM": "QQQM", "SPYM": "SPYM"}
INDEXES = {"코스피": "^KS11", "코스닥": "^KQ11", "다우": "^DJI", "나스닥": "^IXIC", "나스닥100": "^NDX", "S&P500": "^GSPC"}
MACRO = {"환율": "KRW=X", "국채10년": "^TNX"}

def get_data(ticker):
    try:
        # 데이터 수집 (야후 파이낸스)
        s = yf.Ticker(ticker).history(period="5d")
        if s.empty: return None, 0
        curr, prev = s['Close'].iloc[-1], s['Close'].iloc[-2]
        return curr, ((curr - prev) / prev) * 100
    except: return None, 0

def get_market_news():
    # 야후 파이낸스에서 시장 뉴스를 안정적으로 가져오기
    try:
        news = yf.Ticker("QQQM").news # QQQM 관련 최신 뉴스를 샘플로 활용
        return "\n".join([f"• {n['title']}" for n in news[:5]])
    except: return "• 시장 이슈 수집 중..."

def get_market_data():
    now = datetime.now() + timedelta(hours=9)
    hour = now.hour
    is_kor = 9 <= hour < 16
    
    msg = f"📈 [주식 비서 리포트] ({now.strftime('%H:%M')} KST)\n\n"
    
    # 매크로
    msg += "🌍 [매크로 지표]\n"
    for n, t in MACRO.items():
        v, _ = get_data(t)
        if v: msg += f"- {n}: {v:,.2f}\n"

    # 종목 (한국/미국 자동 구분)
    target = MY_KOR if is_kor else MY_USA
    msg += f"\n{'🇰🇷 [한국장 보유]' if is_kor else '🇺🇸 [미국장 보유]'}\n"
    for n, t in target.items():
        v, c = get_data(t)
        if v: msg += f"- {n}: {'원' if is_kor else '$'}{v:,.2f} ({c:+.2f}%)\n"
    
    # 지수
    msg += "\n📊 [주요 지수]\n"
    for n, t in INDEXES.items():
        v, c = get_data(t)
        if v: msg += f"- {n}: {v:,.0f} ({c:+.2f}%)\n"
        
    msg += "\n📰 [주요 시장 이슈]\n" + get_market_news()
    return msg

async def main():
    if not TOKEN or not CHAT_ID: return
    bot = telegram.Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=get_market_data())

if __name__ == "__main__":
    asyncio.run(main())
