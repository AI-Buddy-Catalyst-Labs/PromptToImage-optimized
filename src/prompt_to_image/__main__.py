#!/usr/bin/env python3
"""Text-to-Image Converter CLI Tool."""

import sys
import os
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import pymupdf

MARGIN = 2
SPACING = 2
TEXT_OFFSET = 1
BG_COLOR = "#FFFFFF"
TEXT_COLOR = "#000000"
VALID_EXTENSIONS = [".md", ".txt", ".pdf"]
DEFAULT_FONT_SIZE = 14
DEFAULT_IMAGE_WIDTH = 500


def print_error(message: str | None) -> None:
    """Print error message to stderr."""
    if message:
        print(f"Error: {message}", file=sys.stderr)


def validate_file_path(file_path: str) -> tuple[bool, str | None]:
    """Validate that the input file exists, is readable, and has a valid extension."""
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"

    if not os.path.isfile(file_path):
        return False, f"Path is not a file: {file_path}"

    if not os.access(file_path, os.R_OK):
        return False, f"File is not readable: {file_path}"

    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext not in VALID_EXTENSIONS:
        return (
            False,
            f"Invalid file type: {file_ext}. Only .md, .txt, and .pdf files are supported.",
        )

    return True, None


def get_input_file() -> str:
    """Prompt user for input file path with validation and graceful exit options."""
    while True:
        try:
            file_path = input(
                "\nEnter a valid .md, .txt, or .pdf file (or 'quit' to exit): "
            ).strip()

            if file_path.lower() in ("quit", "exit", "q"):
                print("Operation cancelled by user.")
                sys.exit(0)

            if not file_path:
                print("Error: File path cannot be empty. Please try again.")
                continue

            is_valid, error_msg = validate_file_path(file_path)
            if is_valid:
                return file_path
            else:
                print_error(error_msg)
                print("Please try again.\n")

        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            sys.exit(0)


def read_text_file(file_path: str) -> list[str]:
    """Read text file and filter out empty lines."""

    def read_with_encoding(encoding: str) -> list[str]:
        with open(file_path, "r", encoding=encoding) as f:
            return [line.rstrip("\n") for line in f if line.strip()]

    try:
        return read_with_encoding("utf-8")
    except UnicodeDecodeError:
        try:
            return read_with_encoding("latin-1")
        except Exception as e:
            raise Exception(f"Failed to read file: {e}")


def get_numeric_input(
    prompt: str, min_value: int = 1, max_value: int | None = None
) -> int:
    """Get numeric input from user with validation."""
    while True:
        try:
            value = int(input(prompt))
            if value < min_value:
                print(f"Value must be at least {min_value}. Please try again.")
                continue
            if max_value is not None and value > max_value:
                print(f"Value must be at most {max_value}. Please try again.")
                continue
            return value
        except ValueError:
            print("Invalid input. Please enter a numeric value.")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            sys.exit(1)


def load_font_with_fallback(
    font_size: int,
) -> ImageFont.ImageFont:
    """Load Pillow default system font."""
    return ImageFont.load_default(size=font_size)


def wrap_text(
    lines: list[str],
    font: ImageFont.ImageFont,
    image_width: int,
    draw: ImageDraw.ImageDraw,
) -> list[str]:
    """Implement word wrapping algorithm for text that exceeds image width."""
    wrapped_lines: list[str] = []
    max_line_width = image_width - MARGIN

    for line in lines:
        words = line.split()
        if not words:
            continue

        current_line = words[0]

        if draw.textlength(current_line, font=font) > max_line_width:
            wrapped_lines.append(current_line)
            current_line = ""
        else:
            for word in words[1:]:
                test_line = current_line + " " + word
                if draw.textlength(test_line, font=font) <= max_line_width:
                    current_line = test_line
                else:
                    wrapped_lines.append(current_line)
                    current_line = word

            if current_line:
                wrapped_lines.append(current_line)

    return wrapped_lines


def calculate_image_dimensions(
    wrapped_lines: list[str],
    font: ImageFont.ImageFont,
    draw: ImageDraw.ImageDraw,
) -> tuple[int, int]:
    """Calculate image dimensions using multiline_textbbox()."""
    if not wrapped_lines:
        return (50 + MARGIN, 50 + MARGIN)

    text = "\n".join(wrapped_lines)
    bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=SPACING)

    return (math.ceil(bbox[2] - bbox[0]) + MARGIN, math.ceil(bbox[3] + MARGIN))


