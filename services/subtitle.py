"""字幕格式化、SRT 產生、燒錄與 HTML 播放器模組。"""  # 模組說明

from __future__ import annotations  # 啟用延遲型別註解

import base64  # 將影片編碼為 base64 嵌入 HTML
import json  # 將字幕片段序列化供 JavaScript 使用
import subprocess  # 呼叫 ffmpeg 燒錄字幕
from pathlib import Path  # 檔案路徑操作

import imageio_ffmpeg  # 取得 ffmpeg 執行檔路徑


def format_timestamp(seconds: float) -> str:  # 將秒數轉為 SRT 時間格式
    hours = int(seconds // 3600)  # 計算小時數
    minutes = int((seconds % 3600) // 60)  # 計算分鐘數
    secs = int(seconds % 60)  # 計算秒數（整數部分）
    millis = int((seconds % 1) * 1000)  # 計算毫秒部分
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"  # 格式化為 HH:MM:SS,mmm


def segments_to_srt(segments: list[dict]) -> str:  # 將片段清單轉為 SRT 字串
    lines: list[str] = []  # 存放 SRT 各行內容
    for i, seg in enumerate(segments, start=1):  # 從 1 開始編號字幕序號
        start = format_timestamp(seg["start"])  # 格式化開始時間
        end = format_timestamp(max(seg["end"], seg["start"] + 0.5))  # 結束時間至少 0.5 秒
        lines.extend([str(i), f"{start} --> {end}", seg["text_zh"], ""])  # 序號、時間軸、中文、空行
    return "\n".join(lines)  # 以換行組合成完整 SRT


def save_srt(segments: list[dict], output_path: Path) -> Path:  # 寫入 SRT 檔案
    output_path.write_text(segments_to_srt(segments), encoding="utf-8")  # UTF-8 寫入字幕
    return output_path  # 回傳輸出路徑


def burn_subtitles(video_path: Path, srt_path: Path, output_path: Path) -> Path:  # 將字幕燒進影片
    """Burn Chinese subtitles into video using ffmpeg."""  # 函式文件字串
    srt_escaped = str(srt_path).replace("\\", "/").replace(":", "\\:")  # Windows 路徑轉義供 ffmpeg 使用

    cmd = [  # ffmpeg 燒錄字幕命令
        imageio_ffmpeg.get_ffmpeg_exe(),  # ffmpeg 執行檔
        "-y",  # 覆寫輸出檔
        "-i",  # 輸入參數
        str(video_path),  # 來源影片
        "-vf",  # 視訊濾鏡參數
        (
            f"subtitles='{srt_escaped}':"  # 載入 SRT 字幕檔
            "force_style='FontName=Microsoft JhengHei,FontSize=24,"  # 字型與大小
            "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"  # 白字黑邊
            "BorderStyle=1,Outline=2,Shadow=1,MarginV=30'"  # 描邊、陰影、下邊距
        ),
        "-c:a",  # 音訊編碼參數
        "copy",  # 音訊直接複製，不重新編碼
        str(output_path),  # 輸出影片路徑
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)  # 執行 ffmpeg
    if result.returncode != 0:  # 執行失敗
        raise RuntimeError(f"字幕燒錄失敗: {result.stderr}")  # 拋出錯誤

    return output_path  # 回傳燒錄後影片路徑


def build_video_player_html(video_path: Path, segments: list[dict], width: int = 900) -> str:  # 建立 HTML 播放器
    """Build HTML5 video player with synchronized Chinese subtitle overlay."""  # 函式文件字串
    video_bytes = video_path.read_bytes()  # 讀取影片二進位資料
    video_b64 = base64.b64encode(video_bytes).decode("ascii")  # 轉為 base64 字串
    subtitles_json = json.dumps(segments, ensure_ascii=False)  # 字幕 JSON 供 JS 使用

    # 回傳含 base64 影片與 JS 同步字幕的完整 HTML 頁面
    return f"""
<!DOCTYPE html>  <!-- HTML5 文件類型 -->
<html>  <!-- 根元素 -->
<head>  <!-- 頁首：樣式與編碼 -->
  <meta charset="utf-8" />  <!-- UTF-8 編碼，支援中文 -->
  <style>  <!-- CSS 樣式區塊 -->
    body {{  /* 頁面整體樣式 */
      margin: 0;  /* 移除外邊距 */
      font-family: "Microsoft JhengHei", "PingFang TC", "Noto Sans TC", sans-serif;  /* 中文字型 */
      background: #111;  /* 深色背景 */
    }}
    .player-wrap {{  /* 播放器外層容器 */
      position: relative;  /* 相對定位，供字幕絕對定位參考 */
      width: {width}px;  /* 播放器寬度 */
      max-width: 100%;  /* 響應式最大寬度 */
      margin: 0 auto;  /* 水平置中 */
      background: #000;  /* 黑色背景 */
    }}
    video {{  /* 影片元素樣式 */
      width: 100%;  /* 填滿容器寬度 */
      display: block;  /* 區塊顯示 */
      background: #000;  /* 載入前黑色背景 */
    }}
    .subtitle {{  /* 字幕疊加層樣式 */
      position: absolute;  /* 絕對定位在影片上方 */
      left: 50%;  /* 水平起點置中 */
      bottom: 8%;  /* 距底部 8% */
      transform: translateX(-50%);  /* 向左偏移自身寬度一半以置中 */
      width: 92%;  /* 字幕區寬度 */
      text-align: center;  /* 文字置中 */
      color: #fff;  /* 白色文字 */
      font-size: 26px;  /* 字體大小 */
      font-weight: 700;  /* 粗體 */
      line-height: 1.45;  /* 行高 */
      text-shadow:  /* 文字陰影提升可讀性 */
        2px 2px 4px rgba(0, 0, 0, 0.95),
        -1px -1px 2px rgba(0, 0, 0, 0.8);
      pointer-events: none;  /* 不攔截滑鼠事件，方便操作影片 */
      z-index: 10;  /* 顯示在影片上方 */
      padding: 8px 12px;  /* 內距 */
      background: rgba(0, 0, 0, 0.35);  /* 半透明黑底 */
      border-radius: 8px;  /* 圓角 */
      min-height: 1.5em;  /* 最小高度避免跳動 */
    }}
  </style>
</head>
<body>  <!-- 頁面主體 -->
  <div class="player-wrap">  <!-- 播放器容器 -->
    <video id="video" controls>  <!-- HTML5 影片，顯示控制列 -->
      <source src="data:video/mp4;base64,{video_b64}" type="video/mp4" />  <!-- base64 內嵌影片 -->
    </video>
    <div id="subtitle" class="subtitle"></div>  <!-- 字幕顯示區，由 JS 更新 -->
  </div>
  <script>  <!-- JavaScript：同步字幕與播放時間 -->
    const segments = {subtitles_json};  // 注入字幕片段資料
    const video = document.getElementById("video");  // 取得影片元素
    const subtitleEl = document.getElementById("subtitle");  // 取得字幕元素

    function updateSubtitle() {{  // 依目前播放時間更新字幕
      const t = video.currentTime;  // 目前播放秒數
      const active = segments.find(seg => t >= seg.start && t <= seg.end);  // 找出對應片段
      subtitleEl.textContent = active ? active.text_zh : "";  // 顯示中文或清空
    }}

    video.addEventListener("timeupdate", updateSubtitle);  // 播放中持續更新
    video.addEventListener("seeked", updateSubtitle);  // 拖曳進度後更新
    video.addEventListener("play", updateSubtitle);  // 開始播放時更新
  </script>
</body>
</html>
"""
