"""OpenAI Whisper 語音辨識模組。"""  # 模組說明



from __future__ import annotations  # 啟用延遲型別註解



from pathlib import Path  # 音訊檔案路徑型別



from openai import OpenAI  # OpenAI SDK





def transcribe_audio(  # 語音轉文字，支援多語言

    client: OpenAI,  # OpenAI 用戶端

    audio_path: Path,  # 音訊檔案路徑

    model: str = "whisper-1",  # Whisper 模型

    language: str | None = None,  # 來源語言代碼；None 則自動偵測

) -> tuple[list[dict], str | None]:  # 回傳片段清單與偵測到的語言代碼

    """Transcribe audio and return segments with timestamps and detected language."""  # 函式文件字串

    with audio_path.open("rb") as audio_file:  # 以二進位模式開啟音訊檔

        kwargs: dict = {  # API 參數

            "model": model,  # Whisper 模型名稱

            "file": audio_file,  # 上傳的音訊檔案

            "response_format": "verbose_json",  # 回傳含時間軸的詳細 JSON

            "timestamp_granularities": ["segment"],  # 要求片段級時間戳

        }

        if language:  # 使用者指定來源語言時

            kwargs["language"] = language  # 提示 Whisper 使用該語言辨識



        response = client.audio.transcriptions.create(**kwargs)  # 呼叫 Whisper 轉錄 API



    detected_language = getattr(response, "language", None) or language  # 取得偵測或指定的語言



    segments = []  # 存放整理後的語音片段

    for seg in response.segments or []:  # 遍歷 API 回傳的每個片段

        text = (seg.text or "").strip()  # 取得並去除空白

        if text:  # 有文字內容才加入

            segments.append(  # 加入標準化片段字典

                {

                    "start": float(seg.start),  # 片段開始時間（秒）

                    "end": float(seg.end),  # 片段結束時間（秒）

                    "text": text,  # 原文（任意語言）

                }

            )



    if not segments and response.text:  # 無片段但有整段文字時（後備方案）

        segments.append({"start": 0.0, "end": 0.0, "text": response.text.strip()})  # 整段作為一條



    return segments, detected_language  # 回傳語音片段與語言代碼


