from abc import ABC, abstractmethod

from ..domain.content import DocumentContent
from ..domain.document import Document


class DocumentReader(ABC):
    @abstractmethod
    def read(self, document: Document) -> DocumentContent:
        pass