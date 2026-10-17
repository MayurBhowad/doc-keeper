
from collections.abc import Callable

import fitz

from document_reader.domain.content import DocumentContent
from document_reader.domain.document import Document
from document_reader.readers.base import DocumentReader

OCRCallable = Callable[[fitz.Page], str]


class PDFReader(DocumentReader):
    def __init__(
        self,
        ocr: OCRCallable | None = None,
        min_text_chars: int = 1,
    ):
        if min_text_chars < 1:
            raise ValueError("min_text_chars must be at least 1")

        self.ocr = ocr
        self.min_text_chars = min_text_chars

    def read(self, document: Document) -> DocumentContent:
        if not document.path.exists():
            raise FileNotFoundError(
                f"Document file not found: {document.path}"
            )

        pages = []

        with fitz.open(document.path) as pdf:
            for page in pdf:
                text = page.get_text().strip()

                if len(text) < self.min_text_chars:
                    has_visual_content = bool(
                        page.get_images(full=True) or page.get_drawings()
                    )

                    if not text and not has_visual_content:
                        pages.append("")
                        continue

                    if self.ocr is None:
                        raise RuntimeError(
                            "This PDF page contains insufficient extractable "
                            "text. Configure an OCR implementation to process "
                            "scanned PDFs."
                        )

                    text = self.ocr(page).strip()

                pages.append(text)

        return DocumentContent(
            filename=document.filename,
            document_type="pdf",
            text="\n".join(pages),
            pages=tuple(pages),
        )
