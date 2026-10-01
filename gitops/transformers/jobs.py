from typing import List
from ..utils import get_pod_spec, path_matches
from .base import ManifestTransformer

_MANIFEST_SUFFIXES = (
    "jobs.yml", "jobs.yaml",
)

class JobTransformer(ManifestTransformer):
    """elimina jobs innecesarios y sobreescribe comandos definidos en config"""

    def should_apply(self, path: str) -> bool:
        return path_matches(path, *_MANIFEST_SUFFIXES)

    def transform(self, docs: List[dict]) -> List[dict]:
        result = []
        for doc in docs:
            kind = doc.get("kind")

            if kind == "Job":
                job_name = doc.get("metadata", {}).get("name")
                if getattr(self.config, "jobs_to_delete", []) and job_name in self.config.jobs_to_delete:
                    continue

                pod_spec = get_pod_spec(doc)
                if pod_spec:
                    self._override_job_commands(doc, pod_spec)

            result.append(doc)
        return result


    def _override_job_commands(self, doc: dict, pod_spec: dict) -> None:
        """sobreescribe comandos de jobs definidos en config (dockerize, settings de prod, etc)"""
        job_name = doc.get("metadata", {}).get("name")
        job_config = self.config.job_commands.get(job_name)
        if not job_config:
            return

        target_container = job_config.get("container")
        for container in pod_spec.get("containers", []):
            if container.get("name") != target_container:
                continue

            if "command" in job_config:
                container["command"] = job_config["command"]
            if "args" in job_config:
                container["args"] = job_config["args"]
