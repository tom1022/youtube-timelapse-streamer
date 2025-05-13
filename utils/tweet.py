import tweepy
from utils.config import load_settings


def tweet_stream_info(
    contents = {
        "comment": "hogehogefugafuga",
        "url": "https://example.com",
    }
):
    # 設定を読み込む
    settings = load_settings()["tweet"]
    api_key = settings["consumer_api_key"]
    api_secret = settings["consumer_api_secret"]
    access_token = settings["access_token"]
    access_token_secret = settings["access_token_secret"]
    bearer_token = settings["bearer_token"]

    try:
        client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
        )

        # 投稿する内容
        tweet_text = f"""
        {contents['comment']}

        {contents['url']}
        """

        # ツイート投稿
        client.create_tweet(text=tweet_text)
    except Exception as e:
        print(f"ツイートの投稿中にエラーが発生しました: {e}")

if __name__ == "__main__":
    tweet_stream_info()
