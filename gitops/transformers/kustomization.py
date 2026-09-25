from typing import List
from ..utils import LiteralString, path_matches
from .base import ManifestTransformer

class KustomizationTransformer(ManifestTransformer):
    """limpieza y ajustes sobre kustomization.yml."""

    def should_apply(self, path: str) -> bool:
        return path_matches(path, "kustomization.yml", "kustomization.yaml")

    def transform(self, docs: List[dict]) -> List[dict]:
        for doc in docs:
            self._fix_resource_paths(doc)
            self._add_extra_resources(doc)
            self._set_generator_options(doc)
            self._filter_sensitive_configmap_generators(doc)
            self._add_service_type_patches(doc)
            self._add_openedx_env_patches(doc)
            self._add_images(doc)
        return docs

    def _fix_resource_paths(self, doc: dict) -> None:
        """remueve el prefijo k8s/ de los recursos porque ahora se escriben en la raíz del output"""
        resources = doc.get("resources")
        if not isinstance(resources, list):
            return
            
        new_resources = []
        for r in resources:
            if isinstance(r, str) and r.startswith("k8s/"):
                new_resources.append(r[4:])
            else:
                new_resources.append(r)
        doc["resources"] = new_resources

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
        
        # Filtrar configmaps sensibles
        filtered = [gen for gen in generators if gen.get("name") not in self.config.sensitive_configmaps]
        
        # Filtrar configmaps de deployments eliminados (ej: caddy-config, nginx-config)
        deps_to_delete = getattr(self.config, "deployments_to_delete", [])
        final_filtered = []
        for gen in filtered:
            name = gen.get("name", "")
            # Si el configmap se llama <dep>-config y <dep> está eliminado, lo quitamos
            dep_name = name.replace("-config", "")
            if dep_name in deps_to_delete:
                continue
            final_filtered.append(gen)
            
        doc["configMapGenerator"] = final_filtered



    def _add_service_type_patches(self, doc: dict) -> None:
        """fuerza ClusterIP en servicios que no necesitan LoadBalancer (Gateway API maneja el ingress)"""
        if "patches" not in doc:
            doc["patches"] = []

        deps_to_delete = getattr(self.config, "deployments_to_delete", [])
        
        for svc_name, svc_type in self.config.service_type_overrides.items():
            if svc_name in deps_to_delete:
                continue

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

    def _add_openedx_env_patches(self, doc: dict) -> None:
        """inyecta env vars (ej. LMS_CFG/STUDIO_CFG) en los contenedores de Open edX vía strategic merge"""
        if not self.config.openedx_env_vars:
            return
        if "patches" not in doc:
            doc["patches"] = []

        api_versions = {"Deployment": "apps/v1", "Job": "batch/v1"}
        env_lines = "".join(
            f"        - name: {name}\n"
            f"          value: {value}\n"
            for name, value in self.config.openedx_env_vars.items()
        )

        deps_to_delete = getattr(self.config, "deployments_to_delete", [])
        jobs_to_delete = getattr(self.config, "jobs_to_delete", [])
        
        for target in self.config.openedx_env_targets:
            kind, name, container = target["kind"], target["name"], target["container"]
            
            if kind == "Deployment" and name in deps_to_delete:
                continue
            if kind == "Job" and name in jobs_to_delete:
                continue
                
            actual_name = getattr(self.config, "job_renames", {}).get(name, name) if kind == "Job" else name

            kind, name, container = target["kind"], actual_name, target["container"]
            patch_str = (
                f"apiVersion: {api_versions[kind]}\n"
                f"kind: {kind}\n"
                "metadata:\n"
                f'  name: "{name}"\n'
                "spec:\n"
                "  template:\n"
                "    spec:\n"
                "      containers:\n"
                f"      - name: {container}\n"
                "        env:\n"
                f"{env_lines}"
            )
            patch_obj = {
                "patch": LiteralString(patch_str),
                "target": {"kind": kind, "name": name},
            }
            if patch_obj not in doc["patches"]:
                doc["patches"].append(patch_obj)
