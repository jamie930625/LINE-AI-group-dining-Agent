# 🤖 LINE 揪團神隊友 (LINE AI Group-Dining Agent)

> 一個專為 LINE 群組打造的「全自動化聚餐助理」。
> 透過 LLM 結合 **RAG（記憶檢索）**、**Tool Use（工具調用）**、**Cronjob（排程喚醒）** 與 **Human-in-the-loop（人類介入）** 機制，完美解決群組聚餐從「提議」、「投票」到「自動打 API 訂位」的繁瑣行政流程。

---

## ✨ 核心解決痛點

* **消滅決策摩擦力：** 解決群組討論總是發散、無人統整的困境。
* **零切換成本 (Zero-Context-Switching)：** 讓使用者直接在 LINE 聊天室內完成找餐廳、投票、訂位，無需跳轉外部 App。
* **群組專屬記憶：** 系統具備長期記憶，能記住群組成員的飲食禁忌（如：不吃牛、海鮮過敏）與偏好時段。

## 📂 專案結構與核心模組

本專案實作了 Agent 的核心「手腳（Tools）」與「大腦（LLM）」的互動介面。主要模組如下：

* 🧠 **`memory_search.py`**
  * **混合檢索 (Hybrid Search)：** 結合 BM25（字面比對）與 Embedding（語意比對），精準從 `MEMORY.md` 提取群組偏好與限制，作為後續決策的 Context。
* 🔍 **`search_restaurants.py`**
  * **Context Engineering：** 串接外部餐廳 API，並將繁雜的 JSON 轉換為乾淨的摘要，結合「記憶」主動剔除地雷選項。
* 📊 **`create_line_poll.py`**
  * **原生/模擬投票：** 透過 LINE API 發布群組投票，建立選項並設定截止時間。
* ⏰ **`schedule_wakeup.py`**
  * **Heartbeat & Sleep Mode：** 實作非同步排程機制。發起投票後 Agent 進入休眠不消耗 Token，時間一到由系統主動喚醒 Agent 結算票數（System-initiated Prompt）。
* 🎫 **`inline_booking_step1.py` & `inline_booking_step2.py`**
  * **自動化訂位與 HITL：** 處理訂位 API 的狀態機（State Machine）。實作「客滿時主動詢問備案」以及「請求發起人提供簡訊驗證碼」的雙向互動機制，確保高風險操作交還人類決策。

## 🔄 系統運作流程 (Workflow)

1. **意圖觸發：** 使用者在群組發送 `「幫我們訂下週五晚餐」`。
2. **記憶補全：** Agent 調用 `memory_search` 得知「下班時間為 18:00，有人不吃海鮮」。
3. **過濾推薦：** 調用 `search_restaurants` 取得清單，並依據記憶剔除不適合的選項。
4. **發起投票：** 調用 `create_line_poll`，設定截止時間後進入休眠。
5. **排程喚醒：** 截止時間到，`schedule_wakeup` 抓取最高票結果並喚醒 Agent。
6. **嘗試訂位：** 調用 `inline_booking_step1` 嘗試卡位。
7. **驗證與完成：** 系統觸發簡訊，Agent 向人類索取驗證碼。成功調用 `inline_booking_step2` 後，回傳行事曆連結至群組。

## 🛠️ 技術亮點 (Technical Highlights)

* **自主錯誤恢復 (Autonomous Fallback)：** 當 API 呼叫失敗（如餐廳客滿）時，系統不會 Crash，而是將 Error Message 當作 Context 傳回給 LLM，由 Agent 判斷下一步（如：改訂第二高票或詢問群組）。
* **狀態與對話解耦 (Decoupling)：** Python 程式只負責處理 API 邏輯與狀態碼，人類可讀的溫暖回覆皆由 LLM 根據「系統提示」動態生成，保持程式碼簡潔與彈性。

## 🚀 快速開始 (Getting Started)

### 1. 安裝依賴套件
```bash
git clone [https://github.com/jamie930625/LINE-AI-group-dining-Agent.git](https://github.com/jamie930625/LINE-AI-group-dining-Agent.git)
cd LINE-AI-group-dining-Agent
pip install -r requirements.txt
