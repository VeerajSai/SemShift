"""Tests for scoring utilities."""

import pytest

from semshift.utils.scoring import clamp, drift_label, label_meets, weighted_sum


class TestClamp:
    def test_value_in_range_unchanged(self):
        assert clamp(0.5) == 0.5

    def test_below_minimum_clamped_to_zero(self):
        assert clamp(-1.0) == 0.0

    def test_above_maximum_clamped_to_one(self):
        assert clamp(1.5) == 1.0

    def test_exactly_at_boundaries(self):
        assert clamp(0.0) == 0.0
        assert clamp(1.0) == 1.0

    def test_custom_bounds(self):
        assert clamp(0.5, minimum=0.6, maximum=0.9) == 0.6
        assert clamp(1.0, minimum=0.6, maximum=0.9) == 0.9


class TestDriftLabel:
    def test_zero_is_low(self):
        assert drift_label(0.0) == "low"

    def test_just_below_medium_boundary(self):
        assert drift_label(0.24) == "low"

    def test_at_medium_boundary(self):
        assert drift_label(0.25) == "medium"

    def test_just_below_high_boundary(self):
        assert drift_label(0.514) == "medium"

    def test_at_high_boundary(self):
        assert drift_label(0.515) == "high"

    def test_just_below_critical_boundary(self):
        assert drift_label(0.69) == "high"

    def test_at_critical_boundary(self):
        assert drift_label(0.70) == "critical"

    def test_one_is_critical(self):
        assert drift_label(1.0) == "critical"

    def test_out_of_range_clamped(self):
        assert drift_label(2.0) == "critical"
        assert drift_label(-1.0) == "low"


class TestLabelMeets:
    def test_same_label_meets(self):
        assert label_meets("high", "high") is True

    def test_higher_label_meets_lower_threshold(self):
        assert label_meets("critical", "high") is True
        assert label_meets("critical", "low") is True
        assert label_meets("high", "medium") is True

    def test_lower_label_does_not_meet_higher_threshold(self):
        assert label_meets("low", "medium") is False
        assert label_meets("medium", "critical") is False
        assert label_meets("high", "critical") is False

    def test_unknown_label_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown drift threshold"):
            label_meets("unknown", "high")

    def test_unknown_threshold_raises_value_error(self):
        with pytest.raises(ValueError):
            label_meets("high", "extreme")

    def test_case_insensitive(self):
        assert label_meets("HIGH", "high") is True
        assert label_meets("Low", "MEDIUM") is False

    def test_none_threshold_never_fails(self):
        assert label_meets("critical", "none") is False
        assert label_meets("high", "NONE") is False


class TestWeightedSum:
    def test_equal_weights(self):
        result = weighted_sum([(0.5, 1.0), (0.5, 1.0)])
        assert abs(result - 0.5) < 1e-9

    def test_different_weights(self):
        result = weighted_sum([(1.0, 0.8), (0.0, 0.2)])
        assert abs(result - 0.8) < 1e-9

    def test_all_zero_scores(self):
        assert weighted_sum([(0.0, 0.5), (0.0, 0.5)]) == 0.0

    def test_empty_list_returns_zero(self):
        assert weighted_sum([]) == 0.0

    def test_zero_total_weight_returns_zero(self):
        assert weighted_sum([(0.5, 0.0)]) == 0.0

    def test_result_clamped_to_one(self):
        assert weighted_sum([(2.0, 1.0)]) == 1.0

    def test_single_component(self):
        result = weighted_sum([(0.7, 1.0)])
        assert abs(result - 0.7) < 1e-9
