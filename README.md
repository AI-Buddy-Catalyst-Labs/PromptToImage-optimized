# PromptToImage

A Python CLI tool that converts text and markdown files into PNG images. Inspired by the DeepSeek OCR paper, this tool leverages vision tokens—which hold more context per token than text tokens—as a context engineering technique.

## About

PromptToImage transforms your text content into visual representations, enabling efficient context compression through vision tokens. This is particularly useful for:
- Preparing long prompts for vision-language models
- Reducing token count while preserving context
- Converting documentation into image format for multimodal AI workflows

**Font:** Uses Pillow's default system font for text rendering.

## Installation

### For Developers

Install in editable mode (changes take effect immediately):

```bash
cd prompt-to-image
pip install -e .
```

### For End Users

Choose one of the following methods:

**Option 1: Install from Git repository**

```bash
pip install git+https://github.com/AI-Buddy-Catalyst-Labs/PromptToImage-optimized.git
```

**Option 2: Install from local directory**

clone the repository then install:
```bash
pip install /path/to/prompt-to-image
```

**Option 3: Install from built wheel**
clone the repository, build the wheel, then install:
```bash
# First build the wheel (run by package maintainer)
python -m build

# Then install from the wheel
pip install dist/prompt_to_image-1.0.0-py3-none-any.whl
```

**Requirements:**
- Python 3.8 or higher
- Pillow >= 12.0.0
- Pillow library for image generation

## Usage

After installation, the `prompt-to-image` command is available from anywhere in your terminal.

### Command-Line Mode

```bash
prompt-to-image <input_file.md|txt> [font_size] [image_width] [output_file]
```

**Parameters:**
- `input_file`: Path to .md or .txt file (required)
- `font_size`: Font size in pixels, 8-200 (default: 14)
- `image_width`: Max image width in pixels, 50-10000 (default: 500)
- `output_file`: Output filename (default: `<input_filename>.png`)

**Examples:**

```bash
# Convert with defaults (14px font, 500px width)
prompt-to-image document.md

# Convert with custom font size and image width
prompt-to-image notes.txt 14 800

# Convert with custom output filename
prompt-to-image readme.md 14 1000 output.png
```

### Interactive Mode

Run without arguments for interactive prompts:

```bash
prompt-to-image
```

You will be prompted for:
1. Input file path (or type `quit` to exit)
2. Font size (8-200 pixels)
3. Max image width (50-10000 pixels)

## Example

**Input (`sample.md`):**
```markdown
# Context Engineering with Vision Tokens

Vision tokens represent a powerful technique for context compression.
By encoding text as images, we can leverage the higher information
density of visual representations in multimodal models.
```

**Command:**
```bash
prompt-to-image sample.md 12 800
```

**Output:** `sample.png` - A formatted PNG image with wrapped text, ready for use with vision-language models.

## Updating

To update to the latest version, follow the same installation method you originally used:

### If installed from Git repository:

```bash
# Reinstall from the latest version
pip install --upgrade --force-reinstall git+https://github.com/AI-Buddy-Catalyst-Labs/PromptToImage-optimized.git

# Or install specific version/tag
pip install --upgrade --force-reinstall git+https://github.com/AI-Buddy-Catalyst-Labs/PromptToImage-optimized.git@v1.0.0
```

### If installed from local directory or wheel:

```bash
# First uninstall the current version
pip uninstall prompt-to-image

# Then pull the latest code and reinstall
pip install /path/to/prompt-to-image

# Or install the new wheel
pip install dist/prompt_to_image-1.0.0-py3-none-any.whl
```

### Check installed version:

```bash
pip show prompt-to-image
```

## Features

- **Multiple Input Formats:** Supports both `.md` and `.txt` files
- **Customizable Rendering:** Adjustable font size (8-200px) and image width (50-10000px)
- **Smart Word Wrapping:** Automatically wraps text to fit specified dimensions
- **Empty Line Removal:** Removes empty lines to reduce whitespace in the output image
- **Encoding Support:** UTF-8 with Latin-1 fallback for broad compatibility
- **Font Handling:** Uses Pillow default system font
- **Dual Modes:** Both command-line and interactive interfaces
- **Error Handling:** Comprehensive validation and graceful error messages

## Architecture

- **src/prompt_to_image/__main__.py**: Main CLI entry point
- **src/prompt_to_image/**: Main package directory
- **pyproject.toml**: Package configuration
- Uses modern Pillow APIs (12.0.0+) for accurate text measurement

## Development

To build a distribution wheel:

```bash
pip install build
python -m build
```

The wheel will be created in `dist/` directory.

To uninstall:

```bash
pip uninstall prompt-to-image
```

## License

MIT License - feel free to use and modify for your projects.
