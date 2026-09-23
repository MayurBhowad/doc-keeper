import json
from pathlib import Path

from document_reader.domain.content import DocumentContent


class JsonStorage:

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save(self, content: DocumentContent) -> Path:
        output_path = (self.output_dir / f"{Path(content.filename).stem}.json")
        data = {
            "filename": content.filename,
            "type": content.document_type,
            "content": content.text,
        }
        output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return output_path