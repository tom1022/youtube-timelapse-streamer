import json

FONT_PATH = "font/MPLUS1p-Regular.ttf"
SETTINGS_JSON_PATH = "settings.json"


def load_settings():
    default_settings = {
        "lower_text": "テキスト",
        "right_long_text": "# デフォルトテキスト\n- 例1\n- 例2",
        "font_path": FONT_PATH,
        "interval": 5,  # デフォルトのインターバル（秒）
        "stream_key": "YOUR_YOUTUBE_STREAM_KEY",  # デフォルトのストリームキー
        "resolution": "1280x720",  # デフォルトの解像度
        "fps": 30,  # デフォルトのFPS
        "youtube": {
            "title": "テスト",
            "description": "テスト配信",
            "privacy": "unlisted",
        },
    }
    try:
        with open(SETTINGS_JSON_PATH, "r", encoding="utf-8") as f:
            settings = json.load(f)
            # 不足しているキーをデフォルト値で補完
            return {**default_settings, **settings}
    except FileNotFoundError:
        print(
            f"エラー: 設定ファイル {SETTINGS_JSON_PATH} が見つかりません。デフォルト値を使用します。"
        )
        return default_settings
    except json.JSONDecodeError:
        print(
            f"エラー: 設定ファイル {SETTINGS_JSON_PATH} の読み込みに失敗しました。デフォルト値を使用します。"
        )
        return default_settings
    except Exception as e:
        print(f"エラー: 予期せぬエラーが発生しました: {e}。デフォルト値を使用します。")
        return default_settings


def deep_merge(original, updates):
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(original.get(key), dict):
            deep_merge(original[key], value)
        else:
            original[key] = value
    return original

def update_settings(updates):
    # 設定ファイル読み込み
    try:
        with open(SETTINGS_JSON_PATH, 'r') as f:
            original_data = json.load(f)
    except FileNotFoundError:
        original_data = {}

    # 差分マージ
    merged_data = deep_merge(original_data, updates)

    # ファイルに保存
    with open(SETTINGS_JSON_PATH, 'w') as f:
        json.dump(merged_data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    # 設定の読み込み
    settings = load_settings()
    print(settings)
