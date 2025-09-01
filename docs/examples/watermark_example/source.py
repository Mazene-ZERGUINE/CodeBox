from PIL import Image, ImageDraw, ImageFont
import os
import sys

def resize_and_watermark(input_path, output_path, watermark_text, options=None):
    """
    Resize an image and add a text watermark
    
    Args:
        input_path (str): Path to input image
        output_path (str): Path to save processed image
        watermark_text (str): Text to use as watermark
        options (dict): Configuration options
    """
    if options is None:
        options = {}
    
    # Default options
    width = options.get('width', 800)
    height = options.get('height', None)  # None = maintain aspect ratio
    quality = options.get('quality', 85)
    watermark_position = options.get('watermark_position', 'bottom-right')
    watermark_opacity = options.get('watermark_opacity', 128)  # 0-255
    watermark_color = options.get('watermark_color', 'white')
    font_size = options.get('font_size', 32)
    margin = options.get('margin', 10)
    
    try:
        print('Loading image...')
        # Open and load the image
        image = Image.open(input_path)
        original_size = image.size
        print(f'Original size: {original_size[0]}x{original_size[1]}')
        
        # Convert to RGB if necessary (for JPEG output)
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        
        # Resize the image
        if height is None:
            # Maintain aspect ratio
            aspect_ratio = original_size[1] / original_size[0]
            height = int(width * aspect_ratio)
        
        print('Resizing image...')
        image = image.resize((width, height), Image.Resampling.LANCZOS)
        print(f'New size: {image.size[0]}x{image.size[1]}')
        
        # Create a transparent overlay for the watermark
        overlay = Image.new('RGBA', image.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Try to use a better font, fall back to default if not available
        try:
            # Try to find a system font
            if sys.platform.startswith('win'):
                font_path = 'C:/Windows/Fonts/arial.ttf'
            elif sys.platform.startswith('darwin'):  # macOS
                font_path = '/System/Library/Fonts/Arial.ttf'
            else:  # Linux
                font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
            
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
            else:
                raise OSError("Font not found")
        except (OSError, IOError):
            print("Using default font (system font not found)")
            try:
                font = ImageFont.load_default()
            except:
                font = ImageFont.load_default()
        
        # Get text dimensions
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Calculate watermark position
        image_width, image_height = image.size
        
        if watermark_position == 'top-left':
            x, y = margin, margin
        elif watermark_position == 'top-right':
            x, y = image_width - text_width - margin, margin
        elif watermark_position == 'bottom-left':
            x, y = margin, image_height - text_height - margin
        elif watermark_position == 'center':
            x, y = (image_width - text_width) // 2, (image_height - text_height) // 2
        else:  # bottom-right (default)
            x, y = image_width - text_width - margin, image_height - text_height - margin
        
        print(f'Adding watermark at position: ({x}, {y})')
        
        # Convert color name to RGB if needed
        if isinstance(watermark_color, str):
            color_map = {
                'white': (255, 255, 255, watermark_opacity),
                'black': (0, 0, 0, watermark_opacity),
                'red': (255, 0, 0, watermark_opacity),
                'blue': (0, 0, 255, watermark_opacity),
                'green': (0, 255, 0, watermark_opacity),
                'yellow': (255, 255, 0, watermark_opacity),
            }
            watermark_color = color_map.get(watermark_color.lower(), (255, 255, 255, watermark_opacity))
        
        # Add text to overlay
        draw.text((x, y), watermark_text, font=font, fill=watermark_color)
        
        # Composite the overlay onto the image
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        image = Image.alpha_composite(image, overlay)
        
        # Convert back to RGB for JPEG output
        if output_path.lower().endswith(('.jpg', '.jpeg')):
            image = image.convert('RGB')
        
        print('Saving processed image...')
        # Save with quality setting
        if output_path.lower().endswith(('.jpg', '.jpeg')):
            image.save(output_path, 'JPEG', quality=quality, optimize=True)
        else:
            image.save(output_path, quality=quality, optimize=True)
        
        print(f'✅ Image processed successfully!')
        print(f'📁 Saved to: {output_path}')
        
        return {
            'success': True,
            'original_size': original_size,
            'new_size': image.size,
            'output_path': output_path
        }
        
    except Exception as error:
        print(f'❌ Error processing image: {error}')
        return {
            'success': False,
            'error': str(error)
        }

def resize_and_watermark_image(input_path, output_path, watermark_image_path, options=None):
    """
    Resize an image and add an image watermark (logo)
    """
    if options is None:
        options = {}
    
    width = options.get('width', 800)
    height = options.get('height', None)
    quality = options.get('quality', 85)
    watermark_position = options.get('watermark_position', 'bottom-right')
    watermark_opacity = options.get('watermark_opacity', 0.7)  # 0.0 to 1.0
    watermark_scale = options.get('watermark_scale', 0.2)  # Scale relative to main image
    margin = options.get('margin', 10)
    
    try:
        print('Loading images...')
        # Load main image
        image = Image.open(input_path)
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        
        # Load watermark image
        watermark = Image.open(watermark_image_path)
        if watermark.mode != 'RGBA':
            watermark = watermark.convert('RGBA')
        
        # Resize main image
        original_size = image.size
        if height is None:
            aspect_ratio = original_size[1] / original_size[0]
            height = int(width * aspect_ratio)
        
        image = image.resize((width, height), Image.Resampling.LANCZOS)
        
        # Resize watermark
        wm_width = int(image.size[0] * watermark_scale)
        wm_aspect = watermark.size[1] / watermark.size[0]
        wm_height = int(wm_width * wm_aspect)
        watermark = watermark.resize((wm_width, wm_height), Image.Resampling.LANCZOS)
        
        # Apply opacity to watermark
        watermark_with_opacity = watermark.copy()
        alpha = watermark_with_opacity.split()[-1]  # Get alpha channel
        alpha = alpha.point(lambda p: int(p * watermark_opacity))  # Apply opacity
        watermark_with_opacity.putalpha(alpha)
        
        # Calculate position
        image_width, image_height = image.size
        
        if watermark_position == 'top-left':
            pos = (margin, margin)
        elif watermark_position == 'top-right':
            pos = (image_width - wm_width - margin, margin)
        elif watermark_position == 'bottom-left':
            pos = (margin, image_height - wm_height - margin)
        elif watermark_position == 'center':
            pos = ((image_width - wm_width) // 2, (image_height - wm_height) // 2)
        else:  # bottom-right
            pos = (image_width - wm_width - margin, image_height - wm_height - margin)
        
        # Paste watermark onto image
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        image.paste(watermark_with_opacity, pos, watermark_with_opacity)
        
        # Convert back for JPEG
        if output_path.lower().endswith(('.jpg', '.jpeg')):
            image = image.convert('RGB')
        
        # Save
        if output_path.lower().endswith(('.jpg', '.jpeg')):
            image.save(output_path, 'JPEG', quality=quality, optimize=True)
        else:
            image.save(output_path)
        
        print(f'✅ Image with logo watermark processed successfully!')
        print(f'📁 Saved to: {output_path}')
        
        return {'success': True, 'output_path': output_path}
        
    except Exception as error:
        print(f'❌ Error processing image: {error}')
        return {'success': False, 'error': str(error)}

# Main execution
if __name__ == "__main__":
    # Example usage - adjust these paths as needed
    input_image = IN_1  # This should be defined in your environment
    output_image = OUT_IMAGE.PNG  # This should be defined in your environment
    watermark_text = '© Your Brand 2024'
    
    # Process with text watermark
    result = resize_and_watermark(
        input_image,
        output_image,
        watermark_text,
        {
            'width': 800,
            'quality': 85,
            'watermark_position': 'bottom-right',
            'watermark_opacity': 180,  # 0-255
            'watermark_color': 'white',
            'font_size': 32,
            'margin': 15
        }
    )
    
    print("Result:", result)