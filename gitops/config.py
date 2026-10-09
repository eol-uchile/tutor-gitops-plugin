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
        "migrate-job": "2",
        "discovery-migrate-job": "3",
    })
    deployment_sync_wave: str = "5"
    deployment_names: List[str] = field(default_factory=lambda: [
        "lms", "lms-worker", "cms", "cms-worker",
        "forum", "caddy", "nginx", "discovery"
    ])

    # Secrets
    deployment_secret_name: str = "deployment-secrets"
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

    # Jobs & Deployments
    deployments_to_delete: List[str] = field(default_factory=lambda: [])

    job_renames: Dict[str, str] = field(default_factory=lambda: {
        "lms-job": "migrate-job",
        "discovery-job": "discovery-migrate-job",
    })

    jobs_to_delete: List[str] = field(default_factory=lambda: [
        "mysql-job", "cms-job", "forum-job", "minio-job"
    ])
    
    job_commands: Dict[str, dict] = field(default_factory=lambda: {
        "lms-job": {
            "container": "lms",
            "command": ["bash", "-c"],
            "args": [
                "export DJANGO_SETTINGS_MODULE=lms.envs.tutor.production && "
                "./manage.py lms migrate && "
                "export DJANGO_SETTINGS_MODULE=cms.envs.tutor.production && "
                "./manage.py cms migrate"
            ],
        },
        "discovery-job": {
            "container": "discovery",
            "command": ["bash", "-c"],
            "args": [
                "export DJANGO_SETTINGS_MODULE=course_discovery.settings.tutor.production && "
                "./manage.py migrate"
            ],
        },
    })

    service_type_overrides: Dict[str, str] = field(default_factory=lambda: {
        "caddy": "ClusterIP",
    })

    openedx_env_vars: Dict[str, str] = field(default_factory=lambda: {
        "LMS_CFG": "/openedx/config/lms.env.yml",
        "STUDIO_CFG": "/openedx/config/cms.env.yml",
    })
    
    openedx_env_targets: List[Dict[str, str]] = field(default_factory=lambda: [
        {"kind": "Deployment", "name": "lms", "container": "lms"},
        {"kind": "Deployment", "name": "lms-worker", "container": "lms-worker"},
        {"kind": "Deployment", "name": "cms", "container": "cms"},
        {"kind": "Deployment", "name": "cms-worker", "container": "cms-worker"},
        {"kind": "Job", "name": "lms-job", "container": "lms"},
        {"kind": "Job", "name": "cms-job", "container": "cms"},
    ])
