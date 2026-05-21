"""Public Python API for semshift."""

from semshift.core.semantic_diff import SemanticDiffResult, compare_files, compare_text

__all__ = ["SemanticDiffResult", "compare_files", "compare_text"]

__version__ = "0.2.0"
