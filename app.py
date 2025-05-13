import os
import threading

from time import sleep
from flask import Flask, session, render_template, request, jsonify, flash, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import (
    IntegerField,
    BooleanField,
    StringField,
    SubmitField,
    TextAreaField,
    SelectField,
)
from wtforms.validators import NumberRange

from utils.stream import LiveStreamer
from utils.config import load_settings, update_settings
from utils.image_processing import generate_image

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24)

streamer = None

class DisplaySettingsForm(FlaskForm):
    lower_text = StringField("下部テキスト")
    right_long_text = TextAreaField("右側長文テキスト")
    font_path = StringField("フォントパス")
    grayscale = BooleanField("グレースケール")
    mosaic_size = IntegerField("モザイクサイズ", validators=[NumberRange(min=0)])
    submit = SubmitField("設定を保存")


class StreamSettingsForm(FlaskForm):
    title = StringField("配信名")
    description = TextAreaField("配信の概要欄")
    privacy = SelectField(
        "公開範囲",
        choices=[
            ("public", "公開"),
            ("unlisted", "限定公開"),
            ("private", "非公開"),
        ],
    )
    interval = IntegerField("インターバル（秒）", validators=[NumberRange(min=1)])
    resolution = SelectField(
        "解像度",
        choices=[
            ("1920x1080", "1080p"),
            ("1280x720", "720p"),
            ("854x480", "480p"),
            ("640x360", "360p"),
            ("426x240", "240p"),
        ],
    )
    fps = IntegerField("FPS", validators=[NumberRange(min=1)])
    submit = SubmitField("設定を保存")

@app.route('/static/<path:filename>')
def static_files(filename):
    return app.send_static_file(filename)

@app.route("/")
def index():
    global streamer
    settings = load_settings()
    display_form = DisplaySettingsForm(
        lower_text=settings.get("lower_text", "画面下部に表示するテキスト"),
        right_long_text=settings.get("right_long_text", "画面右側に表示するテキスト\n改行可能\n# h1の見出しのみ使用可能\n- 箇条書き可能"),
        font_path=settings.get("font_path", "font/MPLUS1p-Regular.ttf"),
        grayscale=settings.get("grayscale", False),
        mosaic_size=settings.get("mosaic_size", 0),
    )
    stream_form = StreamSettingsForm(
        title=settings["youtube"].get("title", "タイトルなし"),
        description=settings["youtube"].get("description", "概要なし"),
        privacy=settings["youtube"].get("privacy", "unlisted"),
        interval=settings.get("interval", 5),
        resolution=settings.get("resolution", "1920x1080"),
        fps=settings.get("fps", 30),
    )
    stream_settings = settings
    display_settings = settings

    stream_url = None
    stream_exsists = streamer._is_running if streamer else False
    if stream_exsists:
        sleep(10)
        stream_url = "https://www.youtube.com/watch?v=" + streamer.youtube_broadcast_id
    return render_template(
        "index.html",
        display_form=display_form,
        stream_form=stream_form,
        stream_settings=stream_settings,
        display_settings=display_settings,
        stream_exsists=stream_exsists,
        stream_url=stream_url
    )

@app.route('/start_stream', methods=['GET'])
def start_stream():
    global streamer
    global streamer_thread
    if streamer is None or not streamer._is_running:
        streamer = LiveStreamer()
        streamer_thread = threading.Thread(target=streamer.start_streaming, daemon=True)
        streamer_thread.start()
        flash(f"ライブ配信が開始されました", "success")
        return redirect(url_for('index'))
    else:
        flash("ライブ配信はすでに実行中です", "danger")
        return redirect(url_for('index'))

@app.route('/stop_stream', methods=['GET'])
def stop_stream():
    global streamer
    global streamer_thread
    if streamer and streamer._is_running:
        streamer.stop_streaming()
        # スレッドの終了を待機 (オプション)
        if streamer_thread and streamer_thread.is_alive():
            streamer_thread.join(timeout=10)
        streamer = None
        streamer_thread = None
        flash("ライブ配信が停止されました", "success")
        return redirect(url_for('index'))
    else:
        flash("ライブ配信は実行されていません", "danger")
        return redirect(url_for('index'))

@app.route("/update_display_settings", methods=["POST"])
def update_display_settings():
    form = DisplaySettingsForm()
    if form.validate_on_submit():
        settings = {
            "lower_text": form.lower_text.data,
            "right_long_text": form.right_long_text.data,
            "grayscale": form.grayscale.data,
            "mosaic_size": form.mosaic_size.data,
        }
        update_settings(settings)
        canvas = generate_image(example=True)
        canvas.save("static/display.png")
        flash("表示設定が保存されました", "success")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", "danger")

        flash("表示設定の保存に失敗しました", "danger")
    return redirect(url_for("index"))

@app.route("/update_stream_settings", methods=["POST"])
def update_stream_settings():
    form = StreamSettingsForm()
    if form.validate_on_submit():
        settings = {
            "youtube": {
                "title": form.title.data,
                "description": form.description.data,
                "privacy": form.privacy.data,
            },
            "fps": form.fps.data,
            "resolution": form.resolution.data,
            "interval": form.interval.data,
        }
        update_settings(settings)
        flash("配信設定が保存されました", "success")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", "danger")

        flash("配信設定の保存に失敗しました", "danger")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
