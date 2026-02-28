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
BG_COLOR = "#FFFFFF"
TEXT_COLOR = "#000000"
VALID_EXTENSIONS = [".md", ".txt", ".pdf"]
DEFAULT_FONT_SIZE = 14
DEFAULT_IMAGE_WIDTH = 500
MAX_HEIGHT_RATIO = 2.5
MIN_CHUNK_RATIO = 0.05


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
) -> tuple[int, int, tuple[float, float, float, float]]:
    """Calculate image dimensions using multiline_textbbox()."""
    if not wrapped_lines:
        return (50 + MARGIN * 2, 50 + MARGIN * 2, (0, 0, 0, 0))

    text = "\n".join(wrapped_lines)
    bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=SPACING)

    width = math.ceil(bbox[2] - bbox[0] + 2 * MARGIN)
    height = math.ceil(bbox[3] - bbox[1] + 2 * MARGIN)

    return (width, height, bbox)


def create_text_image(
    wrapped_lines: list[str],
    font: ImageFont.ImageFont,
    image_width: int,
    image_height: int,
    text_bbox: tuple[float, float, float, float],
) -> Image.Image:
    """Create image with white background and render text."""
    image = Image.new("RGB", (image_width, image_height), color=BG_COLOR)
    draw = ImageDraw.Draw(image)

    text = "\n".join(wrapped_lines)
    text_x = MARGIN - text_bbox[0]
    text_y = MARGIN - text_bbox[1]
    draw.multiline_text(
        (text_x, text_y), text, font=font, fill=TEXT_COLOR, spacing=SPACING
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


def calculate_optimal_lines_per_slice(
    wrapped_lines: list[str],
    font: ImageFont.ImageFont,
    draw: ImageDraw.ImageDraw,
    max_height: int,
) -> int:
    """Find maximum lines that fit within max_height via iterative testing."""
    if not wrapped_lines:
        return 0

    total_lines = len(wrapped_lines)
    test_lines = min(total_lines, 100)

    while test_lines <= total_lines:
        test_text = "\n".join(wrapped_lines[:test_lines])
        bbox = draw.multiline_textbbox((0, 0), test_text, font=font, spacing=SPACING)
        height = math.ceil(bbox[3] - bbox[1] + 2 * MARGIN)

        if height <= max_height:
            if test_lines == total_lines:
                return test_lines
            test_lines += 10
        else:
            while test_lines > 0:
                test_text = "\n".join(wrapped_lines[:test_lines])
                bbox = draw.multiline_textbbox(
                    (0, 0), test_text, font=font, spacing=SPACING
                )
                height = math.ceil(bbox[3] - bbox[1] + 2 * MARGIN)

                if height <= max_height:
                    return test_lines
                test_lines -= 1
            return test_lines

    return total_lines


def split_lines_into_chunks(
    wrapped_lines: list[str],
    font: ImageFont.ImageFont,
    draw: ImageDraw.ImageDraw,
    max_width: int,
    max_height: int,
) -> list[list[str]]:
    """Greedy packing of lines into chunks that fit within max_height."""
    if not wrapped_lines:
        return []

    max_lines = calculate_optimal_lines_per_slice(wrapped_lines, font, draw, max_height)
    chunks: list[list[str]] = []
    remaining_lines = wrapped_lines[:]

    while remaining_lines:
        candidate_size = min(max_lines, len(remaining_lines))
        chunk = remaining_lines[:candidate_size]

        chunk_width, chunk_height, chunk_bbox = calculate_image_dimensions(
            chunk, font, draw
        )

        while chunk_height > max_height and len(chunk) > 1:
            candidate_size -= 1
            chunk = remaining_lines[:candidate_size]
            chunk_width, chunk_height, chunk_bbox = calculate_image_dimensions(
                chunk, font, draw
            )

        chunks.append(chunk)
        remaining_lines = remaining_lines[len(chunk) :]

    if len(chunks) > 1:
        last_chunk_width, last_chunk_height, last_chunk_bbox = (
            calculate_image_dimensions(chunks[-1], font, draw)
        )

        if last_chunk_height < max_height * MIN_CHUNK_RATIO:
            chunks[-2].extend(chunks[-1])
            chunks.pop()

    return chunks


def generate_output_paths(
    output_file: str,
    num_images: int,
) -> list[str]:
    """Generate output paths for single or multiple images."""
    if num_images == 1:
        return [output_file]

    base_name = output_file
    if base_name.lower().endswith(".png"):
        base_name = base_name[:-4]

    return [f"{base_name}_part_{i}.png" for i in range(1, num_images + 1)]


def build_chunk_with_navigation(
    chunk_lines: list[str],
    chunk_index: int,
    total_chunks: int,
    output_paths: list[str],
) -> list[str]:
    """Add navigation lines to chunk: top from previous, bottom to next."""
    augmented = chunk_lines.copy()

    if chunk_index > 1:
        prev_file = os.path.basename(output_paths[chunk_index - 2])
        augmented.insert(0, f"[continued from {prev_file}]")

    if chunk_index < total_chunks:
        next_file = os.path.basename(output_paths[chunk_index])
        augmented.append(f"[continue to {next_file}]")

    return augmented


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

    image_width, image_height, text_bbox = calculate_image_dimensions(
        wrapped_lines, font, measure_draw
    )

    print(f"Image dimensions: {image_width}x{image_height} pixels")
    print(f"Rendering {len(wrapped_lines)} lines...")

    max_height = int(image_width * MAX_HEIGHT_RATIO)

    try:
        if image_height <= max_height:
            image = create_text_image(
                wrapped_lines, font, image_width, image_height, text_bbox
            )
            save_image(image, output_file)
            print(f"\nSuccess! Image saved to: {output_file}")
        else:
            print(
                f"Image too tall ({image_height}px). Splitting into multiple images..."
            )

            line_chunks = split_lines_into_chunks(
                wrapped_lines, font, measure_draw, image_width, max_height
            )
            output_paths = generate_output_paths(output_file, len(line_chunks))

            for i, chunk in enumerate(line_chunks, 1):
                chunk_with_nav = build_chunk_with_navigation(
                    chunk, i, len(line_chunks), output_paths
                )
                chunk_width, chunk_height, chunk_bbox = calculate_image_dimensions(
                    chunk_with_nav, font, measure_draw
                )
                chunk_image = create_text_image(
                    chunk_with_nav, font, chunk_width, chunk_height, chunk_bbox
                )
                save_image(chunk_image, output_paths[i - 1])
                print(
                    f"Saved part {i}/{len(line_chunks)}: {output_paths[i - 1]} ({chunk_width}x{chunk_height})"
                )

            print(f"\nSuccess! {len(line_chunks)} images saved.")
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