def create_text_image(
    wrapped_lines: list[str],
    font: ImageFont.ImageFont,
    image_width: int,
    image_height: int,
) -> Image.Image:
    """Create image with white background and render text."""
    image = Image.new("RGB", (image_width, image_height), color=BG_COLOR)
    draw = ImageDraw.Draw(image)

    text = "\n".join(wrapped_lines)
    draw.multiline_text(
        (TEXT_OFFSET, TEXT_OFFSET), text, font=font, fill=TEXT_COLOR, spacing=SPACING
    )

    return image


def save_image(image: Image.Image, output_path: str) -> None:
    """Save image to file with error handling."""
    try:
        image.save(output_path, "PNG")
    except PermissionError:
        raise Exception(f"Permission denied: Cannot write to {output_path}")
    except Exception as e:
        raise Exception(f"Failed to save image: {e}")


def render_pdf_pages(file_path: str, max_width: int, output_folder: str) -> None:
    """Render each PDF page as PNG, resizing to max_width if needed. Scaling preserves aspect ratio - no content is cropped."""
    os.makedirs(output_folder, exist_ok=True)
    doc = pymupdf.open(file_path)
    page_count = len(doc)

    print(f"Found {page_count} page(s) in PDF.")

    for page in doc:
        page_width = page.rect.width
        zoom = min(1.0, max_width / page_width)

        mat = pymupdf.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        output_path = os.path.join(output_folder, f"page_{page.number + 1}.png")
        pix.save(output_path)

    doc.close()


def main() -> None:
    """Main entry point for the CLI tool."""
    if len(sys.argv) >= 2:
        input_file = sys.argv[1]
        is_valid, error_msg = validate_file_path(input_file)
        if not is_valid:
            print_error(error_msg)
            sys.exit(1)
        print("Converting text/markdown/PDF files to PNG images.")
    else:
        input_file = get_input_file()

    if len(sys.argv) >= 4:
        try:
            font_size = int(sys.argv[2])
            image_width = int(sys.argv[3])
            if font_size < 8 or font_size > 200:
                print_error("Font size must be between 8 and 200 pixels.")
                sys.exit(1)
            if image_width < 50 or image_width > 10000:
                print_error("Image width must be between 50 and 10000 pixels.")
                sys.exit(1)
            print(f"Using font size: {font_size}px, max width: {image_width}px")
        except ValueError:
            print_error("Font size and image width must be numeric values.")
            sys.exit(1)
    elif len(sys.argv) == 2:
        font_size = DEFAULT_FONT_SIZE
        image_width = DEFAULT_IMAGE_WIDTH
        print(f"Using defaults: font size={font_size}px, max width={image_width}px")
    else:
        font_size = get_numeric_input(
            "Enter font size (pixels): ", min_value=8, max_value=200
        )
        image_width = get_numeric_input(
            "Enter max image width (pixels): ", min_value=50, max_value=10000
        )

    if len(sys.argv) >= 5:
        output_file = sys.argv[4]
        if not output_file.lower().endswith(".png"):
            output_file += ".png"
    else:
        output_file = os.path.splitext(input_file)[0] + ".png"

    file_ext = os.path.splitext(input_file)[1].lower()

    if file_ext == ".pdf":
        output_folder = os.path.splitext(output_file)[0]
        print(f"\nProcessing: {input_file}")
        print(f"Using max width: {image_width}px")
        try:
            render_pdf_pages(input_file, image_width, output_folder)
            print(f"\nSuccess! Pages saved to: {output_folder}/")
        except Exception as e:
            print_error(str(e))
            sys.exit(1)
        sys.exit(0)

    try:
        lines = read_text_file(input_file)
    except Exception as e:
        print_error(str(e))
        sys.exit(1)

    if not lines:
        print_error("File is empty or contains only whitespace.")
        sys.exit(1)

    print(f"\nProcessing: {input_file}")
    print(f"Found {len(lines)} non-empty lines.")

    font = load_font_with_fallback(font_size)

    measure_image = Image.new("RGB", (1, 1))
    measure_draw = ImageDraw.Draw(measure_image)

    wrapped_lines = wrap_text(lines, font, image_width, measure_draw)

    if not wrapped_lines:
        print_error("No text to render after processing.")
        sys.exit(1)

    image_width, image_height = calculate_image_dimensions(
        wrapped_lines, font, measure_draw
    )

    print(f"Image dimensions: {image_width}x{image_height} pixels")
    print(f"Rendering {len(wrapped_lines)} lines...")

    try:
        image = create_text_image(wrapped_lines, font, image_width, image_height)
        save_image(image, output_file)
        print(f"\nSuccess! Image saved to: {output_file}")
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
