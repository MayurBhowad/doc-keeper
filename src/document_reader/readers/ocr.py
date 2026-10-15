import importlib.util
import shutil

import fitz


class TesseractOCR:
    """Recognize text from a PDF page using Tesseract OCR."""

    def __call__(self, page: fitz.Page) -> str:
        if importlib.util.find_spec("pytesseract") is None:
            raise RuntimeError(
                "OCR requires the optional 'pytesseract' package. "
                "Install it with: pip install pytesseract"
            )

        if importlib.util.find_spec("PIL") is None:
            raise RuntimeError(
                "OCR requires Pillow. Install it with: pip install Pillow"
            )

        if shutil.which("tesseract") is None:
            raise RuntimeError(
                "OCR requires the Tesseract executable. "
                "On Ubuntu, install it with: sudo apt install tesseract-ocr"
            )

        import pytesseract
        from PIL import Image

        pixmap = page.get_pixmap(dpi=200, alpha=False)
        image = Image.frombytes(
            "RGB",
            (pixmap.width, pixmap.height),
            pixmap.samples,
        )
        return pytesseract.image_to_string(image)
