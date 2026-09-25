from typing import List
from ..utils import get_pod_spec, path_matches
from .base import ManifestTransformer

_MANIFEST_SUFFIXES = (
    "deployments.yml", "deployments.yaml",
    "jobs.yml", "jobs.yaml",
)

class SecretsTransformer(ManifestTransformer):
    """reemplaza env vars hardcodeados por secretKeyRef y configMaps por Secrets"""

    def should_apply(self, path: str) -> bool:
        return path_matches(path, *_MANIFEST_SUFFIXES)

    def transform(self, docs: List[dict]) -> List[dict]:
        for doc in docs:
            pod_spec = get_pod_spec(doc)
            if not pod_spec:
                continue
            self._replace_env_vars_with_secret_refs(pod_spec)
            self._convert_configmap_volumes_to_secrets(pod_spec)
        return docs

    def _replace_env_vars_with_secret_refs(self, pod_spec: dict) -> None:
        """reemplaza env vars en texto plano por referencias a deployment-secrets"""
        for container in pod_spec.get("containers", []):
            for env_var in container.get("env", []):
                mapping = self.config.env_var_secret_mapping.get(env_var.get("name"))
                if not mapping:
                    continue

                new_name = mapping.get("env_name")
                if new_name:
                    env_var["name"] = new_name

                env_var.pop("value", None)
                env_var["valueFrom"] = {
                    "secretKeyRef": {
                        "name": self.config.deployment_secret_name,
                        "key": mapping["secret_key"],
                    }
                }

    def _convert_configmap_volumes_to_secrets(self, pod_spec: dict) -> None:
        """cambia el montaje de configmaps sensibles para que monten Secrets en los pods"""
        for volume in pod_spec.get("volumes", []):
            cm = volume.get("configMap")
            if cm and cm.get("name") in self.config.sensitive_configmaps:
                cm_name = cm["name"]
                volume.pop("configMap", None)
                volume["secret"] = {"secretName": cm_name}
