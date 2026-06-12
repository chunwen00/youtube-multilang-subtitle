"""OpenAI GPT 多語言翻譯成繁體中文模組。"""  # 模組說明



from __future__ import annotations  # 啟用延遲型別註解



import json  # 序列化與解析翻譯請求/回應



from openai import OpenAI  # OpenAI SDK



from services.languages import language_label  # 語言代碼轉中文名稱





def translate_segments(  # 批次翻譯語音片段並保留時間軸

    client: OpenAI,  # OpenAI 用戶端

    segments: list[dict],  # 含 start/end/text 的原文片段

    model: str = "gpt-4o-mini",  # 預設翻譯模型

    source_language: str | None = None,  # 來源語言代碼，None 表示自動判斷

    batch_size: int = 20,  # 每批送出的片段數量

) -> list[dict]:  # 回傳含原文與中文對照的片段清單

    """Translate segment text from any language to Traditional Chinese."""  # 函式文件字串

    translated: list[dict] = []  # 累積翻譯結果



    if source_language:  # 已知來源語言

        src_hint = language_label(source_language)  # 轉為中文語言名稱

        system_prompt = (  # 指定語言的翻譯提示

            f"你是專業翻譯。將輸入的{src_hint}逐句翻譯成繁體中文，"

            "保持語意自然、口語化，適合影片字幕。只回傳 JSON："

            '{"translations":[{"id":0,"text":"中文"}]}'

        )

    else:  # 自動判斷來源語言

        system_prompt = (  # 多語言自動翻譯提示

            "你是專業多語言翻譯。輸入可能是英語、法語、俄語、日語等任意語言，"

            "請逐句翻譯成繁體中文，保持語意自然、口語化，適合影片字幕。只回傳 JSON："

            '{"translations":[{"id":0,"text":"中文"}]}'

        )



    for i in range(0, len(segments), batch_size):  # 分批處理，避免單次請求過大

        batch = segments[i : i + batch_size]  # 取出目前批次的片段

        payload = [{"id": idx, "text": seg["text"]} for idx, seg in enumerate(batch)]  # 組成 API 輸入



        response = client.chat.completions.create(  # 呼叫 Chat Completions API

            model=model,  # 翻譯模型

            temperature=0.2,  # 低溫度，翻譯較穩定一致

            response_format={"type": "json_object"},  # 要求回傳 JSON 物件

            messages=[  # 對話訊息清單

                {"role": "system", "content": system_prompt},  # 系統提示

                {

                    "role": "user",  # 使用者訊息：待翻譯的原文片段

                    "content": json.dumps(payload, ensure_ascii=False),  # JSON 字串

                },

            ],

        )



        content = response.choices[0].message.content or "{}"  # 取得模型回覆文字

        data = json.loads(content)  # 解析 JSON 回應

        mapping = {item["id"]: item["text"] for item in data.get("translations", [])}  # id 對應中文



        for idx, seg in enumerate(batch):  # 將翻譯結果合併回原始時間軸

            translated.append(  # 加入一筆翻譯後片段

                {

                    "start": seg["start"],  # 保留開始時間

                    "end": seg["end"],  # 保留結束時間

                    "text_src": seg["text"],  # 原文（任意語言）

                    "text_zh": mapping.get(idx, seg["text"]),  # 中文譯文，缺則退回原文

                }

            )



    return translated  # 回傳完整翻譯片段清單


