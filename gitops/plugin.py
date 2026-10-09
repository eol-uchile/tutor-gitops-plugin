"""
plugin gitops para tutor
intercepta env.write_to para aplicar transformaciones a los manifiestos
k8s antes de que se escriban
"""
import logging
import os
from tutor import env
from .config import GitOpsConfig
from .pipeline import TransformPipeline
from .transformers import (
    ArgoCDTransformer,
    JobTransformer,
    DeploymentTransformer,
    KustomizationTransformer,
    SecretsTransformer,
)

logger = logging.getLogger(__name__)

# _gitops_config para no chocar con la convención de Tutor v0
_gitops_config = GitOpsConfig()

# el orden importa:
# - kustomization y argocd trabajan sobre kustomization.yml
# - jobs primero, luego secrets
_pipeline = TransformPipeline([
    KustomizationTransformer(_gitops_config),
    ArgoCDTransformer(_gitops_config),
    JobTransformer(_gitops_config),
    SecretsTransformer(_gitops_config),
    DeploymentTransformer(_gitops_config),
])

_original_write_to = env.write_to

def _gitops_write_to(content, path):
    if isinstance(content, str):
        content = _pipeline.process(content, path)
        
    # escribimos en el destino original
    result = _original_write_to(content, path)
    
    path_str = str(path)
    
    # y además escribimos una copia en out_dir/ si corresponde
    out_dir = os.environ.get("GITOPS_OUTPUT_DIR")
    
    if out_dir:
        if "/env/k8s/" in path_str:
            k8s_path = path_str.replace("/env/k8s/", f"/{out_dir}/")
            _original_write_to(content, k8s_path)

        elif "/env/apps/" in path_str:
            base_allowed = ["caddy", "nginx", "permissions", "redis", "openedx"]
            deps_to_delete = getattr(_gitops_config, "deployments_to_delete", [])
            allowed_apps = [app for app in base_allowed if app not in deps_to_delete]
            
            parts = path_str.split("/env/apps/")

            if len(parts) == 2:
                app_name = parts[1].split("/")[0]
                if app_name in allowed_apps:
                    apps_path = path_str.replace("/env/apps/", f"/{out_dir}/apps/")
                    _original_write_to(content, apps_path)
        elif path_str.endswith("/env/kustomization.yml"):
            kustom_path = path_str.replace("/env/kustomization.yml", f"/{out_dir}/kustomization.yml")
            _original_write_to(content, kustom_path)
        
    return result

env.write_to = _gitops_write_to
