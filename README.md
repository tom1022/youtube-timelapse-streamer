# YouTube Live Streaming System

カメラ映像にテキストやエフェクトを追加して、YouTubeに自動的にライブ配信するシステムです。

## 機能

- ウェブインターフェースによる直感的な操作
- カメラ映像にテキストやマークダウン形式の情報を表示
- グレースケールやモザイク効果の適用
- YouTube Live APIを使用した配信の自動作成と管理
- Twitter連携による配信開始の自動告知
- 配信設定のカスタマイズ（解像度、FPS、公開範囲など）

## スクリーンショット

![](/imgs/image.png)
![](/imgs/image-2.png)

## 必要条件

- Python 3.8以上
- FFmpeg
- YouTubeアカウント（ライブ配信が有効になっていること）
- Twitterアカウント（投稿機能を使用する場合）

## インストール

1. リポジトリをクローン

```bash
git clone https://github.com/tom1022/youtube-timelapse-streamer.git
cd youtube-timelapse-streamer
```

2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

3. FFmpegのインストール

- **Linux**:
```bash
sudo apt update
sudo apt install ffmpeg
```

- **MacOS**:
```bash
brew install ffmpeg
```

- **Windows**:
[FFmpegの公式サイト](https://ffmpeg.org/download.html)からダウンロードし、環境変数のPATHに追加してください。

## 設定

1. Google Cloud Platformで以下の操作を行います：
   - プロジェクトを作成
   - YouTube Data API v3を有効化
   - OAuthクライアントIDの作成（デスクトップアプリケーション）
   - client_secret.jsonファイルをダウンロードしてプロジェクトのルートディレクトリに配置

2. YouTubeアカウントでライブ配信が有効になっていることを確認します：
```bash
python utils/check.py
```

3. Twitter連携を使用する場合は、Twitter Developer Portalで以下の操作を行います：
   - アプリを作成
   - 認証キーとトークンを取得
   - settings.jsonファイルに追加

## 使い方

1. アプリケーションを起動します：
```bash
python app.py
```

2. ブラウザで http://localhost:5000 にアクセスします。

3. 表示設定と配信設定をカスタマイズします。

4. 「配信開始」ボタンをクリックしてライブ配信を開始します。

5. 配信を終了するには「配信停止」ボタンをクリックします。

## settings.jsonの例

```json
{
  "lower_text": "画面下部に表示するテキスト",
  "right_long_text": "# 右側のタイトル\n- 箇条書き1\n- 箇条書き2",
  "font_path": "font/MPLUS1p-Regular.ttf",
  "grayscale": false,
  "mosaic_size": 0,
  "interval": 5,
  "resolution": "1280x720",
  "fps": 30,
  "youtube": {
    "title": "ライブ配信のタイトル",
    "description": "ライブ配信の説明文",
    "privacy": "unlisted"
  },
  "tweet": {
    "consumer_api_key": "YOUR_CONSUMER_API_KEY",
    "consumer_api_secret": "YOUR_CONSUMER_API_SECRET",
    "access_token": "YOUR_ACCESS_TOKEN",
    "access_token_secret": "YOUR_ACCESS_TOKEN_SECRET",
    "bearer_token": "YOUR_BEARER_TOKEN"
  }
}
```

## プロジェクト構成

```
youtube-timelapse-streamer/
├── app.py                # メインアプリケーション
├── utils/
│   ├── check.py          # YouTube認証チェック
│   ├── config.py         # 設定管理
│   ├── image_processing.py # 画像処理
│   ├── stream.py         # 配信管理
│   ├── tweet.py          # Twitter投稿
│   └── youtube.py        # YouTube API連携
├── templates/
│   └── index.html        # Webインターフェース
├── static/
│   └── display.png       # プレビュー画像
├── font/
│   └── MPLUS1p-Regular.ttf # デフォルトフォント
├── requirements.txt      # 依存パッケージ
├── settings.json         # 設定ファイル
└── README.md             # 本ファイル
```

## トラブルシューティング

### FFmpegエラー
- FFmpegがインストールされていることを確認してください
- PATHに正しく設定されていることを確認してください

### YouTube API認証エラー
- client_secret.jsonが正しく配置されていることを確認してください
- YouTubeアカウントでライブ配信が有効になっていることを確認してください

### カメラが見つからない場合
- `image_processing.py`の`capture()`関数内のカメラインデックスを調整してください
  ```python
  cap = cv2.VideoCapture(0)
  ```

## ライセンス

MIT License - 詳細は[LICENSE](LICENSE)を参照してください。

## 謝辞

- [Flask](https://flask.palletsprojects.com/)
- [OpenCV](https://opencv.org/)
- [YouTube Data API](https://developers.google.com/youtube/v3)
- [Tweepy](https://www.tweepy.org/)
