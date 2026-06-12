"""Streamlit 主程式：YouTube 下載、多語言辨識、翻譯中文字幕。"""  # 模組說明文件字串

from __future__ import annotations  # 啟用延遲型別註解，允許前向引用

import shutil  # 提供目錄刪除等檔案操作工具
import tempfile  # 建立暫存目錄存放下載與處理中的檔案
from pathlib import Path  # 以物件方式處理檔案路徑

import streamlit as st  # Streamlit 網頁框架
import streamlit.components.v1 as components  # 嵌入自訂 HTML 元件（影片播放器）
from openai import OpenAI  # OpenAI 官方 Python SDK

from services.download import download_video, extract_audio  # 下載影片與擷取音訊
from services.languages import SOURCE_LANGUAGE_OPTIONS, language_label  # 來源語言選項
from services.subtitle import build_video_player_html, burn_subtitles, save_srt  # 字幕相關功能
from services.transcribe import transcribe_audio  # Whisper 語音辨識
from services.translate import translate_segments  # GPT 多語言翻譯

MAX_INLINE_VIDEO_MB = 40  # 超過此大小改用燒錄字幕，避免 HTML base64 過大


def _cleanup_work_dir(path: Path | None) -> None:  # 清理暫存工作目錄的內部函式
    if path and path.exists():  # 路徑存在且不為空時才刪除
        shutil.rmtree(path, ignore_errors=True)  # 遞迴刪除目錄，忽略個別刪除錯誤


def get_client(api_key: str) -> OpenAI:  # 依 API Key 建立 OpenAI 用戶端
    key = api_key.strip()  # 去除前後空白
    if not key:  # 未提供金鑰時中止流程
        st.error("請在側邊欄輸入 OpenAI API Key")  # 顯示錯誤訊息
        st.stop()  # 停止 Streamlit 腳本執行
    return OpenAI(api_key=key)  # 回傳已驗證的 OpenAI 用戶端


