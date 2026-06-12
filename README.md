# YouTube 多語言即時翻譯中文字幕

下載 YouTube 影片，自動辨識語音並翻譯成**繁體中文**字幕，直接在影片畫面上顯示。支援英語、法語、俄語等多種語言。

## 功能特色

- **YouTube 影片下載**：透過 yt-dlp 下載影片
- **多語言語音辨識**：OpenAI Whisper 自動或手動指定來源語言
- **AI 翻譯**：OpenAI GPT 將原文翻譯成自然流暢的繁體中文字幕
- **字幕疊加顯示**：播放時即時同步顯示中文（微軟正黑體）
- **字幕燒錄**：大型影片可將字幕永久寫入畫面
- **匯出字幕**：可下載 SRT 字幕檔或含字幕的 MP4

## 支援的來源語言

| 語言 | 語言 | 語言 |
|------|------|------|
| 自動偵測 | 英語 | 法語 |
| 俄語 | 日語 | 韓語 |
| 西班牙語 | 德語 | 義大利語 |
| 葡萄牙語 | 阿拉伯語 | 越南語 |
| 泰語 | 中文 | 印地語 |
| 土耳其語 | 波蘭語 | 荷蘭語 |
| 瑞典語 | 烏克蘭語 | |

不確定影片語言時，建議使用「**自動偵測**」。已知語言可手動指定，有助提升辨識準確度。

## 技術架構

```
YouTube 網址
    ↓
yt-dlp 下載影片
    ↓
ffmpeg 擷取音訊
    ↓
OpenAI Whisper 語音辨識（含時間軸）
    ↓
OpenAI GPT 翻譯成繁體中文
    ↓
Streamlit 網頁播放 + 字幕疊加 / 燒錄
```

| 元件 | 用途 |
|------|------|
| [Streamlit](https://streamlit.io/) | 網頁介面 |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | YouTube 下載 |
| [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) | 內建 ffmpeg（音訊擷取、字幕燒錄） |
| [OpenAI Whisper](https://platform.openai.com/docs/guides/speech-to-text) | 語音轉文字 |
| [OpenAI GPT](https://platform.openai.com/) | 多語言翻譯 |

## 環境需求

- Python 3.10 以上
- [OpenAI API Key](https://platform.openai.com/api-keys)
- 網路連線

> 無需另外安裝 ffmpeg 或 yt-dlp 命令列工具，Python 依賴已內建處理。

## 安裝

```bash
# 克隆專案
git clone https://github.com/chunwen00/youtube-multilang-subtitle.git
cd youtube-multilang-subtitle

# 安裝依賴
pip install -r requirements.txt
```

## 使用方式

```bash
streamlit run app.py
```

瀏覽器開啟 `http://localhost:8501` 後：

1. 在**側邊欄**輸入 OpenAI API Key
2. 選擇**來源語言**（預設自動偵測）
3. 貼上 **YouTube 影片網址**
4. 點擊「**開始處理**」
5. 處理完成後播放影片，即可看到中文字幕

### 側邊欄設定說明

| 設定項 | 說明 |
|--------|------|
| OpenAI API Key | 從 OpenAI 平台取得，僅存在本次瀏覽器 session |
| 來源語言 | 自動偵測或手動指定（法語、俄語等） |
| 語音辨識模型 | 預設 `whisper-1` |
| 翻譯模型 | 預設 `gpt-4o-mini`（較省費用） |
| 大型影片燒錄字幕 | 影片 > 40MB 時建議開啟 |

## 專案結構

```
├── app.py                  # Streamlit 主程式
├── requirements.txt        # Python 依賴
├── .env.example            # 環境變數範例（可選）
└── services/
    ├── download.py         # YouTube 下載、音訊擷取
    ├── transcribe.py       # Whisper 語音辨識
    ├── translate.py        # GPT 多語言翻譯
    ├── subtitle.py         # SRT 產生、字幕燒錄、HTML 播放器
    └── languages.py        # 支援語言清單
```

## 注意事項

- **API 費用**：使用 Whisper 轉錄與 GPT 翻譯會產生 OpenAI API 費用
- **音訊大小限制**：Whisper API 單次上傳上限 25MB，過長影片會自動壓縮音訊；仍超過則需使用較短影片
- **影片大小**：小於 40MB 使用 HTML 即時疊加字幕；較大影片建議開啟「燒錄字幕」
- **API Key 安全**：請勿將 API Key 提交至 Git；本專案在網頁側邊欄輸入，不寫入檔案

## 常見問題

**Q: 處理失敗，提示 ffmpeg 相關錯誤？**  
A: 請確認已執行 `pip install -r requirements.txt`，`imageio-ffmpeg` 會提供內建 ffmpeg。

**Q: 辨識結果不準？**  
A: 在側邊欄手動選擇正確的來源語言，或確認影片音質清晰。

**Q: 可以翻譯成簡體中文嗎？**  
A: 目前預設輸出繁體中文，可在 `services/translate.py` 的提示詞中修改。

## 授權

本專案供學習與個人使用。下載 YouTube 影片請遵守相關服務條款與版權法規。

## 連結

- GitHub：https://github.com/chunwen00/youtube-multilang-subtitle
