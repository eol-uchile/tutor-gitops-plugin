from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class GitOpsConfig:
    """valores de configuración para las transformaciones GitOps"""

    # Kustomization resources
    extra_resources: List[str] = field(default_factory=lambda: [
        "secrets",
    ])
    # ArgoCD sync waves
    job_sync_waves: Dict[str, str] = field(default_factory=lambda: {
        "minio-job": "1",
        "lms-job": "2",
        "cms-job": "3",
        "forum-job": "3",
        "discovery-job": "3",
    })
    deployment_sync_wave: str = "5"
    deployment_names: List[str] = field(default_factory=lambda: [
        "lms", "lms-worker", "cms", "cms-worker",
        "forum", "caddy", "nginx", "discovery"
    ])

    # Secrets
    deployment_secret_name: str = "deployment-secrets"
    # original env var -> (nuevo nombre, key del secret)
    # Si env_name es None, se mantiene el nombre original.
    env_var_secret_mapping: Dict[str, Dict[str, Optional[str]]] = field(
        default_factory=lambda: {
            "MYSQL_ROOT_PASSWORD": {
                "env_name": None,
                "secret_key": "MYSQL_ROOT_PASSWORD",
            },
            "MINIO_ACCESS_KEY": {
                "env_name": "MINIO_ROOT_USER",
                "secret_key": "MINIO_ROOT_USER",
            },
            "MINIO_SECRET_KEY": {
                "env_name": "MINIO_ROOT_PASSWORD",
                "secret_key": "MINIO_ROOT_PASSWORD",
            },
        }
    )
    # Images for Kustomize (se reescribirán en el entorno de despliegue)
    kustomize_images: List[Dict[str, str]] = field(default_factory=lambda: [
        {
            "name": "docker.io/overhangio/openedx",
            "newName": "ghcr.io/eol-uchile/openedx-eol",
            "newTag": "lilac-testing",
        },
        {
            "name": "docker.io/overhangio/openedx-forum",
            "newName": "docker.io/overhangio/openedx-forum",
            "newTag": "12.2.0",
        }
    ])
    sensitive_configmaps: List[str] = field(default_factory=lambda: [
        "openedx-settings-lms",
        "openedx-settings-cms",
        "openedx-config",
        "discovery-settings",
    ])

    # Jobs
    jobs_to_delete: List[str] = field(default_factory=lambda: [
        "mysql-job",
    ])
    job_commands: Dict[str, dict] = field(default_factory=lambda: {
        # lms-job y cms-job:
        # forzamos DJANGO_SETTINGS_MODULE a producción para evitar que intente cargar librerías de dev (como debug_toolbar)
        # NOTA: dockerize ES OBLIGATORIO porque aunque ArgoCD use Sync Waves, el pod de MySQL se reporta como "Healthy"
        # apenas arranca el contenedor, pero tarda unos segundos extra en abrir el puerto 3306, haciendo crashear a Django
        "lms-job": {
            "container": "lms",
            "command": ["bash", "-c"],
            "args": [
                "dockerize -wait tcp://mysql:3306 -timeout 60s && "
                "export DJANGO_SETTINGS_MODULE=lms.envs.tutor.production && "
                "./manage.py lms migrate"
            ],
        },
        "cms-job": {
            "container": "cms",
            "command": ["bash", "-c"],
            "args": [
                "dockerize -wait tcp://mysql:3306 -timeout 60s && "
                "export DJANGO_SETTINGS_MODULE=cms.envs.tutor.production && "
                "./manage.py cms migrate"
            ],
        },
        # forum-job:
        # Reconstruye los índices de búsqueda en Elasticsearch para que las discusiones del foro funcionen.
        # Lo forzamos explícitamente para asegurar que los índices existan en cada despliegue.
        "forum-job": {
            "container": "forum",
            "args": [
                "bash", "-c",
                "bundle exec rake search:initialize && bundle exec rake search:rebuild_indices",
            ],
        },
        # minio-job:
        # utiliza el cliente 'mc' para crear los buckets necesarios (openedx, openedxuploads, openedxvideos)
        # y configura las políticas públicas correctas, sin este job LMS/CMS fallan al intentar guardar archivos
        "minio-job": {
            "container": "minio",
            "command": ["sh", "-c"],
            "args": [
                "mc config host add minio http://minio:9000 "
                "$MINIO_ROOT_USER $MINIO_ROOT_PASSWORD --api s3v4 "
                "&& mc mb --ignore-existing minio/openedx minio/openedxuploads minio/openedxvideos "
                "&& mc policy set public minio/openedx",
            ],
        },
        "discovery-job": {
            "container": "discovery",
            "command": ["bash", "-c"],
            "args": [
                "while ! (echo > /dev/tcp/mysql/3306) >/dev/null 2>&1; do sleep 2; done; "
                "export DJANGO_SETTINGS_MODULE=course_discovery.settings.tutor.production && "
                "./manage.py migrate"
            ],
        },
    })

    # service type overrides (Gateway API maneja el tráfico externo)
    service_type_overrides: Dict[str, str] = field(default_factory=lambda: {
        "caddy": "ClusterIP",
    })
