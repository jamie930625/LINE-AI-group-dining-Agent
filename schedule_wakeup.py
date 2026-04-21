# // 模組 A：LLM 使用的工具 (設定鬧鐘)
# 定義函數 schedule_wakeup(喚醒時間 time, 任務名稱 task):
#     1. 驗證時間格式是否正確
#     2. 將 (time, task, 目前的對話 Session_ID) 寫入系統的排程資料庫 (如 Redis 或 Cron)
#     3. 系統紀錄目前的 Agent 狀態為「休眠中」
#     4. 回傳字串給 LLM："排程已設定，請結束當前對話並進入休眠。"

# // 模組 B：系統底層的背景工作 (龍蝦大管家的鬧鐘響了)
# 定義背景任務 check_poll_results_worker():
#     1. 時間到達 4/27 12:00，系統觸發此任務
#     2. 呼叫 LINE API 取得特定群組的投票結果
#     3. 解析結果，找出最高票的餐廳（例如：築間）
#     4. 組裝主動喚醒的 System Prompt："投票已截止，最高票為築間，請執行下一步訂位。"
#     5. 載入原本休眠的 Agent Session，把這段 Prompt 塞進去
#     6. 重新呼叫 LLM API，讓它接續工作


from datetime import datetime
# 假設我們用一個輕量級的排程套件或自己包裝的 Task Queue
from app.core.task_queue import scheduler
from app.llm_engine import agent_invoke

# ==========================================
# 模組 A: 提供給 LLM 呼叫的 Tool
# ==========================================
def schedule_wakeup(wakeup_time_str, task_name, session_id="session_123"):
    """
    [tool_use] 讓 Agent 可以設定未來的喚醒時間與任務
    """
    # 將字串轉換為 datetime 物件
    wakeup_time = datetime.strptime(wakeup_time_str, "%Y-%m-%d %H:%M")
    
    # 把任務註冊進系統排程器 (非同步)
    scheduler.add_job(
        func=background_wakeup_worker, # 時間到要執行的 function
        trigger='date', 
        run_date=wakeup_time,
        args=[task_name, session_id]
    )
    
    # 告訴 LLM 已經設定好了，它可以停止輸出了
    return "系統提示：鬧鐘設定成功，Agent 進入休眠狀態 (Sleep Mode)。"


# ==========================================
# 模組 B: 時間到了，系統在背景自動執行的 Worker
# ==========================================
def background_wakeup_worker(task_name, session_id):
    """
    時間一到，系統會觸發這個 Worker (龍蝦大管家)
    """
    if task_name == "check_poll_results":
        # 1. 執行實體任務：去抓 LINE 的投票結果
        # mock_get_poll_winner 是一個假設的內部函數
        winner_restaurant = mock_get_poll_winner(group_id="Cxxxx_mock") 
        
        # 2. 準備喚醒 LLM 的 Context
        system_prompt = (
            f"【系統自動喚醒 (HEARTBEAT)】\n"
            f"你設定的排程任務 '{task_name}' 時間已到。\n"
            f"目前的投票結果已結算，最高票為：{winner_restaurant}。\n"
            f"請接續處理，執行下一步的訂位任務。"
        )
        
        # 3. 帶著之前的 Session 記憶，主動去「戳」LLM 讓它繼續工作
        print(f"[{datetime.now()}] 觸發喚醒機制，重新啟動 Agent...")
        agent_invoke(session_id=session_id, user_message=system_prompt)
