from typing import List
from ..utils import LiteralString, path_matches
from .base import ManifestTransformer

class ArgoCDTransformer(ManifestTransformer):
    """configura hooks y sync waves de ArgoCD en jobs y deployments"""

    def should_apply(self, path: str) -> bool:
        return path_matches(path, "kustomization.yml", "kustomization.yaml")

    def transform(self, docs: List[dict]) -> List[dict]:
        for doc in docs:
            if "patches" not in doc:
                doc["patches"] = []

            self._add_job_hook_patch(doc)
            self._add_job_sync_wave_patches(doc)
            self._add_deployment_sync_wave_patches(doc)
        return docs

    def _add_job_hook_patch(self, doc: dict) -> None:
        """marca los jobs como Sync hooks con política de borrado post-éxito"""
        patch_str = (
            "apiVersion: batch/v1\n"
            "kind: Job\n"
            "metadata:\n"
            '  name: ".*"\n'
            "  annotations:\n"
            "    argocd.argoproj.io/hook: Sync\n"
            "    argocd.argoproj.io/hook-delete-policy: HookSucceeded,BeforeHookCreation\n"
            "spec:\n"
            "  backoffLimit: 3\n"
            "  ttlSecondsAfterFinished: 3600\n"
        )
        patch_obj = {
            "patch": LiteralString(patch_str),
            "target": {"kind": "Job"},
        }
        if patch_obj not in doc["patches"]:
            doc["patches"].append(patch_obj)

    def _add_job_sync_wave_patches(self, doc: dict) -> None:
        """asigna el orden de ejecución (sync wave) de cada job (minio -> lms -> cms)"""
        for job_name, wave in self.config.job_sync_waves.items():
            actual_name = getattr(self.config, "job_renames", {}).get(job_name, job_name)
            if getattr(self.config, "jobs_to_delete", []) and job_name in self.config.jobs_to_delete:
                continue
                
            patch_str = (
                "apiVersion: batch/v1\n"
                "kind: Job\n"
                "metadata:\n"
                f'  name: "{actual_name}"\n'
                "  annotations:\n"
                f"    argocd.argoproj.io/sync-wave: '{wave}'\n"
            )
            patch_obj = {
                "patch": LiteralString(patch_str),
                "target": {
                    "kind": "Job",
                    "name": actual_name,
                },
            }
            if patch_obj not in doc["patches"]:
                doc["patches"].append(patch_obj)

    def _add_deployment_sync_wave_patches(self, doc: dict) -> None:
        """mueve los deployments a wave 5 para que arranquen después de los jobs"""
        wave = self.config.deployment_sync_wave
        for app_name in self.config.deployment_names:
            if getattr(self.config, "deployments_to_delete", []) and app_name in self.config.deployments_to_delete:
                continue
                
            patch_str = (
                "apiVersion: apps/v1\n"
                "kind: Deployment\n"
                "metadata:\n"
                f'  name: "{app_name}"\n'
                "  annotations:\n"
                f"    argocd.argoproj.io/sync-wave: '{wave}'\n"
            )
            patch_obj = {
                "patch": LiteralString(patch_str),
                "target": {
                    "kind": "Deployment",
                    "name": app_name,
                },
            }
            if patch_obj not in doc["patches"]:
                doc["patches"].append(patch_obj)
