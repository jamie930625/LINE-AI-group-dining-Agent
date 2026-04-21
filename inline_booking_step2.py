# 定義函數 inline_booking_step2(驗證碼 code, 訂位任務 ID booking_id):
#     1. 準備呼叫 Inline 訂位系統的「驗證與確認」API
#     2. 將 (code, booking_id) 打包傳送
    
#     3. 取得 API 回傳狀態：
#         情境 A：狀態為「驗證成功 (CONFIRMED)」
#             - 從 API 回傳資料中萃取：訂位代號、行事曆加入連結
#             - 回傳 系統提示 給 LLM："驗證成功！請向群組發佈訂位成功的慶祝訊息，並附上行事曆連結。"
            
#         情境 B：狀態為「驗證碼錯誤 (INVALID_CODE)」
#             - 不輕易放棄，觸發 Retry 機制
#             - 回傳 系統提示 給 LLM："驗證碼錯誤。請在群組回覆發起人，請他檢查簡訊並重新提供正確的驗證碼。"
            
#     4. (LLM 收到上述回傳後，會生成最終的慶祝訊息，或是請使用者重試的訊息)



import requests

# 假設 booking_id 是 Agent 記錄在短期記憶或 Session 裡的變數
def inline_booking_step2(code, booking_id="temp_booking_9527"):
    """
    [tool_use] 提交簡訊驗證碼，完成最終訂位確認
    """
    # 呼叫訂位系統的驗證端點
    api_url = f"https://api.mock-inline.com/v1/booking/{booking_id}/verify"
    payload = {"verification_code": code}
    
    try:
        response = requests.post(api_url, json=payload, timeout=10)
        result = response.json()
        
        # ==========================================
        # 成功流程: 驗證通過，訂位完成
        # ==========================================
        if result.get("status") == "CONFIRMED":
            # 實務上 API 通常會回傳供使用者存取的資訊
            booking_ref = result.get("booking_ref", "B-778899")
            cal_link = result.get("calendar_link", "https://cal.mock/add/9527")
            
            # 將系統提示與動態資料打包，交給 LLM 去「潤飾」
            return (
                f"系統提示：訂位驗證成功！\n"
                f"請向 LINE 群組發佈成功的慶祝訊息，並務必附上以下資訊：\n"
                f"- 訂位代號: {booking_ref}\n"
                f"- 行事曆連結: {cal_link}\n"
                f"指引：請使用熱情、開心的語氣，並加上 🎉 等表情符號。"
            )
            
        # ==========================================
        # Edge Case 2: 驗證碼打錯 (再次觸發 HITL)
        # ==========================================
        elif result.get("status") == "INVALID_CODE":
            # LLM 看到這個，就會在群組說：「哎呀，驗證碼好像不對喔！請再確認一下簡訊～」
            return "系統提示：驗證碼錯誤。請在群組提醒發起人重新確認簡訊，並再次提供正確的 6 位數驗證碼。"
            
        else:
            return "系統提示：驗證失敗，發生未知狀態錯誤。"

    except requests.exceptions.RequestException as e:
        return f"系統提示：驗證 API 連線異常。請告知群組稍後重試。錯誤：{str(e)}"
