from document_reader.readers.base import DocumentReader
from document_reader.readers.pdf import PDFReader
from document_reader.readers.text import TextReader


class ReaderRegistry:

    def __init__(self):
        self._readers: dict[str, DocumentReader] = {
            ".txt": TextReader(),
            ".pdf": PDFReader(),
        }

    def get(self, extension: str) -> DocumentReader:
        try:
            return self._readers[extension]
        except KeyError:
            raise ValueError(f"Unsupported document type: {extension}")