import warnings, os, yfinance as yf
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
        # period="1d"로 변경하여 당일 데이터 위주로 수집
        ticker_obj = yf.Ticker(ticker)
        s = ticker_obj.history(period="1d") 
        if s.empty: return None, 0
        curr = s['Close'].iloc[-1]
        prev = ticker_obj.history(period="5d")['Close'].iloc[-2] # 전일 종가 비교
        return curr, ((curr - prev) / prev) * 100
    except: return None, 0

def get_market_news():
    try:
        # 뉴스 데이터를 가져올 때 시간을 조금 더 여유롭게 줌
        news = yf.Ticker("QQQM").news
        if not news: return "현재 불러올 뉴스가 없습니다."
        return "\n".join([f"• {n['title']}" for n in news[:3]])
    except: return "뉴스 수집 실패"

def get_market_data():
    now = datetime.now() + timedelta(hours=9)
    hour = now.hour
    is_kor = 9 <= hour < 16
    
    msg = f"📈 [주식 비서 리포트] ({now.strftime('%H:%M')} KST)\n\n"
    
    # 지표 및 지수
    msg += "🌍 [매크로 및 주요 지수]\n"
    for n, t in {**MACRO, **INDEXES}.items():
        v, _ = get_data(t)
        if v: msg += f"- {n}: {v:,.2f}\n"

    # 보유 종목
    target = MY_KOR if is_kor else MY_USA
    msg += f"\n{'🇰🇷 [한국장]' if is_kor else '🇺🇸 [미국장]'} 보유종목\n"
    for n, t in target.items():
        v, c = get_data(t)
        if v: msg += f"- {n}: {'원' if is_kor else '$'}{v:,.2f} ({c:+.2f}%)\n"
        
    msg += "\n📰 [시장 이슈]\n" + get_market_news()
    return msg

async def main():
    if not TOKEN or not CHAT_ID: return
    bot = telegram.Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=get_market_data())

if __name__ == "__main__":
    asyncio.run(main())
