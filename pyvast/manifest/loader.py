
from pathlib import Path
import yaml
from .types import ManifestModel

def _load(src):
    if isinstance(src, dict):
        return src
    text = Path(src).read_text() if isinstance(src, Path) else src
    return yaml.safe_load(text)

class ManifestLoader:
    def __init__(self, source):
        self.model = ManifestModel(**_load(source))
