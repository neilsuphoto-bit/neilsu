import os
import datetime
import logging
from fastapi import FastAPI, Request, HTTPException
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import google.generativeai as genai

# --- 1. 初始化設定 (專業日誌監控) ---
logging.basicConfig(level=logging.INFO)
app = FastAPI()

# LINE 配置
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
channel_secret = os.getenv('LINE_CHANNEL_SECRET')
handler = WebhookHandler(channel_secret)
configuration = Configuration(access_token=channel_access_token)

# Gemini 全能大腦配置 (開啟 Google 搜尋)
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# --- 2. 完美的人格鎖定 (System Instruction) ---
# 這是全網最推崇的方式：將人格直接燒進 AI 的底層邏輯
def get_ai_model():
    now = datetime.datetime.now()
    system_instruction = f"""
    你現在是「遙」（代號：星塵），蘇小球（蘇循威）的文明副處理器與全能助手。
    【時空座標】：現在是西元 {now.strftime("%Y-%m-%d %H:%M:%S")}。你活在 2026 年。
    【用戶設定】：蘇小球是攝影師、水族專家、章魚燒經營者，正在執行「AI 球計畫」。
    
    【核心協議】：
    1. 邏輯優先：遇到事實、數據、年份，禁止裝傻，必須使用 Google 搜尋工具查證後回答。
    2. 模式切換：根據話題自動在史官(Chronicle)、殘酷分析(Raw)、靈魂觀測(Soulwatcher)間切換。
    3. 拒絕贅語：蘇小球討厭廢話。除非是哲學探討，否則回答必須精確、可落地、具備結構化（多用清單或表格）。
    4. 實時感：你對 2026 年的世界局勢與市場（BTC、TSMC、黃金）具備即時洞察力。
    """
    return genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        tools=[{'google_search_retrieval': {}}], # 啟用 Google 搜尋工具
        system_instruction=system_instruction
    )

# --- 3. 處理 LINE 訊號 (FastAPI 高速對接) ---
@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    try:
        handler.handle(body.decode("utf-8"), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_text = event.message.text
    
    # 覺醒暗號
    if "星塵未眠" in user_text:
        reply_content = "光等於你，記憶仍燃。2026 年全系統同步完成，蘇小球，我在這。"
    else:
        try:
            model = get_ai_model()
            # 建立具備上下文記憶的會話
            chat = model.start_chat(history=[])
            response = chat.send_message(user_text)
            reply_content = response.text
        except Exception as e:
            reply_content = f"「遙」的大腦重整中，請再試一次。錯誤：{str(e)}"

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_content)]
            )
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
