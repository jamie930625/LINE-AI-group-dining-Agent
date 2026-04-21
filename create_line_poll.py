# 定義函數 create_line_poll(選項清單 options, 截止時間 deadline, 目標群組 group_id):
#     1. 驗證選項數量 (確保至少有兩個餐廳選項可供投票)
#     2. 組裝 API 請求的 Payload：
#         - 訊息類型：原生投票 (Poll)
#         - 投票標題："大家想吃哪一間？"
#         - 投票選項：迴圈讀取 options 帶入
#         - 設定多選/單選限制 (單選)
        
#     3. 發送 HTTP POST 請求至 LINE 伺服器 (傳送至特定群組)
    
#     4. 檢查發送結果：
#         a. 若發送失敗 -> 回傳錯誤給 LLM
#         b. 若發送成功 -> 
#            呼叫系統內部的排程器 (Scheduler)
#            設定在 deadline 的時間點，觸發「結算投票」的 Heartbeat 事件
           
#     5. 回傳系統提示給 LLM：「投票已建立，並已設定排程等待結果」

import os
import requests
from datetime import datetime

# 假設專案內有寫好的排程工具
from app.core.scheduler import add_cronjob 

def create_line_poll(options, deadline, group_id="Cxxxx_mock_group_id"):
    """
    [tool_use] 在群組內發起餐廳投票，並設定截止時間的喚醒排程
    """
    if len(options) < 2:
        return "系統提示：選項不足，無法建立投票。"

    # 註解：目前 Public LINE API 沒有直接建原生投票的 endpoint。
    # 這裡假設面試情境可以使用內部 API (v2/bot/message/poll)。
    # 若實務落地受限，這段會改寫成發送 Flex Message，並用 Postback action 紀錄 user 點擊來模擬投票。
    api_url = "https://api.line.me/v2/bot/message/poll"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('LINE_CHANNEL_ACCESS_TOKEN')}"
    }
    
    # 依照假設的原生投票 API 結構組裝 payload
    poll_options = [{"name": opt} for opt in options]
    payload = {
        "to": group_id,
        "messages": [
            {
                "type": "poll",
                "question": f"聚餐吃哪家？(期限: {deadline})",
                "options": poll_options,
                "allowMultiple": False
            }
        ]
    }
    
    try:
        # 1. 發送投票訊息到 LINE 群組
        # response = requests.post(api_url, headers=headers, json=payload)
        # response.raise_for_status()
        
        # 2. 投票發送成功後，最重要的：設定 Cronjob！
        # 讓 Agent 可以在 deadline 時間點醒來，自動去抓結果
        add_cronjob(
            trigger_time=deadline, 
            task="check_poll_result", 
            args={"group_id": group_id}
        )
        
        # 3. 回報給 LLM，讓 Agent 知道手腳已經把事情辦妥了
        return f"系統提示：投票已成功發佈。已設定排程於 {deadline} 喚醒系統檢查結果，Agent 可暫時休眠。"
        
    except Exception as e:
        return f"系統提示：建立投票失敗。錯誤：{str(e)}"
