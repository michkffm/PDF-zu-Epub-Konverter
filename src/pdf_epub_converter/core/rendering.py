"""Bounded PDF rasterization isolated from the GUI and its worker thread."""

import subprocess
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image


def render_page(pdf_path, index, dpi=150, crop=None, check_cancel=None):
    """Return an owned image; kill the renderer on cancellation or after 30 seconds."""
    check_cancel = check_cancel or (lambda: None)
    check_cancel()
    if not 72 <= dpi <= 300 or index < 0:
        raise ValueError("Invalid render resolution or page number")
    with TemporaryDirectory(prefix="pdf-epub-render-") as temporary:
        output = Path(temporary) / "page.png"
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            str(pdf_path),
            str(index),
            str(dpi),
            str(output),
        ]
        if crop is not None:
            command.extend(str(value) for value in crop)
        process = subprocess.Popen(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
        )
        deadline = time.monotonic() + 30
        try:
            while True:
                check_cancel()
                if time.monotonic() >= deadline:
                    raise TimeoutError("PDF rendering exceeded the 30 second limit")
                try:
                    _, error = process.communicate(timeout=0.1)
                    break
                except subprocess.TimeoutExpired:
                    continue
            if process.returncode:
                # Child errors contain only controlled diagnostic messages.
                raise ValueError(
                    error.decode(errors="replace").strip() or "PDF rendering failed"
                )
            check_cancel()
            with Image.open(output) as image:
                if image.width * image.height > 16_000_000:
                    raise ValueError("Page exceeds the 16 megapixel rendering limit")
                return image.copy()
        finally:
            if process.poll() is None:
                process.kill()
            process.communicate()


def _render_child():
    import math
    import pdfplumber

    pdf_path, index, dpi, output, *coordinates = sys.argv[1:]
    index, dpi = int(index), int(dpi)
    if not 72 <= dpi <= 300:
        raise ValueError("Invalid rendering resolution")
    if Path(pdf_path).stat().st_size > 100 * 1024 * 1024:
        raise ValueError("PDF exceeds the 100 MiB limit")
    with pdfplumber.open(pdf_path) as pdf:
        if not 0 <= index < len(pdf.pages) <= 500:
            raise ValueError("Invalid page range or more than 500 pages")
        page = pdf.pages[index]
        if page.width * page.height * (dpi / 72) ** 2 > 16_000_000:
            raise ValueError("Page exceeds the 16 megapixel rendering limit")
        if coordinates:
            box = tuple(float(value) for value in coordinates)
            if len(box) != 4 or not all(math.isfinite(value) for value in box):
                raise ValueError("Invalid crop bounds")
            page = page.crop(box)
        pixels = math.ceil(page.width * dpi / 72) * math.ceil(page.height * dpi / 72)
        if pixels <= 0 or pixels > 16_000_000:
            raise ValueError("Page exceeds the 16 megapixel rendering limit")
        image = page.to_image(resolution=dpi).original
        try:
            image.save(output, "PNG")
        finally:
            image.close()


if __name__ == "__main__":
    try:
        _render_child()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
