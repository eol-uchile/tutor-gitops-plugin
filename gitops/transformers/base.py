from abc import ABC, abstractmethod
from typing import List
from ..config import GitOpsConfig

class ManifestTransformer(ABC):

    def __init__(self, config: GitOpsConfig):
        self.config = config

    @abstractmethod
    def should_apply(self, path: str) -> bool:
        """True si este transformador debe procesar el archivo."""

    @abstractmethod
    def transform(self, docs: List[dict]) -> List[dict]:
        """Transforma los docs YAML y retorna la lista modificada."""

    @property
    def name(self) -> str:
        return self.__class__.__name__
