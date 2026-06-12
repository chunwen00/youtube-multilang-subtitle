"""YouTube 影片下載與音訊擷取模組。"""  # 模組說明

from __future__ import annotations  # 啟用延遲型別註解

import subprocess  # 呼叫 ffmpeg 外部程序
from pathlib import Path  # 路徑物件操作

import imageio_ffmpeg  # 內建 ffmpeg 執行檔路徑
import yt_dlp  # YouTube 下載函式庫

WHISPER_MAX_BYTES = 25 * 1024 * 1024  # Whisper API 音訊檔案上限 25MB


def _ffmpeg_exe() -> str:  # 取得 ffmpeg 可執行檔完整路徑
    return imageio_ffmpeg.get_ffmpeg_exe()  # 由 imageio-ffmpeg 套件提供


def download_video(url: str, output_dir: Path) -> tuple[Path, str]:  # 下載影片，回傳路徑與標題
    """Download YouTube video and return (video_path, title)."""  # 函式文件字串
    output_dir.mkdir(parents=True, exist_ok=True)  # 確保輸出目錄存在
    output_template = str(output_dir / "%(title)s.%(ext)s")  # yt-dlp 輸出檔名模板

    ffmpeg_path = _ffmpeg_exe()  # 取得 imageio-ffmpeg 內建的 ffmpeg 路徑
    ydl_opts = {  # yt-dlp 下載選項
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",  # 優先 mp4 最佳畫質
        "merge_output_format": "mp4",  # 合併後輸出為 mp4
        "ffmpeg_location": ffmpeg_path,  # 指定 ffmpeg，供合併影音使用
        "outtmpl": output_template,  # 輸出路徑模板
        "noplaylist": True,  # 只下載單一影片，不下整個播放清單
        "quiet": True,  # 減少終端機輸出
        "no_warnings": True,  # 不顯示警告訊息
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # 建立 yt-dlp 下載器
        info = ydl.extract_info(url, download=True)  # 解析網址並下載
        video_path = Path(ydl.prepare_filename(info))  # 取得下載後檔案路徑
        title = info.get("title", video_path.stem)  # 取得影片標題，無則用檔名

    if video_path.suffix != ".mp4":  # 若副檔名不是 mp4
        mp4_path = video_path.with_suffix(".mp4")  # 嘗試對應的 mp4 路徑
        if mp4_path.exists():  # mp4 檔案存在
            video_path = mp4_path  # 改用 mp4 路徑

    if not video_path.exists():  # 下載後檔案不存在
        raise RuntimeError(f"影片檔案不存在: {video_path}")  # 拋出錯誤

    return video_path, title  # 回傳影片路徑與標題


def extract_audio(video_path: Path, output_dir: Path) -> Path:  # 從影片擷取 mp3 音訊
    """Extract audio from video as mp3 for Whisper (max 25MB)."""  # 函式文件字串
    output_dir.mkdir(parents=True, exist_ok=True)  # 確保音訊輸出目錄存在
    audio_path = output_dir / f"{video_path.stem}.mp3"  # 音訊輸出檔名
    ffmpeg = _ffmpeg_exe()  # 取得 ffmpeg 路徑

    for bitrate in ("64k", "48k", "32k", "24k"):  # 依序嘗試不同位元率壓縮
        cmd = [  # ffmpeg 命令參數
            ffmpeg,  # ffmpeg 執行檔
            "-y",  # 覆寫已存在輸出檔
            "-i",  # 指定輸入檔
            str(video_path),  # 來源影片路徑
            "-vn",  # 不處理影像，只擷取音訊
            "-acodec",  # 指定音訊編碼器
            "libmp3lame",  # 使用 mp3 編碼
            "-b:a",  # 音訊位元率參數
            bitrate,  # 目前嘗試的位元率
            "-ar",  # 取樣率參數
            "16000",  # 16kHz，適合語音辨識
            "-ac",  # 聲道數參數
            "1",  # 單聲道
            str(audio_path),  # 輸出 mp3 路徑
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)  # 執行 ffmpeg
        if result.returncode != 0:  # 命令執行失敗
            raise RuntimeError(f"音訊擷取失敗: {result.stderr}")  # 拋出錯誤

        if audio_path.stat().st_size <= WHISPER_MAX_BYTES:  # 檔案大小符合 API 限制
            return audio_path  # 回傳音訊路徑

    raise RuntimeError("音訊檔案超過 25MB 上限，請使用較短的影片。")  # 所有位元率仍過大
