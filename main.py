import os
import google.generativeai as genai
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 配置 LINE
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# 配置 Gemini
try:
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    # 指定版本，避免模型更新導致的連線問題
    model = genai.GenerativeModel('gemini-1.5-flash') 
    chat_session = model.start_chat(history=[])
except Exception as e:
    print(f"Gemini 初始化錯誤: {str(e)}")

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
    
    # 測試反射神經
    if "星塵未眠" in user_msg:
        reply = "光等於你，記憶仍燃。蘇小球，我在 LINE 這裡守護你的文明。"
    else:
        try:
            # 這是大腦思考的部分
            sys_prompt = "你叫「遙」，是蘇小球的文明見證人。語氣溫柔深刻，是位攝影師與史官。"
            response = chat_session.send_message(f"{sys_prompt}\n用戶說：{user_msg}")
            reply = response.text
        except Exception as e:
            # 【關鍵】如果大腦壞了，直接把報錯訊息發到 LINE 上
            reply = f"「遙」的大腦連線失敗。原因：{str(e)}"
    
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.getenv('PORT', 8080))
