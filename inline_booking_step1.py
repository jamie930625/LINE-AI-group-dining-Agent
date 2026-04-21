# 定義函數 inline_booking_step1(餐廳名稱 restaurant, 日期時間 date, 人數 pax):
#     1. 準備呼叫 Inline 訂位系統 API
#     2. 將參數 (restaurant, date, pax) 打包傳送
    
#     3. 取得 API 回傳狀態：
#         情境 A：狀態為「客滿 (Fully Booked)」
#             - 不直接拋出系統錯誤當機
#             - 回傳 系統提示 給 LLM："預訂失敗，該時段已客滿。請詢問群組是否更換第二高票餐廳或更改時間。"
            
#         情境 B：狀態為「保留中，需驗證 (Pending SMS)」
#             - API 已經自動觸發簡訊給註冊會員（發起人）
#             - 回傳 系統提示 給 LLM："座位已成功預留。系統已發送 SMS 驗證碼。請在群組標記發起人，請他提供 6 位數驗證碼。"
            
#     4. (LLM 收到上述回傳後，會根據 System Prompt 生成對應的 LINE 訊息，達到 HITL 的效果)


import requests

def inline_booking_step1(restaurant, date, pax, user_phone="0912345678"):
    """
    [tool_use] 向訂位系統發起初步預訂，並處理客滿或簡訊驗證狀態
    """
    # 假設這是 Inline 的訂位 API endpoint
    api_url = "https://api.mock-inline.com/v1/booking/request"
    payload = {
        "restaurant_name": restaurant,
        "datetime": date,
        "pax": pax,
        "phone": user_phone
    }
    
    try:
        # 發送預訂請求
        response = requests.post(api_url, json=payload, timeout=10)
        result = response.json()
        
        # ==========================================
        # Edge Case 1: 餐廳客滿 (觸發備案 HITL)
        # ==========================================
        if result.get("status") == "FULL":
            # 將狀態與「行動建議」一起回傳給 LLM
            # LLM 看到這段，就會自己生成：「大家抱歉，築間客滿了...」
            return (
                "系統提示：該時段已客滿，訂位失敗。"
                "請中止訂位流程，並在 LINE 群組發言詢問大家："
                "是否要改訂第二高票的餐廳，或是更改時間？"
            )
            
        # ==========================================
        # 正常流程: 座位預留，需簡訊驗證 (觸發驗證 HITL)
        # ==========================================
        elif result.get("status") == "PENDING_VERIFICATION":
            # 告訴 LLM 卡位成功，請 LLM 負責去跟人類討驗證碼
            # LLM 會根據這段生成：「已幫大家預留！@發起人 請提供簡訊驗證碼...」
            return (
                "系統提示：座位預留成功！但尚未確認。"
                f"訂位系統已發送簡訊驗證碼至手機 {user_phone}。"
                "請在 LINE 群組標記發起人，向他索取 6 位數的驗證碼以進行 step2。"
            )
            
        else:
            return "系統提示：未知的 API 狀態，請回報系統錯誤。"

    except Exception as e:
        return f"系統提示：連線訂位系統失敗。錯誤訊息：{str(e)}"
