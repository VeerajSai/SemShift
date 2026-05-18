"""Tests for embedding backends."""

import numpy as np
import pytest

from semshift.core.embeddings import embed_texts


class TestTfidfEmbeddings:
    def test_returns_embedding_result_with_tfidf_backend(self):
        result = embed_texts(["hello world", "goodbye world"], model_name="tfidf")
        assert result.backend == "tfidf"
        assert result.vectors.shape[0] == 2

    def test_vector_dimension_consistent_across_texts(self):
        result = embed_texts(["foo bar", "baz qux", "hello world"], model_name="tfidf")
        assert result.vectors.shape[0] == 3
        assert result.vectors.shape[1] > 0

    def test_similar_texts_have_higher_cosine_similarity(self):
        from sklearn.metrics.pairwise import cosine_similarity

        result = embed_texts(
            ["we share data with partners", "we may share data", "the cat sat on the mat"],
            model_name="tfidf",
        )
        sim_similar = cosine_similarity(
            result.vectors[0:1], result.vectors[1:2]
        )[0][0]
        sim_different = cosine_similarity(
            result.vectors[0:1], result.vectors[2:3]
        )[0][0]
        assert sim_similar > sim_different

    def test_identical_texts_have_maximum_similarity(self):
        from sklearn.metrics.pairwise import cosine_similarity

        result = embed_texts(["hello world", "hello world"], model_name="tfidf")
        sim = cosine_similarity(result.vectors[0:1], result.vectors[1:2])[0][0]
        assert sim > 0.99

    def test_empty_texts_list_returns_empty_result(self):
        result = embed_texts([], model_name="tfidf")
        assert result.backend == "empty"
        assert result.vectors.shape[0] == 0

    def test_all_empty_strings_handled_gracefully(self):
        result = embed_texts(["", ""], model_name="tfidf")
        assert result.vectors.shape[0] == 2

    def test_tfidf_aliases_all_work(self):
        for alias in ("tfidf", "local", "local-tfidf", "heuristic"):
            result = embed_texts(["test text"], model_name=alias)
            assert result.backend == "tfidf"

    def test_no_warnings_on_tfidf_backend(self):
        result = embed_texts(["some text"], model_name="tfidf")
        assert result.warnings == ()

    def test_invalid_model_falls_back_to_tfidf(self):
        result = embed_texts(["some text"], model_name="nonexistent-model-xyz-123")
        assert "tfidf" in result.backend
        assert len(result.warnings) > 0
        assert "nonexistent-model-xyz-123" in result.warnings[0]
