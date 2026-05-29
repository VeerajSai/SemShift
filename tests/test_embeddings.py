"""Tests for embedding backends."""

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
        sim_similar = cosine_similarity(result.vectors[0:1], result.vectors[1:2])[0][0]
        sim_different = cosine_similarity(result.vectors[0:1], result.vectors[2:3])[0][0]
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

    def test_invalid_model_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="Unknown model"):
            embed_texts(["some text"], model_name="nonexistent-model-xyz-123")

    def test_obvious_tfidf_typo_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="Unknown model"):
            embed_texts(["some text"], model_name="tfdif")


class TestEmbedderProtocol:
    def test_get_embedder_returns_tfidf_embedder(self):
        from semshift.core.embeddings import BaseEmbedder, TfidfEmbedder, get_embedder

        embedder = get_embedder("tfidf")
        assert isinstance(embedder, TfidfEmbedder)
        assert isinstance(embedder, BaseEmbedder)
        assert embedder.backend_type == "lexical"

    def test_facade_matches_embedder_output(self):
        from semshift.core.embeddings import get_embedder

        texts = ["we share data with partners", "we may share data"]
        facade = embed_texts(texts, model_name="tfidf")
        direct = get_embedder("tfidf").embed(texts)
        assert facade.backend == direct.backend == "tfidf"
        assert facade.backend_type == direct.backend_type == "lexical"
        assert facade.vectors.shape == direct.vectors.shape

    def test_get_embedder_validates_semantic_name(self):
        with pytest.raises(ValueError, match="Unknown model"):
            from semshift.core.embeddings import get_embedder

            get_embedder("definitely-not-a-model")

    def test_semantic_embedder_selected_for_hf_id(self):
        from semshift.core.embeddings import SentenceTransformerEmbedder, get_embedder

        embedder = get_embedder("sentence-transformers/all-MiniLM-L6-v2")
        assert isinstance(embedder, SentenceTransformerEmbedder)
        assert embedder.backend_type == "semantic"
