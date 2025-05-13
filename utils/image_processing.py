import cv2
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from utils.config import load_settings

def capture():
    cap = cv2.VideoCapture(2)
    if not cap.isOpened():
        print("エラー: Webカメラを開けません")
        return None

    ret, frame = cap.read()
    cap.release()

    if not ret:
        print("エラー: Webカメラから画像を取得できません")
        return None

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    camera_image = Image.fromarray(rgb_frame)

    width, height = camera_image.size
    target_aspect = 16 / 9
    current_aspect = width / height

    if current_aspect > target_aspect:
        new_width = int(height * target_aspect)
        left = (width - new_width) // 2
        right = (width + new_width) // 2
        cropped_image = camera_image.crop((left, 0, right, height))
    elif current_aspect < target_aspect:
        new_height = int(width / target_aspect)
        top = (height - new_height) // 2
        bottom = (height + new_height) // 2
        cropped_image = camera_image.crop((0, top, width, bottom))
    else:
        cropped_image = camera_image

    return cropped_image


def draw_markdown(
    draw, text, x, y, width, font_path, base_font_size=20, color=(0, 0, 0)
):
    lines = text.split("\n")
    current_y = y
    line_height = base_font_size * 1.2

    for line in lines:
        if line.startswith("# "):
            font_size = base_font_size * 1.5
            font = ImageFont.truetype(font_path, int(font_size))
            text_content = line[2:]
            draw.text((x, current_y), text_content, font=font, fill=color)
            current_y += line_height * 1.5
        elif line.startswith("- "):
            font = ImageFont.truetype(font_path, int(base_font_size))
            # 箇条書きの記号を描画
            marker_radius = 5
            marker_x = x + marker_radius
            marker_y = current_y + base_font_size // 2
            draw.ellipse(
                (
                    marker_x - marker_radius,
                    marker_y - marker_radius,
                    marker_x + marker_radius,
                    marker_y + marker_radius,
                ),
                fill=color,
            )
            text_content = line[2:]
            draw.text(
                (x + marker_radius * 3, current_y), text_content, font=font, fill=color
            )
            current_y += line_height
        elif line.startswith("* "):  # 箇条書きの別記号
            font = ImageFont.truetype(font_path, int(base_font_size))
            text_content = line[2:]
            draw.text(
                (x + base_font_size // 2, current_y),
                "• " + text_content,
                font=font,
                fill=color,
            )
            current_y += line_height
        elif line.strip():
            font = ImageFont.truetype(font_path, int(base_font_size))
            draw.text((x, current_y), line, font=font, fill=color)
            current_y += line_height

        if current_y > y + 1000:  # Safety break to avoid infinite loops
            break
    return current_y

def generate_image(start_time=datetime.now(), example=False):
    if example:
        webcam_image = Image.open("alt_webcam.png")
    else:
        webcam_image = capture()
    if webcam_image is None:
        print("エラー: Webカメラを開けません")
        return None

    settings = load_settings()  # 設定ファイルの読み込み

    lower_text = settings.get("lower_text")
    right_long_text = settings.get("right_long_text")
    font_path = settings.get("font_path")
    resolution_str = settings.get("resolution", "1280x720")
    canvas_width, canvas_height = map(int, resolution_str.split("x"))
    mosaic_size = settings.get("mosaic_size", 10)
    grayscale = settings.get("grayscale", False)

    canvas = Image.new("RGB", (canvas_width, canvas_height), color="white")
    draw = ImageDraw.Draw(canvas)

    webcam_width, webcam_height = webcam_image.size
    paste_height = int(canvas_height * 0.85)
    paste_width = int(paste_height * webcam_width / webcam_height)
    paste_x = 0
    paste_y = int(canvas_height * 0.05)
    resized_webcam_image = webcam_image.resize(
        (paste_width, paste_height), Image.Resampling.LANCZOS
    )
    if mosaic_size > 0:
        # モザイク処理
        resized_webcam_image = resized_webcam_image.resize(
            (paste_width // mosaic_size, paste_height // mosaic_size), Image.Resampling.LANCZOS
        )
        resized_webcam_image = resized_webcam_image.resize(
            (paste_width, paste_height), Image.Resampling.NEAREST
        )

    if grayscale:
        # グレースケール処理
        resized_webcam_image = resized_webcam_image.convert("L").convert("RGB")

    canvas.paste(resized_webcam_image, (paste_x, paste_y))

    # 2. ウェブカメラ画像の上部
    upper_height = int(canvas_height * 0.05)
    upper_part = Image.new("RGB", (paste_width, upper_height), color="white")
    upper_draw = ImageDraw.Draw(upper_part)

    # 左側のテキスト
    font_size_upper = int(upper_height * 0.5)
    try:
        font_upper = ImageFont.truetype(font_path, font_size_upper)
    except IOError:
        font_upper = ImageFont.load_default()

    now = datetime.now()
    elapsed = now - start_time

    hours, remainder = divmod(elapsed.seconds, 3600)
    minutes = remainder // 60
    upper_left_text = f"経過時間: {hours}時間{minutes}分"

    text_bbox_left = upper_draw.textbbox((0, 0), upper_left_text, font=font_upper)
    text_width_left = text_bbox_left[2] - text_bbox_left[0]
    text_height_left = text_bbox_left[3] - text_bbox_left[1]
    text_x_left = 0
    text_y_left = int(upper_height / 2 - text_height_left / 2)
    upper_draw.text(
        (text_x_left, text_y_left), upper_left_text, font=font_upper, fill=(0, 0, 0)
    )

    # 右側の現在時間
    current_time_str = now.strftime("%Y年%m月%d日 %H:%M")
    text_bbox_right = upper_draw.textbbox((0, 0), current_time_str, font=font_upper)
    text_width_right = text_bbox_right[2] - text_bbox_right[0]
    text_height_right = text_bbox_right[3] - text_bbox_right[1]
    text_x_right = paste_width / 2 - text_width_right / 2  # ウェブカメラ画像の中央
    text_y_right = int(upper_height / 2 - text_height_right / 2)
    upper_draw.text(
        (text_x_right, text_y_right), current_time_str, font=font_upper, fill=(0, 0, 0)
    )

    canvas.paste(upper_part, (0, 0))

    # 3. ウェブカメラ画像の下部
    lower_height = int(canvas_height * 0.10)
    lower_part = Image.new("RGB", (paste_width, lower_height), color="white")
    lower_draw = ImageDraw.Draw(lower_part)
    font_size_lower = int(lower_height * 0.6)
    try:
        font_lower = ImageFont.truetype(font_path, font_size_lower)
    except IOError:
        font_lower = ImageFont.load_default()
    text_bbox_lower = lower_draw.textbbox((0, 0), lower_text, font=font_lower)
    text_width_lower = text_bbox_lower[2] - text_bbox_lower[0]
    text_height_lower = text_bbox_lower[3] - text_bbox_lower[1]
    text_x_lower = 0  # 左揃え
    text_y_lower = int(lower_height / 2 - text_height_lower / 2)
    lower_draw.text(
        (text_x_lower, text_y_lower), lower_text, font=font_lower, fill=(0, 0, 0)
    )
    canvas.paste(lower_part, (0, paste_y + paste_height))

    # 4. 右側の領域
    right_width = canvas_width - paste_width
    right_height = canvas_height
    right_part = Image.new("RGB", (right_width, right_height), color="white")
    right_draw = ImageDraw.Draw(right_part)
    markdown_x = 20
    markdown_y = 20
    markdown_width = right_width - 40

    try:
        font_markdown = ImageFont.truetype(font_path, 30)
    except IOError:
        font_markdown = ImageFont.load_default()

    draw_markdown(
        right_draw, right_long_text, markdown_x, markdown_y, markdown_width, font_path
    )

    canvas.paste(right_part, (paste_width, 0))

    return canvas


def main():
    final_image = generate_image()
    if final_image:
        final_image.save("final_webcam_image.png")
        print("画像を final_webcam_image.png として保存しました。")
        final_image.show()


if __name__ == "__main__":
    main()
