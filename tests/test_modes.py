"""Tests for mode configuration."""

import pytest

from semshift.core.modes import MODES, ModeConfig, get_mode, list_modes


class TestGetMode:
    def test_valid_mode_names_return_config(self):
        for name in ("default", "policy", "readme", "research", "resume", "prompt"):
            config = get_mode(name)
            assert isinstance(config, ModeConfig)
            assert config.name == name

    def test_case_insensitive_lookup(self):
        assert get_mode("POLICY").name == "policy"
        assert get_mode("Policy").name == "policy"
        assert get_mode("README").name == "readme"

    def test_strips_whitespace_on_lookup(self):
        assert get_mode("  policy  ").name == "policy"

    def test_unknown_mode_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown mode"):
            get_mode("nonexistent")

    def test_error_message_lists_valid_modes(self):
        with pytest.raises(ValueError) as exc_info:
            get_mode("bad_mode")
        error = str(exc_info.value)
        for name in ("default", "policy", "readme", "research", "resume", "prompt"):
            assert name in error


class TestListModes:
    def test_returns_all_six_modes(self):
        modes = list_modes()
        assert len(modes) == 6

    def test_returns_sorted_list(self):
        modes = list_modes()
        assert modes == sorted(modes)

    def test_contains_all_expected_modes(self):
        modes = list_modes()
        for name in ("default", "policy", "readme", "research", "resume", "prompt"):
            assert name in modes


class TestModeConfig:
    def test_every_mode_has_description(self):
        for config in MODES.values():
            assert config.description
            assert len(config.description) > 0

    def test_every_mode_has_focus_terms(self):
        for config in MODES.values():
            assert config.focus_terms
            assert len(config.focus_terms) > 0

    def test_policy_mode_has_relevant_terms(self):
        config = MODES["policy"]
        assert "share" in config.focus_terms or any("shar" in t for t in config.focus_terms)

    def test_research_mode_has_relevant_terms(self):
        config = MODES["research"]
        assert any(t in config.focus_terms for t in ("metric", "accuracy", "baseline", "dataset"))

    def test_mode_configs_are_frozen(self):
        config = get_mode("policy")
        with pytest.raises((AttributeError, TypeError)):
            config.name = "changed"  # type: ignore[misc]