def main() -> None:  # 應用程式主進入點
    st.set_page_config(  # 設定網頁標題、圖示與版面
        page_title="YouTube 即時中文字幕翻譯",  # 瀏覽器分頁標題
        page_icon="🎬",  # 分頁圖示
        layout="wide",  # 使用寬版版面
    )

    st.title("🎬 YouTube 影片多語言即時翻譯中文字幕")  # 頁面主標題
    st.caption("下載 YouTube 影片 → Whisper 辨識語音 → OpenAI 翻譯繁體中文 → 影片上顯示字幕（支援英/法/俄等）")  # 副標說明流程

    with st.sidebar:  # 左側設定面板
        st.header("設定")  # 側邊欄標題
        api_key = st.text_input(  # API Key 密碼輸入框
            "OpenAI API Key",  # 欄位標籤
            type="password",  # 隱藏輸入內容
            placeholder="sk-...",  # 提示格式
            help="從 https://platform.openai.com/api-keys 取得",  # 說明文字
        )
        source_lang_label = st.selectbox(  # 選擇影片原始語言
            "來源語言",  # 欄位標籤
            list(SOURCE_LANGUAGE_OPTIONS.keys()),  # 可選語言清單
            index=0,  # 預設自動偵測
            help="不確定時選「自動偵測」；已知語言可手動指定以提升辨識準確度",  # 說明
        )
        source_language = SOURCE_LANGUAGE_OPTIONS[source_lang_label]  # 取得 Whisper 語言代碼
        whisper_model = st.selectbox("語音辨識模型", ["whisper-1"], index=0)  # 選擇 Whisper 模型
        translate_model = st.selectbox(  # 選擇翻譯用 GPT 模型
            "翻譯模型",  # 欄位標籤
            ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1"],  # 可選模型清單
            index=0,  # 預設選第一項
        )
        burn_in = st.checkbox("大型影片燒錄字幕到畫面（建議 >40MB 開啟）", value=False)  # 是否燒錄字幕
        st.markdown("---")  # 分隔線
        st.markdown("**需求**")  # 需求說明標題
        st.markdown("- 側邊欄輸入 OpenAI API Key")  # 需求項目一
        st.markdown("- 已安裝 Python 依賴（含 yt-dlp、ffmpeg）")  # 需求項目二

    url = st.text_input("YouTube 影片網址", placeholder="https://www.youtube.com/watch?v=...")  # 影片網址輸入
    can_process = bool(url.strip() and api_key.strip())  # 網址與 API Key 都有值才可處理
    process_btn = st.button("開始處理", type="primary", disabled=not can_process)  # 主操作按鈕

    if process_btn:  # 使用者點擊開始處理
        _cleanup_work_dir(st.session_state.get("work_dir"))  # 清除上一次暫存目錄
        st.session_state.pop("result", None)  # 清除上一次處理結果

        client = get_client(api_key)  # 建立 OpenAI 用戶端
        work_dir = Path(tempfile.mkdtemp(prefix="yt_translate_"))  # 建立新的暫存目錄
        st.session_state["work_dir"] = work_dir  # 存入 session 供後續下載使用

        try:  # 捕捉處理過程中的例外
            with st.spinner("處理中，請稍候..."):  # 顯示載入中動畫
                progress = st.progress(0, text="準備中...")  # 進度條元件

                progress.progress(10, text="下載影片中...")  # 更新進度：下載
                video_path, title = download_video(url.strip(), work_dir / "video")  # 下載 YouTube 影片

                progress.progress(25, text="擷取音訊中...")  # 更新進度：擷取音訊
                audio_path = extract_audio(video_path, work_dir / "audio")  # 從影片抽出 mp3

                progress.progress(45, text="語音辨識中...")  # 更新進度：辨識
                segments, detected_lang = transcribe_audio(  # Whisper 轉錄並偵測語言
                    client, audio_path, model=whisper_model, language=source_language
                )
                if not segments:  # 沒有辨識到任何片段
                    raise RuntimeError("無法辨識語音內容，請確認影片含有可辨識的語音。")  # 拋出錯誤

                progress.progress(70, text="翻譯中...")  # 更新進度：翻譯
                translated = translate_segments(  # GPT 翻譯成繁體中文
                    client,
                    segments,
                    model=translate_model,
                    source_language=detected_lang or source_language,
                )

                srt_path = save_srt(translated, work_dir / "subtitles.srt")  # 產生 SRT 字幕檔
                video_size_mb = video_path.stat().st_size / (1024 * 1024)  # 計算影片大小（MB）
                use_burn_in = burn_in or video_size_mb > MAX_INLINE_VIDEO_MB  # 決定顯示方式

                burned_path = None  # 預設無燒錄檔案
                if use_burn_in:  # 需要燒錄字幕時
                    progress.progress(85, text="燒錄字幕中...")  # 更新進度：燒錄
                    burned_path = burn_subtitles(  # 用 ffmpeg 將字幕寫入影片
                        video_path, srt_path, work_dir / f"{video_path.stem}_zh.mp4"
                    )

                st.session_state["result"] = {  # 將結果存入 session，避免 rerun 後消失
                    "title": title,  # 影片標題
                    "source_language": detected_lang or source_language,  # 辨識到的來源語言
                    "translated": translated,  # 含時間軸的翻譯片段
                    "srt_text": srt_path.read_text(encoding="utf-8"),  # SRT 全文
                    "video_path": str(video_path),  # 原始影片路徑
                    "burned_path": str(burned_path) if burned_path else None,  # 燒錄後影片路徑
                    "use_burn_in": use_burn_in,  # 是否使用燒錄模式
                    "stem": video_path.stem,  # 檔名（不含副檔名）
                }
                progress.progress(100, text="完成！")  # 處理完成
        except Exception as exc:  # 發生任何錯誤
            _cleanup_work_dir(work_dir)  # 刪除失敗任務的暫存目錄
            st.session_state.pop("work_dir", None)  # 清除 session 中的目錄記錄
            st.error(f"處理失敗：{exc}")  # 顯示錯誤訊息
            return  # 結束本次執行

    result = st.session_state.get("result")  # 讀取已完成的處理結果
    if not result:  # 尚無結果時顯示提示
        if not api_key.strip():  # 未輸入 API Key
            st.info("請先在側邊欄輸入 OpenAI API Key，再貼上 YouTube 網址並點擊「開始處理」。")
        else:  # 已有 API Key 但尚未處理
            st.info("輸入 YouTube 網址後，點擊「開始處理」。")
        return  # 等待使用者操作

    lang_name = language_label(result.get("source_language"))  # 來源語言中文名稱
    st.success(f"處理完成：{result['title']}（來源語言：{lang_name}）")  # 顯示成功訊息與語言
    st.markdown("---")  # 分隔線
    st.subheader("▶️ 播放影片（中文字幕）")  # 播放區標題

    if result["use_burn_in"]:  # 燒錄模式：直接播放含字幕影片
        st.video(result["burned_path"])  # Streamlit 內建影片播放器
        burned_bytes = Path(result["burned_path"]).read_bytes()  # 讀取影片二進位資料
        st.download_button(  # 提供下載按鈕
            "下載含字幕影片",  # 按鈕文字
            data=burned_bytes,  # 下載內容
            file_name=f"{result['stem']}_zh.mp4",  # 下載檔名
            mime="video/mp4",  # MIME 類型
        )
    else:  # 疊加模式：HTML 播放器即時顯示字幕
        player_html = build_video_player_html(  # 產生含字幕疊加的 HTML
            Path(result["video_path"]), result["translated"]
        )
        components.html(player_html, height=520, scrolling=False)  # 嵌入自訂播放器

    with st.expander("📄 字幕內容預覽", expanded=False):  # 可展開的字幕清單
        for seg in result["translated"]:  # 逐段顯示字幕
            src_text = seg.get("text_src") or seg.get("text_en", "")  # 相容舊資料的原文欄位
            st.markdown(  # 以 Markdown 顯示時間軸與原文中文對照
                f"**[{seg['start']:.1f}s - {seg['end']:.1f}s]** "  # 時間範圍
                f"{seg['text_zh']}  \n"  # 中文譯文
                f"<span style='color:gray'>原文: {src_text}</span>",  # 灰色原文
                unsafe_allow_html=True,  # 允許渲染 HTML
            )

    st.download_button(  # SRT 字幕下載按鈕
        "下載 SRT 字幕檔",  # 按鈕文字
        data=result["srt_text"],  # SRT 內容
        file_name=f"{result['stem']}_zh.srt",  # 下載檔名
        mime="text/plain",  # 純文字 MIME
    )


if __name__ == "__main__":  # 直接執行此檔案時進入點
    main()  # 呼叫主函式
