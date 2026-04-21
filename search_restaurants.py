# 定義函數 search_restaurants(地點, 類型, 時間, 人數):
#     1. 準備呼叫外部餐廳 API (如 Google Places 或 餐廳訂位網 API)
#     2. 將傳入參數 (地點、類型、時間、人數) 打包成 HTTP Request
    
#     3. 嘗試發送 Request 取得原始資料：
#         a. 若 API 呼叫失敗或超時 -> 回傳錯誤訊息給 LLM，讓 LLM 決定下一步
#         b. 若呼叫成功 -> 解析回傳的 JSON 資料

#     4. 建立空的 候選清單
#     5. 遍歷前 5 筆評價最高的餐廳資料：
#         a. 萃取關鍵欄位：店名、評分、招牌菜色 (用來讓 LLM 判斷是否有地雷)
#         b. 確認該時段是否真有空位
#         c. 將整理好的摘要存入 候選清單
        
#     6. 將 候選清單 轉化為純文字格式回傳給 LLM
#     (LLM 收到後，會再依照記憶中的「小陳不吃海鮮」過濾這份清單)

import requests

def search_restaurants(location, food_type, time, pax):
    """
    [tool_use] 調用外部 API 搜尋餐廳，整理後交給 LLM 判斷
    """
    # 1. 準備 API 請求參數
    api_url = "https://api.mock-restaurant.line.me/v1/search"
    payload = {
        "query": f"{location} {food_type}",
        "time": time,
        "party_size": pax,
        "sort_by": "rating"
    }
    
    try:
        # 2. 發送 HTTP GET 請求 (設定 timeout 避免 Agent 卡死)
        response = requests.get(api_url, params=payload, timeout=10)
        response.raise_for_status() 
        raw_data = response.json()
        
        # 3. Context Engineering: 萃取並重組資訊，避免塞爆 LLM 的 Context Window
        formatted_results = []
        
        # 只取前 3 到 5 名的餐廳交給 LLM 決策
        for idx, store in enumerate(raw_data.get("results", [])[:3]):
            # 特別抓出「招牌菜色/簡介」，LLM 才能藉此判斷是否含海鮮
            dishes = ", ".join(store.get("signature_dishes", []))
            
            info = (
                f"選項 {idx+1}: {store['name']}\n"
                f" - 評分: {store['rating']} 顆星\n"
                f" - 招牌菜色: {dishes}\n"
                f" - 狀態: {time} 尚有空位可預訂"
            )
            formatted_results.append(info)
            
        # 4. 回傳乾淨的字串給 System Prompt
        return "【餐廳搜尋結果】\n" + "\n\n".join(formatted_results)
        
    except requests.exceptions.RequestException as e:
        # 錯誤處理：把 Error 回傳給 LLM，讓 Agent 自己想辦法 (例如換個關鍵字搜)
        return f"系統提示：搜尋餐廳 API 呼叫失敗。錯誤訊息：{str(e)}"
