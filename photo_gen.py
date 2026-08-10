"""
PAGAL Escrow Bot - Group Photo Generator
Overlays buyer/seller names on template image
"""
import os
import logging
from PIL import Image, ImageDraw, ImageFont
from config import TEMPLATE_PATH, FONT_PATH

logger = logging.getLogger(__name__)

def generate_group_photo(buyer_username, seller_username, output_path="generated_photo.png"):
    """
    Generates group photo with buyer/seller overlay.
    Template should have P.A.G.A.L ESCROW BOT logo.
    Text added at bottom: 💰 BUYER: @xxx / 💰 SELLER: @xxx
    """
    try:
        if not os.path.exists(TEMPLATE_PATH):
            logger.error(f"Template not found: {TEMPLATE_PATH}")
            return None

        img = Image.open(TEMPLATE_PATH).convert("RGBA")
        draw = ImageDraw.Draw(img)
        width, height = img.size

        # Try to load font, fallback to default
        try:
            if os.path.exists(FONT_PATH):
                font_large = ImageFont.truetype(FONT_PATH, 42)
                font_small = ImageFont.truetype(FONT_PATH, 32)
            else:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
        except Exception:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Colors (white text with slight shadow for readability)
        text_color = (255, 255, 255, 255)
        shadow_color = (0, 0, 0, 180)

        # Position text at bottom center area (adjust based on your template)
        # These coordinates work for a typical 500x500 or similar group photo
        y_base = height - 140
        x_center = width // 2

        buyer_text = f"💰 BUYER: @{buyer_username}"
        seller_text = f"💰 SELLER: @{seller_username}"

        # Calculate text widths for centering
        def get_text_width(text, font):
            bbox = draw.textbbox((0, 0), text, font=font)
            return bbox[2] - bbox[0]

        bw = get_text_width(buyer_text, font_large)
        sw = get_text_width(seller_text, font_large)

        bx = (width - bw) // 2
        sx = (width - sw) // 2

        # Draw shadow first
        draw.text((bx+2, y_base+2), buyer_text, font=font_large, fill=shadow_color)
        draw.text((sx+2, y_base+52), seller_text, font=font_large, fill=shadow_color)

        # Draw main text
        draw.text((bx, y_base), buyer_text, font=font_large, fill=text_color)
        draw.text((sx, y_base+50), seller_text, font=font_large, fill=text_color)

        img.save(output_path)
        logger.info(f"Photo generated: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Photo generation failed: {e}")
        return None
