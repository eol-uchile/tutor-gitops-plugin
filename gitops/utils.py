import yaml
from typing import List


class LiteralString(str):
    """subclase de str para forzar a PyYAML a formatear con block scalar (|)"""
    pass


def _literal_string_representer(dumper, data):
    # formatea strings multilínea con '|' para no romper parches inline de kustomize
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")


yaml.add_representer(LiteralString, _literal_string_representer)
yaml.SafeDumper.add_representer(LiteralString, _literal_string_representer)


def parse_yaml_docs(content: str) -> List[dict]:
    """parsea YAML multi-documento ignorando bloques vacíos o comentarios sueltos"""
    return [
        doc for doc in yaml.safe_load_all(content)
        if doc and isinstance(doc, dict)
    ]


def dump_yaml_docs(docs: List[dict]) -> str:
    """serializa lista de diccionarios a YAML preservando el orden de campos"""
    return yaml.dump_all(docs, sort_keys=False, default_flow_style=False)


def get_pod_spec(doc: dict) -> dict | None:
    """extrae el pod spec de un workload (Deployment, Job, CronJob, etc) según su kind"""
    kind = doc.get("kind")
    if kind in ("Deployment", "StatefulSet", "DaemonSet", "Job"):
        return doc.get("spec", {}).get("template", {}).get("spec")
    elif kind == "CronJob":
        return (
            doc.get("spec", {})
            .get("jobTemplate", {})
            .get("spec", {})
            .get("template", {})
            .get("spec")
        )
    return None


def path_matches(path: str, *suffixes: str) -> bool:
    """valida si el archivo coincide con alguno de los nombres o extensiones indicados"""
    return any(path.endswith(s) for s in suffixes)
