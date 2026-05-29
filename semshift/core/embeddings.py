"""Embedding backends for semantic matching."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol, runtime_checkable

import numpy as np

DEFAULT_MODEL = "tfidf"
TFIDF_ALIASES = {"tfidf", "lexical", "local", "local-tfidf", "heuristic"}
KNOWN_SENTENCE_TRANSFORMER_MODELS = {
    "all-MiniLM-L6-v2",
    "sentence-transformers/all-MiniLM-L6-v2",
    "all-mpnet-base-v2",
    "sentence-transformers/all-mpnet-base-v2",
    "multi-qa-MiniLM-L6-cos-v1",
    "sentence-transformers/multi-qa-MiniLM-L6-cos-v1",
}
HF_MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*$")


@dataclass(frozen=True)
class EmbeddingResult:
    """Vectors and backend metadata."""

    vectors: np.ndarray
    backend: str
    backend_type: str = "lexical"
    warnings: tuple[str, ...] = ()


@runtime_checkable
class BaseEmbedder(Protocol):
    """Protocol for embedding backends.

    A backend turns a list of texts into vectors plus metadata. New backends
    (e.g. NLI or other local models) only need to implement ``embed``.
    """

    name: str
    backend_type: str

    def embed(self, texts: list[str]) -> EmbeddingResult:
        """Embed ``texts`` and return vectors with backend metadata."""
        ...


class TfidfEmbedder:
    """Deterministic lexical TF-IDF backend (the default)."""

    backend_type = "lexical"

    def __init__(self, name: str = "tfidf") -> None:
        self.name = name

    def embed(self, texts: list[str]) -> EmbeddingResult:
        return _tfidf_embeddings(texts, backend=self.name)


class SentenceTransformerEmbedder:
    """Optional local semantic backend (requires ``semshift[models]``)."""

    backend_type = "semantic"

    def __init__(self, name: str) -> None:
        self.name = name

    def embed(self, texts: list[str]) -> EmbeddingResult:
        model = _load_sentence_transformer(self.name)
        vectors = model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return EmbeddingResult(
            vectors=np.asarray(vectors, dtype=float),
            backend=self.name,
            backend_type="semantic",
        )


def get_embedder(model_name: str = DEFAULT_MODEL) -> BaseEmbedder:
    """Select the embedder backend for ``model_name`` (validates semantic names)."""
    requested = model_name.strip() if model_name else DEFAULT_MODEL
    if requested.lower() in TFIDF_ALIASES:
        return TfidfEmbedder(name="tfidf")
    _validate_semantic_model_name(requested)
    return SentenceTransformerEmbedder(requested)


def embed_texts(texts: list[str], model_name: str = DEFAULT_MODEL) -> EmbeddingResult:
    """Embed texts with a lexical TF-IDF backend or optional local semantic embeddings."""
    if not texts:
        return EmbeddingResult(vectors=np.zeros((0, 0)), backend="empty")
    return get_embedder(model_name).embed(texts)


@lru_cache(maxsize=4)
def _load_sentence_transformer(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on optional extra
        raise ValueError(
            "SentenceTransformers backend requested but optional dependencies are missing. "
            'Install with: pip install "semshift[models]"'
        ) from exc

    return SentenceTransformer(model_name, trust_remote_code=False)


def _tfidf_embeddings(texts: list[str], backend: str) -> EmbeddingResult:
    from sklearn.feature_extraction.text import TfidfVectorizer

    if not any(text.strip() for text in texts):
        return EmbeddingResult(
            vectors=np.zeros((len(texts), 1)), backend=backend, backend_type="lexical"
        )

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), lowercase=True)
    try:
        matrix = vectorizer.fit_transform(texts)
    except ValueError:
        return EmbeddingResult(
            vectors=np.zeros((len(texts), 1)), backend=backend, backend_type="lexical"
        )
    return EmbeddingResult(
        vectors=matrix.astype(float).toarray(), backend=backend, backend_type="lexical"
    )


def _validate_semantic_model_name(model_name: str) -> None:
    """Reject likely typos while allowing explicit Hugging Face model IDs."""
    allowed = _allowed_models()
    if allowed and model_name not in allowed:
        raise ValueError(
            f"Model '{model_name}' is not allowed in this environment. "
            f"Allowed models: {', '.join(sorted(allowed))}"
        )
    if model_name in KNOWN_SENTENCE_TRANSFORMER_MODELS:
        return
    if HF_MODEL_RE.fullmatch(model_name) and ".." not in model_name:
        return
    valid = ", ".join(sorted(TFIDF_ALIASES | KNOWN_SENTENCE_TRANSFORMER_MODELS))
    raise ValueError(
        f"Unknown model '{model_name}'. Use a lexical backend ({', '.join(sorted(TFIDF_ALIASES))}) "
        f"or an explicit Hugging Face model id such as 'sentence-transformers/all-MiniLM-L6-v2'. "
        f"Known local-friendly models: {valid}"
    )


def _allowed_models() -> set[str]:
    raw = os.environ.get("SEMSHIFT_ALLOWED_MODELS", "")
    return {item.strip() for item in raw.split(",") if item.strip()}
