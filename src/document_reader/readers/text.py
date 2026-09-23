from document_reader.domain.content import DocumentContent
from document_reader.domain.document import Document
from document_reader.readers.base import DocumentReader


class TextReader(DocumentReader):

    def read(self, document: Document) -> DocumentContent:
        if not document.path.exists():
            raise FileNotFoundError(f"Document file not found: {document.path}")
        
        text = document.path.read_text(encoding="utf-8")

        return DocumentContent(filename=document.filename, document_type="text", text=text)