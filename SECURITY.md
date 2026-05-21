# Security Policy

## Supported Versions

SemShift is pre-1.0. Security fixes will target the latest released version.

## Reporting a Vulnerability

Please report security issues privately through GitHub Security Advisories if available:

https://github.com/VeerajSai/SemShift/security/advisories/new

If advisories are not available, open a minimal issue asking for a private contact path without disclosing sensitive details.

## Scope

Relevant security issues include:

- unsafe file handling
- command injection in CLI or GitHub Action paths
- accidental credential exposure in reports or logs
- unsafe handling of GitHub tokens in the action

SemShift is local-first by default. Optional embedding models may download weights on first use, and future external integrations should stay explicit opt-in.
