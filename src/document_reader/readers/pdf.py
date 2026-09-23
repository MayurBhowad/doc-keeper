import fitz


from document_reader.domain.content import DocumentContent
from document_reader.domain.document import Document
from document_reader.readers.base import DocumentReader


class PDFReader(DocumentReader):

    def read(self, document: Document) -> DocumentContent:
        if not document.path.exists():
            raise FileNotFoundError(f"Document file not found: {document.path}")

        pages = []

        with fitz.open(document.path) as pdf:
            for page in pdf:
                pages.append(page.get_text())

        return DocumentContent(filename=document.filename, document_type="pdf", text="\n".join(pages))