import logging
from typing import List
from .transformers.base import ManifestTransformer
from .utils import dump_yaml_docs, parse_yaml_docs

logger = logging.getLogger(__name__)

class TransformPipeline:

    def __init__(self, transformers: List[ManifestTransformer]):
        self.transformers = transformers

    def process(self, content: str, path: str) -> str:
        applicable = [t for t in self.transformers if t.should_apply(path)]
        if not applicable:
            return content

        docs = parse_yaml_docs(content)
        if not docs:
            return content

        for transformer in applicable:
            logger.debug("applying %s to %s", transformer.name, path)
            try:
                docs = transformer.transform(docs)
            except Exception:
                logger.error(
                    "transformer %s failed on %s",
                    transformer.name,
                    path,
                    exc_info=True,
                )
                raise

        return dump_yaml_docs(docs)
