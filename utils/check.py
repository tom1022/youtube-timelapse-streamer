from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# YouTube Data API v3 のスコープ (ライブ配信用)
SCOPES = ["https://www.googleapis.com/auth/youtube"]

# token.json から認証情報を読み込む
def load_credentials(token_file="token.json"):
    credentials = Credentials.from_authorized_user_file(token_file, SCOPES)
    return credentials

# チャンネル情報を取得してライブストリーミングの有効化を確認
def check_live_streaming_enabled(credentials):
    try:
        youtube = build("youtube", "v3", credentials=credentials)

        # 自分のチャンネル情報を取得
        request = youtube.channels().list(
            part="snippet,contentDetails,statistics,status",
            mine=True
        )
        response = request.execute()

        if not response.get("items"):
            print("チャンネル情報が取得できませんでした。")
            return False

        # チャンネル情報表示（オプション）
        channel = response["items"][0]
        print(f"チャンネル名: {channel['snippet']['title']}")
        print(f"チャンネルID: {channel['id']}")

        # liveBroadcasts API にアクセスして確認
        test_request = youtube.liveBroadcasts().list(
            part="id",
            broadcastStatus="all",
            maxResults=1
        )
        test_request.execute()

        print("✅ このアカウントはライブストリーミングが有効です。")
        return True

    except HttpError as e:
        if e.resp.status == 403:
            error_reason = e.error_details[0].get("reason", "")
            if error_reason == "liveStreamingNotEnabled":
                print("❌ このアカウントはライブストリーミングが有効化されていません。")
                print("https://www.youtube.com/features で有効にしてください。")
                return False
        print(f"❌ APIエラーが発生しました: {e}")
        return False

if __name__ == "__main__":
    creds = load_credentials("token.json")
    check_live_streaming_enabled(creds)
