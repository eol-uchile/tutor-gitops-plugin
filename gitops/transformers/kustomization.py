from typing import List
from ..utils import LiteralString, path_matches
from .base import ManifestTransformer

class KustomizationTransformer(ManifestTransformer):
    """limpieza y ajustes sobre kustomization.yml."""

    def should_apply(self, path: str) -> bool:
        return path_matches(path, "kustomization.yml", "kustomization.yaml")

    def transform(self, docs: List[dict]) -> List[dict]:
        for doc in docs:
            self._add_extra_resources(doc)
            self._set_generator_options(doc)
            self._filter_sensitive_configmap_generators(doc)
            self._add_service_type_patches(doc)
            self._add_images(doc)
        return docs

    def _add_images(self, doc: dict) -> None:
        """inyecta la sección images configurada"""
        if "images" not in doc:
            doc["images"] = []
        for img in self.config.kustomize_images:
            if img not in doc["images"]:
                doc["images"].append(img)

    def _add_extra_resources(self, doc: dict) -> None:
        """agrega recursos adicionales a la sección resources"""
        resources = doc.get("resources")
        if not isinstance(resources, list):
            return
        for resource in self.config.extra_resources:
            if resource not in resources:
                resources.append(resource)

    def _set_generator_options(self, doc: dict) -> None:
        """evita hashes aleatorios en nombres para poder referenciar configmaps fijos en los pods"""
        doc["generatorOptions"] = {"disableNameSuffixHash": True}

    def _filter_sensitive_configmap_generators(self, doc: dict) -> None:
        """elimina los configMaps sensibles del kustomization y los maneja como Secrets"""
        generators = doc.get("configMapGenerator")
        if not isinstance(generators, list):
            return
        doc["configMapGenerator"] = [
            gen for gen in generators
            if gen.get("name") not in self.config.sensitive_configmaps
        ]

    def _add_service_type_patches(self, doc: dict) -> None:
        """fuerza ClusterIP en servicios que no necesitan LoadBalancer (Gateway API maneja el ingress)"""
        if "patches" not in doc:
            doc["patches"] = []

        for svc_name, svc_type in self.config.service_type_overrides.items():
            patch_str = (
                "apiVersion: v1\n"
                "kind: Service\n"
                "metadata:\n"
                f'  name: "{svc_name}"\n'
                "spec:\n"
                f"  type: {svc_type}\n"
            )
            patch_obj = {
                "patch": LiteralString(patch_str),
                "target": {
                    "kind": "Service",
                    "name": svc_name,
                },
            }
            if patch_obj not in doc["patches"]:
                doc["patches"].append(patch_obj)
