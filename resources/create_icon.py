#!/usr/bin/env python3
"""
Create application icon for DXCom GUI.
Generates a professional icon with DX branding.
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size=256):
    """Create a professional icon with DX branding."""
    # Create image with gradient background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw rounded rectangle background (DEEPX blue gradient)
    # Using a professional blue color scheme
    margin = int(size * 0.05)
    
    # Background with gradient effect using overlapping rectangles
    colors = [
        (0, 102, 204),    # Deep blue
        (0, 122, 224),    # Medium blue
        (0, 142, 244),    # Light blue
    ]
    
    for i, color in enumerate(colors):
        alpha = 255 - (i * 30)
        offset = i * 5
        draw.rounded_rectangle(
            [margin + offset, margin + offset, size - margin - offset, size - margin - offset],
            radius=size // 8,
            fill=color + (alpha,)
        )
    
    # Draw "DX" text in white
    try:
        # Try to use a nice font, fall back to default if not available
        font_size = int(size * 0.4)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    text = "DX"
    
    # Get text bounding box for centering
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center the text
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - int(size * 0.05)  # Slightly higher
    
    # Draw text with shadow for depth
    shadow_offset = max(2, size // 64)
    draw.text((x + shadow_offset, y + shadow_offset), text, fill=(0, 0, 0, 128), font=font)
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
    
    # Add small compiler symbol below (a simple bracket-like icon)
    symbol_y = y + text_height + int(size * 0.05)
    symbol_size = int(size * 0.15)
    symbol_x = size // 2
    
    # Draw brackets: [ ]
    bracket_width = 3
    draw.rectangle(
        [symbol_x - symbol_size, symbol_y, symbol_x - symbol_size + bracket_width, symbol_y + symbol_size],
        fill=(255, 255, 255, 200)
    )
    draw.rectangle(
        [symbol_x - symbol_size, symbol_y, symbol_x - symbol_size // 2, symbol_y + bracket_width],
        fill=(255, 255, 255, 200)
    )
    draw.rectangle(
        [symbol_x - symbol_size, symbol_y + symbol_size - bracket_width, symbol_x - symbol_size // 2, symbol_y + symbol_size],
        fill=(255, 255, 255, 200)
    )
    
    draw.rectangle(
        [symbol_x + symbol_size - bracket_width, symbol_y, symbol_x + symbol_size, symbol_y + symbol_size],
        fill=(255, 255, 255, 200)
    )
    draw.rectangle(
        [symbol_x + symbol_size // 2, symbol_y, symbol_x + symbol_size, symbol_y + bracket_width],
        fill=(255, 255, 255, 200)
    )
    draw.rectangle(
        [symbol_x + symbol_size // 2, symbol_y + symbol_size - bracket_width, symbol_x + symbol_size, symbol_y + symbol_size],
        fill=(255, 255, 255, 200)
    )
    
    return img

if __name__ == '__main__':
    # Create icons in multiple sizes
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create 256x256 icon (main)
    icon_256 = create_icon(256)
    icon_256.save(os.path.join(script_dir, 'icon.png'))
    print("Created icon.png (256x256)")
    
    # Create smaller sizes for different uses
    icon_128 = create_icon(128)
    icon_128.save(os.path.join(script_dir, 'icon_128.png'))
    print("Created icon_128.png (128x128)")
    
    icon_64 = create_icon(64)
    icon_64.save(os.path.join(script_dir, 'icon_64.png'))
    print("Created icon_64.png (64x64)")
    
    icon_32 = create_icon(32)
    icon_32.save(os.path.join(script_dir, 'icon_32.png'))
    print("Created icon_32.png (32x32)")
    
    print("\nIcons created successfully in resources/ directory")
