from typing import List
from ..utils import path_matches
from .base import ManifestTransformer

_MANIFEST_SUFFIXES = ("deployments.yml", "deployments.yaml", "services.yml", "services.yaml", "volumes.yml", "volumes.yaml")

class DeploymentTransformer(ManifestTransformer):
    """elimina deployments y services innecesarios configurados"""

    def should_apply(self, path: str) -> bool:
        return path_matches(path, *_MANIFEST_SUFFIXES)

    def transform(self, docs: List[dict]) -> List[dict]:
        result = []
        for doc in docs:
            kind = doc.get("kind")
            if kind in ("Deployment", "Service", "PersistentVolumeClaim"):
                name = doc.get("metadata", {}).get("name")
                if getattr(self.config, "deployments_to_delete", []) and name in self.config.deployments_to_delete:
                    continue
            result.append(doc)
        return result
