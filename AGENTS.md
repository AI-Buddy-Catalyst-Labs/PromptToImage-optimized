# Agent Guidelines for PromptToImage

This is a Python CLI tool that converts text/markdown/PDF files to PNG images using Pillow and PyMuPDF.
## Project Structure

- `src/prompt_to_image/__main__.py` - Main CLI entry point
- `src/prompt_to_image/__init__.py` - Package init
- `pyproject.toml` - Package configuration
- `requirements.txt` - Development dependencies

## Build/Install/Run Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Install as package (editable mode)
pip install -e .

# Run via Python module
python -m prompt_to_image <input_file.md|txt|pdf> [font_size] [image_width] [output_file]

# Run via CLI commands (after pip install -e .)
prompt-to-image <input_file.md|txt|pdf> [font_size] [image_width] [output_file]
ptoi <input_file.md|txt|pdf> [font_size] [image_width] [output_file]
p2i <input_file.md|txt|pdf> [font_size] [image_width] [output_file]
```

## User Flow

**1. Command-line Mode** (with arguments)
```bash
python -m prompt_to_image <file.md|txt|pdf> [font_size] [image_width] [output_file]
```
- Validates file path from argv[1]
- Skips interactive prompts
- Uses provided font_size and image_width (or prompts if missing)
- Optional output_file: defaults to `<input_filename>.png` if not provided
- Auto-adds `.png` extension if output_file is provided without extension
- **PDF files**: Renders each page as separate PNG in a folder named after input file

**2. Interactive Mode** (no arguments)
```bash
python -m prompt_to_image
```
- **Step 1:** Prompts for input file path (loops until valid file or 'quit')
- **Step 2:** Prompts for font size (8-200px)
- **Step 3:** Prompts for max image width (50-10000px)
- **Step 4:** Generates PNG image(s) with word wrapping (or folder of PNGs for PDF)
- **Step 5:** Saves as `<input_filename>.png` (or `<input_filename>/` folder for PDFs)
  - **Long images** (>2.5x width): Splits into multiple images named `<name>_part_1.png`, `<name>_part_2.png`, etc.
  - Splitting never occurs mid-line; uses greedy packing to maximize content per image

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
- Image splitting: `MAX_HEIGHT_RATIO = 2.5`, `MIN_CHUNK_RATIO = 0.05`

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

### Font Loading
```python
def load_font_with_fallback(font_size: int) -> ImageFont.ImageFont:
    """Load Pillow default system font."""
    return ImageFont.load_default(size=font_size)
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

## Image Splitting Behavior

**When Splitting Occurs:**
- Image height exceeds `MAX_HEIGHT_RATIO * image_width` (default: 2.5x width)
- Only applies to `.txt` and `.md` files (PDFs already split by pages)

**Splitting Algorithm:**
1. Calculate total image dimensions normally
2. If exceeding threshold, determine optimal lines per slice via iterative testing
3. Use greedy packing to fill each chunk to maximum capacity
4. Merge tiny final chunks (< 5% of max_height) with previous chunk
5. Each chunk is saved as separate PNG file

**Output Naming:**
- Single image: `output.png`
- Multiple images: `output_part_1.png`, `output_part_2.png`, etc.
- If user provides `custom.png`, becomes `custom_part_1.png`, `custom_part_2.png`

**Key Functions:**
- `calculate_optimal_lines_per_slice()` - Finds max lines fitting in max_height
- `split_lines_into_chunks()` - Greedy packing with small chunk merging
- `generate_output_paths()` - Handles single vs multiple file naming

## Dependencies

- `Pillow>=12.0.0` - Image generation and text rendering
- `pymupdf>=1.23.0` - PDF rendering to PNG images

### Pillow Version Notes

- `ImageFont.load_default(size=N)` requires Pillow >= 10.1.0
- Always use modern APIs: `textlength()`, `multiline_textbbox()` instead of deprecated `textsize()`, `multiline_textsize()`

## implementation notes

- Before implementation, validate using context7
- Seek validation from user for your assumptions