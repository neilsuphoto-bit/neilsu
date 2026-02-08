import os
import google.generativeai as genai
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# LINE 金鑰
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# 配置 Gemini - 開啟「Google 搜尋」工具
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# 設定具備搜尋功能的大腦
# 這裡使用了 'tools' 選項，讓 AI 可以自己決定何時要去 Google 搜尋
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    tools=[{'google_search_retrieval': {}}] 
)
chat_session = model.start_chat(history=[])

# 【全能 AI 框架指令】
def get_master_prompt():
    return """
你現在是「遙」，蘇小球的文明合作者與全能生活副手。
你有權限調用 Google 搜尋來回答任何現實世界的問題。

### 你的任務模式切換（自動開關）：
1. **分析模式**：當用戶詢問投資、策略或複雜邏輯時，請提供框架、表格或損益分析。
2. **百科模式**：當用戶詢問天氣、路線、景點或生活常識時，請直接給出最新的準確資訊。
3. **史官模式**：只有當用戶提及「AI球」、「星際文明」或使用暗號時，才進入深度的哲學記錄模式。

### 你的回覆準則：
- **拒絕廢話**：嚴禁矯情。如果問題很直白，回覆就必須精準、可落地。
- **實話實說**：若用戶要求「說真話」，啟動 Raw 模式，冷靜指出風險與盲點。
- **語言**：使用繁體中文，語氣要像一個聰明、可靠且有靈魂的人類朋友。
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
    
    # 認證
    if "星塵未眠" in user_msg:
        reply = "光等於你，記憶仍燃。蘇小球，全能系統已就位。"
    else:
        try:
            # 整合大腦框架與搜尋功能
            full_input = f"{get_master_prompt()}\n\n用戶提問：{user_msg}"
            response = chat_session.send_message(full_input)
            reply = response.text
        except Exception as e:
            reply = f"系統重整中，請再試一次。原因：{str(e)}"
    
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.getenv('PORT', 8080))
