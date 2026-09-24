import json
from pathlib import Path

from document_reader.domain.content import DocumentContent
from document_reader.domain.extraction import ExtractionResult


class JsonStorage:

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save(self, filename: str, result: ExtractionResult) -> Path:
        output_path = (self.output_dir / f"{Path(filename).stem}.json")
        data = {
            "filename": filename,
            "data": result.data,
        }
        output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return output_path