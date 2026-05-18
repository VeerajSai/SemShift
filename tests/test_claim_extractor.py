"""Tests for claim extraction and comparison."""

from semshift.core.claim_extractor import ClaimDiff, compare_claims, extract_claims


def test_extract_claims_numbers_and_percentages() -> None:
    claims = extract_claims("Accuracy improved from 91.2% to 94% for 10,000 users.")

    values = [term.value for term in claims.numbers]

    assert "91.2%" in values
    assert "94%" in values
    assert "10,000 users" in values


def test_compare_claims_numeric_modification() -> None:
    diff = compare_claims(
        "We retain logs for 30 days.",
        "We retain logs for 180 days.",
    )

    assert diff.modified_numbers
    assert diff.modified_numbers[0]["old"] == "30 days"
    assert diff.modified_numbers[0]["new"] == "180 days"


def test_compare_claims_modal_strengthening_and_softening() -> None:
    stronger = compare_claims("We may share data.", "We will share data.")
    softer = compare_claims("Users must provide consent.", "Users may provide consent.")

    assert stronger.strengthened_claims
    assert stronger.strengthened_claims[0]["old"].lower() == "may"
    assert stronger.strengthened_claims[0]["new"].lower() == "will"
    assert softer.softened_claims
    assert softer.softened_claims[0]["old"].lower() == "must"
    assert softer.softened_claims[0]["new"].lower() == "may"


def test_extract_claims_prioritizes_useful_terms_over_heading_noise() -> None:
    claims = extract_claims(
        "## Consent\n\nUsers may opt out of analytics. "
        "Acme retains personal data for 30 days and supports GDPR exports."
    )

    entity_values = {term.value for term in claims.entities}
    policy_values = {term.normalized() for term in claims.policy_terms}

    assert "Users" not in entity_values
    assert "Consent" not in entity_values
    assert "Acme" in entity_values
    assert "personal data" in policy_values
    assert "opt out" in policy_values


def test_extract_claims_detects_dates() -> None:
    claims = extract_claims("The policy was last updated on January 1, 2024.")
    assert claims.dates
    assert any("2024" in term.value for term in claims.dates)


def test_extract_claims_detects_strong_phrases() -> None:
    claims = extract_claims("We guarantee data security. Access is always available.")
    phrase_values = {term.normalized() for term in claims.strong_phrases}
    assert "guarantee" in phrase_values or "guaranteed" in phrase_values
    assert "always" in phrase_values


def test_extract_claims_detects_policy_terms() -> None:
    claims = extract_claims("We collect personal data and require consent. Third parties may track you.")
    terms = {term.normalized() for term in claims.policy_terms}
    assert "personal data" in terms
    assert "consent" in terms
    assert "third party" in terms or "third parties" in terms


def test_extract_claims_detects_role_titles() -> None:
    claims = extract_claims("I worked as a Software Engineer at Acme Corp.")
    role_values = [term.value.lower() for term in claims.role_titles]
    assert any("software engineer" in v for v in role_values)


def test_extract_claims_detects_metrics() -> None:
    claims = extract_claims("Our model achieves 95% accuracy and low latency of 10ms.")
    metric_values = {term.value.lower() for term in claims.metrics}
    assert "accuracy" in metric_values


def test_claim_diff_change_count_sums_all_categories() -> None:
    diff = compare_claims(
        "We do not share data. We retain logs for 30 days.",
        "We may share data with partners. We retain logs for 180 days. We now track location.",
    )
    assert diff.change_count == (
        len(diff.added_claims)
        + len(diff.removed_claims)
        + len(diff.modified_numbers)
        + len(diff.softened_claims)
        + len(diff.strengthened_claims)
    )


def test_claim_diff_change_count_zero_for_identical_text() -> None:
    diff = compare_claims("The system may produce errors.", "The system may produce errors.")
    assert diff.change_count == 0


def test_compare_claims_detects_added_strong_phrase() -> None:
    diff = compare_claims(
        "We protect your data.",
        "We guarantee your data is always safe and secure.",
    )
    assert diff.strengthened_claims or diff.added_claims


def test_compare_claims_detects_removed_strong_phrase() -> None:
    diff = compare_claims(
        "This tool is guaranteed to work reliably.",
        "This tool may work in most cases.",
    )
    assert diff.softened_claims or diff.removed_claims


def test_claim_diff_to_dict_has_all_keys() -> None:
    diff = compare_claims("old text", "new text")
    d = diff.to_dict()
    assert set(d.keys()) == {
        "added_claims",
        "removed_claims",
        "modified_numbers",
        "softened_claims",
        "strengthened_claims",
        "change_count",
    }


def test_extract_claims_on_empty_string() -> None:
    claims = extract_claims("")
    assert claims.numbers == []
    assert claims.dates == []
    assert claims.modals == []
    assert claims.change_count == 0 if hasattr(claims, "change_count") else True


def test_extract_claims_numbers_million_suffix() -> None:
    claims = extract_claims("The company has 1.5 million users.")
    values = [term.numeric_value for term in claims.numbers if term.numeric_value is not None]
    assert any(v == 1_500_000 for v in values)


def test_compare_claims_no_change_when_same_number() -> None:
    diff = compare_claims("We retain logs for 30 days.", "We retain logs for 30 days.")
    assert not diff.modified_numbers


def test_extract_claims_metric_without_nearby_number_filtered() -> None:
    claims = extract_claims("Consider the latency characteristics of the system.")
    metric_values = [term.value.lower() for term in claims.metrics]
    assert "latency" not in metric_values


def test_extract_claims_metric_with_nearby_number_included() -> None:
    claims = extract_claims("The system latency is 5ms.")
    metric_values = [term.value.lower() for term in claims.metrics]
    assert "latency" in metric_values
