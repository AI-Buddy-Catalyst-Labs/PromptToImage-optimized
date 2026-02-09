# Agent Guidelines for PromptToImage

This is a Python CLI tool that converts text/markdown files to PNG images using Pillow.
## Project Structure

- `text_to_image.py` - Main CLI entry point with all core functions
- `requirements.txt` - Python dependencies
- `fonts/` - Directory for optional Book Antiqua font (user-provided)
  - `fonts/bookantiqua.ttf` - Optional font file for improved OCR accuracy

## Build/Install/Run Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the tool
python text_to_image.py <input_file.md|txt> [font_size] [image_width] [output_file]
```

## User Flow

**1. Command-line Mode** (with arguments)
```bash
python text_to_image.py <file.md|txt> [font_size] [image_width] [output_file]
```
- Validates file path from argv[1]
- Skips interactive prompts
- Uses provided font_size and image_width (or prompts if missing)
- Optional output_file: defaults to `<input_filename>.png` if not provided
- Auto-adds `.png` extension if output_file is provided without extension

**2. Interactive Mode** (no arguments)
```bash
python text_to_image.py
```
- **Step 1:** Prompts for input file path (loops until valid file or 'quit')
- **Step 2:** Prompts for font size (8-200px)
- **Step 3:** Prompts for max image width (50-10000px)
- **Step 4:** Generates PNG image with word wrapping
- **Step 5:** Saves as `<input_filename>.png`

### Exit Options
- Type `quit`, `exit`, or `q` at file prompt
- `Ctrl+C` at any prompt
- Validation errors exit with code 1

## Code Style Guidelines

### Naming Conventions

- **Functions/Variables**: `snake_case` (e.g., `print_error`, `wrapped_lines`)
- **Constants**: `UPPER_SNAKE_CASE`
- **Private functions**: Prefix with underscore if internal-only

### Type Hints

- New functions SHOULD include type annotations: `def foo(x: int) -> bool:`

### Docstrings

- Use triple-quoted docstrings for all functions
- Keep docstrings concise but descriptive (one line is typical)
- Format: `"""Verb object description."""`

### Error Handling

- Use `try/except` blocks for I/O operations
- Return `(True, None)` or `(False, error_msg)` for validation functions
- Raise `Exception` with descriptive messages for unrecoverable errors
- Print errors to `stderr` via `sys.stderr`
- Exit with `sys.exit(1)` on fatal errors
- Handle specific exceptions: `PermissionError`, `UnicodeDecodeError`, `OSError`, `IOError`, `ValueError`, `KeyboardInterrupt`

### Constants and Magic Numbers

- Define constants at module level
- Magic numbers like `margin = 2`, `spacing = 2` should be extracted as constants
- Hardcoded values like `'#FFFFFF'`, `'#000000'` are already defined as module constants

### CLI Patterns

- Use `sys.argv` for comprehensive CLI argument handling
- Validate file paths before processing
- Provide usage message on incorrect invocation
- Use `sys.exit(1)` for errors, no explicit success exit (implicit 0)

### Function Design

- Keep functions small and single-purpose
- Prefer pure functions where possible (no side effects)
- Use return values instead of printing in helper functions
- Separate I/O from business logic

### Code Formatting

- 4-space indentation (Python standard)
- No trailing whitespace
- Line length: Not strictly enforced, but keep reasonable
- Blank line between functions (2 blank lines at module level per PEP 8)

### Shebang and Encoding

- Use `#!/usr/bin/env python3` at top of executable scripts
- Specify `encoding='utf-8'` when opening files
- Fallback to `encoding='latin-1'` if UTF-8 fails

### Testing

- Use print statements for manual testing
- Ask user for input to test interactive functions

## Common Patterns

### Font Loading with Fallback
```python
# Tier 1: Try project fonts/bookantiqua.ttf
if FONT_FILE.exists():
    try:
        font = ImageFont.truetype(str(FONT_FILE), font_size)
        return font
    except (OSError, IOError):
        pass

# Tier 2: Try OS-installed Book Antiqua (cross-platform)
book_antiqua_names = [
    "Book Antiqua",
    "BookAntiqua",
    "Book Antiqua Regular",
    "BkAntiqua",
]

for font_name in book_antiqua_names:
    try:
        font = ImageFont.truetype(font_name, font_size)
        return font
    except OSError:
        continue

# Tier 3: Fall back to Pillow default
print("Warning: Using Pillow default font (Book Antiqua not found in project or system)", file=sys.stderr)
font = ImageFont.load_default(size=font_size)
```

### Text Measurement (Modern Pillow APIs)
```python
# Get single line text length
line_length = draw.textlength(line, font=font)

# Get bounding box for multiline text
bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=spacing)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
```

### File Validation
```python
if not os.path.exists(file_path):
    return False, f"File not found: {file_path}"
```

## Dependencies

- `Pillow>=12.0.0` - Image generation and text rendering

### Pillow Version Notes

- `ImageFont.load_default(size=N)` requires Pillow >= 10.1.0
- Always use modern APIs: `textlength()`, `multiline_textbbox()` instead of deprecated `textsize()`, `multiline_textsize()`

## implementation notes

- Before implementation, validate using context7
- Seek validation from user for your assumptions