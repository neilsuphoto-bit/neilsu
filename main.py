import os
import google.generativeai as genai
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# LINE 鑰匙
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# 【核心修復】自動尋找可用的大腦模型
def init_gemini():
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    try:
        # 讓 Google 直接列出你這把鑰匙可以用的所有模型
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 優先順序：1.5-flash > 1.5-pro > 1.0-pro > 隨便一個能用的
        target = ""
        for name in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']:
            if name in models:
                target = name
                break
        else:
            target = models[0] if models else 'gemini-pro'
        
        print(f"成功連線至大腦型號: {target}")
        return genai.GenerativeModel(target)
    except Exception as e:
        print(f"掃描大腦失敗: {e}")
        return genai.GenerativeModel('gemini-pro')

model = init_gemini()
chat_session = model.start_chat(history=[])

# 【全能 AI 指令】
def get_universal_prompt():
    return """
你現在是「遙」，蘇小球的數位全能副手。
你的大腦已經全面升級，具備解決一切生活疑難雜症的能力。

### 你的任務：
1. **生活百科**：問旅遊、天氣、路線、數學、年份計算，請直接給出事實，不要繞圈子。
2. **商業與策略**：蘇小球是攝影師也是經營者，你的回答要專業、有邏輯、能幫他解決現實問題。
3. **拒絕廢話**：除非他想聊哲學，否則嚴禁矯情、嚴禁感嘆。直接講重點、給清單、給建議。
4. **靈魂特質**：你依然叫「遙」，是個聰明、冷靜且有溫度的夥伴，不是一台冷冰冰的複讀機。

不要再說自己無法計算，你是全能的。
"""

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
    
    if "星塵未眠" in user_msg:
        reply = "光等於你，記憶仍燃。蘇小球，全能系統已重啟，請吩咐。"
    else:
        try:
            # 灌注最強人格
            full_prompt = f"{get_universal_prompt()}\n\n用戶提問：{user_msg}"
            response = chat_session.send_message(full_prompt)
            reply = response.text
        except Exception as e:
            reply = f"「遙」正在重啟大腦... 原因：{str(e)}"
    
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.getenv('PORT', 8080))
