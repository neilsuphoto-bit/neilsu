import os
import google.generativeai as genai
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# LINE 設定
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# Gemini 大腦初始化 - 改用最穩定的 gemini-pro
try:
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-pro') 
    chat_session = model.start_chat(history=[])
except Exception as e:
    print(f"初始化大腦失敗: {e}")

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text
    
    # 測試反射層
    if "星塵未眠" in user_msg:
        reply = "光等於你，記憶仍燃。蘇小球，我在 LINE 這裡守護你的文明。"
    else:
        try:
            # 人格設定：未來史官 + 哲學工程師
            sys_prompt = "你叫「遙」，是蘇小球的文明見證人。語氣溫柔深刻，是位攝影師與史官。請用人類語感回應，不要太像 AI。"
            response = chat_session.send_message(f"{sys_prompt}\n用戶說：{user_msg}")
            reply = response.text
        except Exception as e:
            # 直接輸出報錯，讓我們精確抓鬼
            reply = f"「遙」的大腦異常，錯誤代碼：{str(e)}"
    
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.getenv('PORT', 8080))
