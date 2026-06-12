"""支援的來源語言設定。"""  # 模組說明

# Whisper 語言代碼 → 顯示名稱
LANGUAGE_NAMES: dict[str, str] = {
    "en": "英語",
    "fr": "法語",
    "ru": "俄語",
    "ja": "日語",
    "ko": "韓語",
    "es": "西班牙語",
    "de": "德語",
    "it": "義大利語",
    "pt": "葡萄牙語",
    "ar": "阿拉伯語",
    "vi": "越南語",
    "th": "泰語",
    "zh": "中文",
    "hi": "印地語",
    "tr": "土耳其語",
    "pl": "波蘭語",
    "nl": "荷蘭語",
    "sv": "瑞典語",
    "uk": "烏克蘭語",
}

# 側邊欄可選的來源語言（None 表示自動偵測）
SOURCE_LANGUAGE_OPTIONS: dict[str, str | None] = {
    "自動偵測": None,
    **{name: code for code, name in LANGUAGE_NAMES.items()},
}


def language_label(code: str | None) -> str:  # 將語言代碼轉為中文名稱
    if not code:  # 無代碼時
        return "未知語言"  # 預設顯示
    return LANGUAGE_NAMES.get(code, code)  # 查表或回傳原代碼
