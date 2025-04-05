import json, os
import gradio as gr
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request,  Header, BackgroundTasks, HTTPException, status
import google.generativeai as genai

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, AudioMessage

# 設定 Google AI API 金鑰
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# 設定生成文字的參數
generation_config = genai.types.GenerationConfig(max_output_tokens=2048, temperature=0.5, top_p=0.5, top_k=16)

# 使用 Gemini-1.5-flash 模型
model = genai.GenerativeModel('gemini-2.0-flash-exp', system_instruction="你是胡說八道的萬應機器人。") # 或是使用 "你是博通古今的萬應機器人！"

# 設定 Line Bot 的 API 金鑰和秘密金鑰
line_bot_api = LineBotApi(os.environ["CHANNEL_ACCESS_TOKEN"])
line_handler = WebhookHandler(os.environ["CHANNEL_SECRET"])

# 設定是否正在與使用者交談
working_status = os.getenv("DEFALUT_TALKING", default = "true").lower() == "true"

# 建立 FastAPI 應用程式
app = FastAPI()

# 設定 CORS，允許跨域請求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 處理根路徑請求
@app.get("/")
def root():
    return {"title": "Line Bot"}

# 處理 Line Webhook 請求
@app.post("/webhook")
async def webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_line_signature=Header(None),
):
    # 取得請求內容
    body = await request.body()
    try:
        # 將處理 Line 事件的任務加入背景工作
        background_tasks.add_task(
            line_handler.handle, body.decode("utf-8"), x_line_signature
        )
    except InvalidSignatureError:
        # 處理無效的簽章錯誤
        raise HTTPException(status_code=400, detail="Invalid signature")
    return "ok"

# 處理文字訊息事件
@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global working_status
    
    # 檢查事件類型和訊息類型
    if event.type != "message" or event.message.type != "text":
        # 回覆錯誤訊息
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="Event type error:[No message or the message does not contain text]")
        )
        
    # 檢查使用者是否輸入 "再見"
    elif event.message.text == "再見":
        # 回覆 "Bye!"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="Bye!")
        )
        return
       
    # 檢查是否正在與使用者交談
    elif working_status:
        try: 
            # 取得使用者輸入的文字
            prompt = event.message.text
            # 使用 Gemini 模型生成文字
            completion = model.generate_content(prompt, generation_config=generation_config)
            # 檢查生成結果是否為空
            if (completion.parts[0].text != None):
                # 取得生成結果
                out = completion.parts[0].text
            else:
                # 回覆 "Gemini沒答案!請換個說法！"
                out = "Gemini沒答案!請換個說法！"
        except:
            # 處理錯誤
            out = "Gemini執行出錯!請換個說法！" 
  
        # 回覆生成結果
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=out))

if __name__ == "__main__":
    # 啟動 FastAPI 應用程式
    uvicorn.run("main:app", host="0.0.0.0", port=7860, reload=True)

# 註解說明：
# import 導入必要的套件
# genai.configure 設定 Google AI API 金鑰
# generation_config 設定文字生成參數
# model 設定使用的 Gemini 模型
# line_bot_api 和 line_handler 設定 Line Bot API 和 webhook 處理器
# working_status 設定是否正在與使用者交談
# app 建立 FastAPI 應用程式
# app.add_middleware 設定 CORS
# @app.get("/") 處理根路徑請求
# @app.post("/webhook") 處理 Line Webhook 請求
# @line_handler.add(MessageEvent, message=TextMessage) 處理文字訊息事件
# if __name__ == "__main__": 啟動 FastAPI 應用程式
# 程式碼功能說明：
# 程式碼首先會導入必要的套件，並設定 Google AI API 金鑰、文字生成參數、Gemini 模型以及 Line Bot API。
# 接著會建立 FastAPI 應用程式，並設定 CORS。
# 程式碼會定義兩個函數：
# root() 處理根路徑請求，返回一個簡單的 JSON 訊息。
# webhook() 處理 Line Webhook 請求，將處理 Line 事件的任務加入背景工作，並處理無效的簽章錯誤。
# 程式碼還定義一個函數 handle_message() 來處理文字訊息事件，它會檢查事件類型和訊息類型，並根據使用者輸入執行不同的動作：
# 如果使用者輸入 "再見"，回覆 "Bye!"。
# 如果正在與使用者交談，則會使用 Gemini 模型生成文字，並將結果回覆給使用者。
# 最後，程式碼會啟動 FastAPI 應用程式，開始監聽 HTTP 請求。
# 程式碼運行方式：
# 將程式碼存為 main.py 文件。
# 在環境變數中設定 GOOGLE_API_KEY、CHANNEL_ACCESS_TOKEN 和 CHANNEL_SECRET。
# 執行 uvicorn main:app --host 0.0.0.0 --port 7860 --reload 命令啟動 FastAPI 應用程式。
# 使用 Line 帳戶與 Line Bot 進行對話。
# 注意：
# 程式碼中使用 os.environ["GOOGLE_API_KEY"]、os.environ["CHANNEL_ACCESS_TOKEN"] 和 os.environ["CHANNEL_SECRET"] 來存取環境變數，需要先在環境變數中設定這些值。
# 程式碼中使用 uvicorn 執行 FastAPI 應用程式，需要先安裝 uvicorn 套件。
# 程式碼中使用 google.generativeai 套件，需要先安裝 google-generativeai 套件。
# 程式碼中使用 linebot 套件，需要先安裝 linebot 套件。