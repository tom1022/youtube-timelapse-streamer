import cv2
import numpy as np
from datetime import datetime
import time
import subprocess
import shlex
import threading
from utils.image_processing import generate_image
from utils.config import load_settings
from utils.youtube import create_youtube_live, stop_youtube_live
from utils.tweet import tweet_stream_info

class LiveStreamer:
    def __init__(self):
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        self.image_thread = None
        self.ffmpeg_process = None
        self._is_running = False
        self.youtube_broadcast_id = None # broadcast IDを保存する変数

    def generate_image_loop(self, start_time):
        settings = load_settings()
        interval = settings.get("interval")
        while self._is_running:
            canvas = generate_image(start_time=start_time)
            if canvas:
                frame_rgb = np.array(canvas, dtype=np.uint8)
                with self.frame_lock:
                    self.latest_frame = frame_rgb
            time.sleep(interval)

    def stream_to_ffmpeg(self):
        settings = load_settings()
        resolution = settings.get("resolution")
        fps = settings.get("fps")

        youtube_settings = settings.get("youtube")
        title = youtube_settings["title"]
        description = youtube_settings["description"]
        privacy = youtube_settings["privacy"]
        rtmp_url, youtube_watch_url, self.youtube_broadcast_id = create_youtube_live( # broadcast IDを受け取る
            title=title,
            description=description,
            privacy=privacy
        )
        tweet_stream_info(
            contents={
                "comment": settings.get("title", "配信開始しました！"),
                "url": youtube_watch_url
            }
        )

        command = shlex.split(
            f"ffmpeg -y -f rawvideo -vcodec rawvideo -pix_fmt rgb24 -s {resolution} -r {fps} -i - "
            f"-f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 "
            f"-b:v 2500k -maxrate 3000k -bufsize 5000k -c:a aac -b:a 96k -ac 2 -ar 44100 "
            f"-map 0:v -map 1:a -f flv {rtmp_url}"
        )

        try:
            self.ffmpeg_process = subprocess.Popen(command, stdin=subprocess.PIPE)
            print(f"配信を開始しました: {rtmp_url} (YouTube Broadcast ID: {self.youtube_broadcast_id})")

            while self._is_running and self.ffmpeg_process.poll() is None:
                with self.frame_lock:
                    frame_to_send = self.latest_frame
                if frame_to_send is not None:
                    frame_bgr = cv2.cvtColor(frame_to_send, cv2.COLOR_RGB2BGR)
                    try:
                        self.ffmpeg_process.stdin.write(frame_bgr.tobytes())
                        self.ffmpeg_process.stdin.flush()
                    except BrokenPipeError:
                        print("エラー: ffmpegパイプが閉じられました。配信を終了します。")
                        self.stop_streaming()
                        break
                time.sleep(1.0 / fps) # FPSに合わせて待機

            if self.ffmpeg_process and self.ffmpeg_process.returncode is not None:
                print(f"ffmpegプロセスが終了しました (終了コード: {self.ffmpeg_process.returncode})。")

        except FileNotFoundError:
            print("エラー: ffmpegが見つかりません。インストールされていることを確認してください。")
            self.stop_streaming()
        except Exception as e:
            print(f"エラー: ffmpegの起動またはストリーミング中にエラーが発生しました: {e}")
            self.stop_streaming()

    def start_streaming(self):
        if not self._is_running:
            self._is_running = True
            start_time = datetime.now()
            self.image_thread = threading.Thread(target=self.generate_image_loop, args=(start_time,), daemon=True)
            self.image_thread.start()
            threading.Thread(target=self.stream_to_ffmpeg, daemon=True).start()
            print("配信処理を開始しました。")
        else:
            print("配信はすでに開始されています。")

    def stop_streaming(self):
        if self._is_running:
            self._is_running = False
            print("配信を停止します...")

            # YouTubeライブ配信を停止
            if self.youtube_broadcast_id:
                stop_youtube_live(self.youtube_broadcast_id)
                self.youtube_broadcast_id = None

            # 画像生成スレッドの停止を待機
            if self.image_thread and self.image_thread.is_alive():
                self.image_thread.join(timeout=5)
                print("画像生成スレッドを停止しました。")

            # FFmpegプロセスの終了
            if self.ffmpeg_process and self.ffmpeg_process.poll() is None:
                print("ffmpegプロセスに終了シグナルを送信します...")
                self.ffmpeg_process.terminate()
                try:
                    self.ffmpeg_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print("警告: ffmpegプロセスが時間内に終了しませんでした。強制終了します。")
                    self.ffmpeg_process.kill()
                print("ffmpegプロセスを終了しました。")
            elif self.ffmpeg_process:
                print("ffmpegプロセスはすでに終了しています。")

            print("配信を完全に停止しました。")
        else:
            print("配信は現在実行されていません。")

def main():
    streamer = LiveStreamer()
    streamer.start_streaming()

    try:
        input("配信を終了するにはEnterキーを押してください...\n")
    except KeyboardInterrupt:
        print("\nCtrl+C が押されました。配信を終了します。")
    finally:
        streamer.stop_streaming()

if __name__ == "__main__":
    main()
