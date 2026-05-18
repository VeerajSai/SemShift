from semshift.core.claim_extractor import compare_claims, extract_claims


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
