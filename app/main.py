from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from io import BytesIO
import base64
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
from fastapi.responses import StreamingResponse, JSONResponse
import os
import re
import requests

app = FastAPI()

# Data models
class Box(BaseModel):
    text: str
    x: int
    y: int
    w: int  # Width of the box
    h: int  # Height of the box
    font: Optional[str] = "arial"
    fontsize: Optional[int] = None
    color: Optional[str] = None  # Text color
    border: Optional[str] = None  # Border (stroke) color

class ImageRequest(BaseModel):
    img: str = Field(..., description="URL or Base64-encoded PNG or JPG image to edit")
    boxes: List[Box]
    image_format: Optional[str] = None

    @validator('img')
    def validate_img(cls, v):
        # Check if 'v' is a valid URL
        url_regex = re.compile(
            r'^(https?://)'
            r'(([A-Za-z0-9-]+\.)+[A-Za-z]{2,6}'
            r'|'
            r'localhost'
            r'|'
            r'\d{1,3}(\.\d{1,3}){3})'
            r'(:\d+)?'
            r'(/.*)?$'
        )
        
        if url_regex.match(v):
            return v  # It's a URL
    
        # Attempt to decode base64 to ensure it's valid
        try:
            base64.b64decode(v)
            return v  # It's base64
        except base64.binascii.Error:
            raise ValueError("The 'img' field must be a valid URL or a base64-encoded image string.")
    

# Allowed image formats
ALLOWED_FORMATS = ("PNG", "JPEG", "JPG")

def fetch_image_from_url(url):
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        if image.format not in ALLOWED_FORMATS:
            raise HTTPException(status_code=400, detail=f"Unsupported image format: {image.format}")
        image_format = image.format
        image = image.convert("RGBA")
        image.format = image_format
        return image
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Error fetching image from URL: {e}")
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Unable to identify the image from the URL")

def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    line = ''
    for word in words:
        test_line = line + ' ' + word if line else word
        bbox = font.getbbox(test_line)
        line_width = bbox[2] - bbox[0]
        if line_width <= max_width:
            line = test_line
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines

def get_line_height(font):
    ascent, descent = font.getmetrics()
    return ascent + descent

def get_max_font_size_and_wrapped_text(text, font_path, max_width, max_height):
    min_size = 1
    max_size = 1000  # Arbitrary upper limit
    best_size = min_size
    best_lines = []

    # the best size is the largest size that fits within the box

    while min_size <= max_size:
        fontsize = (min_size + max_size) // 2
        font = ImageFont.truetype(font_path, fontsize)
        
        # Ensure no single word exceeds max_width
        words = text.split()
        max_word_width = max(font.getbbox(word)[2] - font.getbbox(word)[0] for word in words)
        if max_word_width > max_width:
            max_size = fontsize - 1
            continue

        lines = wrap_text(text, font, max_width)
        line_height = get_line_height(font)
        total_height = line_height * len(lines)
        if total_height <= max_height:
            best_size = fontsize
            best_lines = lines
            min_size = fontsize + 1
        else:
            max_size = fontsize - 1
    return best_size, best_lines

@app.post("/")
def add_captions(request: ImageRequest):
    try:
        img_input = request.img

        if re.match(r'^https?://', img_input):
            image = fetch_image_from_url(img_input)
        else:
            try:
                image_data = base64.b64decode(img_input)
                image = Image.open(BytesIO(image_data))
                if image.format not in ALLOWED_FORMATS:
                    raise HTTPException(status_code=400, detail=f"Unsupported image format: {image.format}")
                image_format = image.format
                image = image.convert("RGBA")
                image.format = image_format
            except (base64.binascii.Error, UnidentifiedImageError):
                raise HTTPException(status_code=400, detail="Invalid base64 image data.")

        input_format = image.format.lower()

        for box in request.boxes:
            draw = ImageDraw.Draw(image)

            font_name = box.font.lower()
            if font_name not in ["arial", "impact"]:
                raise HTTPException(status_code=400, detail="Unsupported font. Use 'arial' or 'impact'.")

            font_path = f"/usr/share/fonts/truetype/{font_name}/{font_name}.ttf"
            if not os.path.isfile(font_path):
                raise HTTPException(status_code=500, detail=f"Font file not found: {font_path}")

            if box.fontsize is None:
                fontsize, lines = get_max_font_size_and_wrapped_text(box.text, font_path, box.w, box.h)
                font = ImageFont.truetype(font_path, fontsize)
            else:
                fontsize = box.fontsize
                font = ImageFont.truetype(font_path, fontsize)
                lines = wrap_text(box.text, font, box.w)
                line_height = get_line_height(font)
                total_height = line_height * len(lines)
                if total_height > box.h:
                    raise HTTPException(status_code=400, detail=f"Text exceeds box height at specified fontsize {fontsize}.")

            # Set default colors based on font
            fill_color = box.color if box.color else ("black" if font_name == "arial" else "white")
            stroke_color = box.border if box.border else ("black" if font_name == "impact" else None)

            # Determine stroke width
            stroke_width = max(1, fontsize // 15) if stroke_color and stroke_color != fill_color else 0

            # Calculate total text height
            line_height = get_line_height(font)
            total_text_height = line_height * len(lines)
            # Calculate starting y to center text vertically
            current_y = box.y + (box.h - total_text_height) // 2

            for line in lines:
                # Calculate the width of the line
                line_width = font.getbbox(line)[2] - font.getbbox(line)[0]
                # Calculate x to center the line within the box
                line_x = box.x + (box.w - line_width) // 2
                draw.text(
                    (line_x, current_y),
                    line,
                    font=font,
                    fill=fill_color,
                    stroke_width=stroke_width,
                    stroke_fill=stroke_color
                )
                current_y += line_height

        output_format = request.image_format or f"b64/{input_format}"

        img_byte_arr = BytesIO()
        output_image_format = 'PNG' if 'png' in output_format.lower() else 'JPEG'

        if output_image_format == 'JPEG':
            image = image.convert("RGB")

        image.save(img_byte_arr, format=output_image_format)
        img_byte_arr.seek(0)

        if output_format.startswith("b64"):
            encoded_img = base64.b64encode(img_byte_arr.read()).decode('utf-8')
            return JSONResponse(content={"img": encoded_img})
        else:
            content_type = f"image/{output_image_format.lower()}"
            return StreamingResponse(img_byte_arr, media_type=content_type)

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
