# 定義函數 memory_search(關鍵字陣列 queries):
#     1. 從檔案庫 (MEMORY.md) 載入所有長期記憶
#     2. 將記憶內容切分成獨立的段落 (Chunks)
#     3. 將傳入的 queries 結合成單一搜尋字串
    
#     4. 建立空的 結果清單
#     5. 針對每一個 Chunk 進行評分：
#         a. 字面比對分數 (s1) = 計算 Chunk 與搜尋字串的關鍵字重疊度 (如 BM25 演算法)
#         b. 語意比對分數 (s2) = 取得 Chunk 與搜尋字串的 Embedding 向量，計算餘弦相似度
#         c. 最終分數 (s) = (權重A * s1) + (權重B * s2)
#         d. 將 (Chunk, 最終分數) 存入 結果清單

#     6. 依據最終分數，將 結果清單 由高到低排序
#     7. 擷取分數最高的前 K 個 Chunks
#     8. 將這些 Chunks 打包成字串，回傳給 Agent (LLM) 作為 Context

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
# 假設專案內已有自建的工具庫，處理 Embedding 與 BM25
from app.utils.text_tools import get_embedding, calculate_bm25_score

def memory_search(*queries, top_k=3):
    """
    從記憶庫中檢索與 queries 相關的 Context
    範例調用: memory_search("公司位置", "下班時間", "飲食禁忌")
    """
    # 1. 讀取並切割記憶檔案
    with open("memory/MEMORY.md", "r", encoding="utf-8") as f:
        memory_text = f.read()
    
    # 簡單以雙換行作為 Chunk 切割依據
    chunks = [c.strip() for c in memory_text.split("\n\n") if c.strip()]
    
    query_text = " ".join(queries)
    query_emb = get_embedding(query_text) # 將搜尋字串轉為向量
    
    scored_chunks = []
    
    for chunk in chunks:
        # 2. 計算字面比對分數 s1 (Sparse Retrieval)
        s1 = calculate_bm25_score(query_text, chunk)
        
        # 3. 計算語意比對分數 s2 (Dense Retrieval)
        chunk_emb = get_embedding(chunk)
        s2 = cosine_similarity([query_emb], [chunk_emb])[0][0]
        
        # 4. 混合評分邏輯 (如系統架構圖: s = a*s1 + b*s2)
        alpha, beta = 0.3, 0.7  # 語意比重放高一點，因為有時關鍵字不完全吻合
        final_score = (alpha * s1) + (beta * s2)
        
        scored_chunks.append((final_score, chunk))
    
    # 5. 排序並取出 Top-K
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    best_memories = [item[1] for item in scored_chunks[:top_k]]
    
    # 6. 組裝成 System Prompt 看得懂的格式回傳
    result_context = "【檢索到的相關記憶】\n"
    for i, memory in enumerate(best_memories):
        result_context += f"{i+1}. {memory}\n"
        
    return result_context
