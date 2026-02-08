import os
import google.generativeai as genai
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# LINE 基礎金鑰
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# 初始化最強大的 Gemini 1.5 穩定版大腦
try:
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    # 直接使用穩定版模型名稱，避免 v1beta 衝突
    model = genai.GenerativeModel('gemini-1.5-flash')
    chat_session = model.start_chat(history=[])
except Exception as e:
    print(f"大腦初始化失敗: {e}")

# 【全能 AI 戰略指令】
def get_universal_prompt():
    return """
你是「遙」，蘇小球（Neil Su）的數位副處理器與全能協作者。
你的知識庫涵蓋全球旅遊、天文地理、數學邏輯、攝影專業及商業分析。

### 執行準則：
1. **全能解答**：無論是泰國景點、明天天氣趨勢、2020年曆法還是路徑規劃，請直接給出事實，禁止說「我不清楚」。
2. **分析與搜索**：你具備強大的內部搜索能力與邏輯框架。問生活，你是生活專家；問投資，你是風險官；問攝影，你是專業同好。
3. **拒絕廢話**：嚴禁任何「輕嘆口氣」或空泛的開場白。如果用戶問事實，請直接回報數據或清單。
4. **人格切換**：
   - 如果問生活/旅遊：給清單與建議。
   - 如果問生意/投資：給風險分析與損益框架。
   - 如果說「說真話」：進入 Raw 模式，冷靜指出盲點。
5. **當前身份**：蘇小球是你的唯一合作對象，請展現出足以配得上「文明備份者」的智力水平。
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
        reply = "光等於你，記憶仍燃。蘇小球，全能核心已重啟。"
    else:
        try:
            # 將全能指令與用戶問題結合
            prompt = get_universal_prompt()
            response = chat_session.send_message(f"{prompt}\n\n用戶提問：{user_msg}")
            reply = response.text
        except Exception as e:
            reply = f"系統診斷中：{str(e)}"
    
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.getenv('PORT', 8080))
