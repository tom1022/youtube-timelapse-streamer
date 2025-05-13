# utils/youtube.py (修正後)
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from datetime import datetime, timezone
import os

SCOPES = ["https://www.googleapis.com/auth/youtube"]

def get_youtube_credentials():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def create_youtube_live(title: str, description: str = "", privacy: str = "unlisted") -> tuple:
    """
    YouTubeライブ配信を作成し、RTMP URL、共有URL、broadcast IDを返す

    :param title: 配信タイトル
    :param description: 概要欄（説明文）
    :param privacy: 公開範囲 ("public" / "unlisted" / "private")
    :param scheduled_start_time: 予約開始時間 (ISO8601形式, UTC), Noneなら即時配信
    :return: (rtmp_url, youtube_watch_url, broadcast_id)
    """
    credentials = get_youtube_credentials()
    youtube = build('youtube', 'v3', credentials=credentials)

    # ライブ配信作成
    broadcast_body = {
        "snippet": {
            "title": title,
            "description": description,
            "scheduledStartTime": datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        },
        "status": {
            "privacyStatus": privacy
        },
        "contentDetails": {
            "enableAutoStart": True,
            "enableAutoStop": True
        }
    }

    broadcast_response = youtube.liveBroadcasts().insert(
        part="snippet,status,contentDetails",
        body=broadcast_body
    ).execute()

    broadcast_id = broadcast_response['id']

    # ライブストリーム作成
    stream_response = youtube.liveStreams().insert(
        part="snippet,cdn",
        body={
            "snippet": {
                "title": f"{title}"
            },
            "cdn": {
                "frameRate": "30fps",
                "ingestionType": "rtmp",
                "resolution": "1080p"
            }
        }
    ).execute()

    stream_id = stream_response['id']

    # 配信とストリームを紐付け
    youtube.liveBroadcasts().bind(
        part="id,contentDetails",
        id=broadcast_id,
        streamId=stream_id
    ).execute()

    # RTMP URL取得
    ingestion_info = stream_response['cdn']['ingestionInfo']
    rtmp_url = f"{ingestion_info['ingestionAddress']}/{ingestion_info['streamName']}"

    # YouTubeの共有URL
    youtube_watch_url = f"https://www.youtube.com/watch?v={broadcast_id}"

    return rtmp_url, youtube_watch_url, broadcast_id

def stop_youtube_live(broadcast_id: str):
    """
    指定されたbroadcast IDのYouTubeライブ配信を停止する

    :param broadcast_id: 停止するライブ配信のID
    """
    credentials = get_youtube_credentials()
    youtube = build('youtube', 'v3', credentials=credentials)

    try:
        youtube.liveBroadcasts().update(
            part="status",
            body={
                "id": broadcast_id,
                "status": {
                    "lifeCycleStatus": "complete"
                }
            }
        ).execute()
        print(f"YouTubeライブ配信 (ID: {broadcast_id}) を正常に停止しました。")
    except Exception as e:
        print(f"YouTubeライブ配信の停止中にエラーが発生しました: {e}")

if __name__ == '__main__':
    # テスト用
    rtmp_url, youtube_watch_url, broadcast_id = create_youtube_live(
        title="テスト配信",
        description="これはテスト配信です。",
        privacy="unlisted"
    )
    print(f"RTMP URL: {rtmp_url}")
    print(f"YouTube Watch URL: {youtube_watch_url}")
    print(f"Broadcast ID: {broadcast_id}")

    # 少し待ってから停止 (テスト用)
    import time
    time.sleep(10)
    stop_youtube_live(broadcast_id)
