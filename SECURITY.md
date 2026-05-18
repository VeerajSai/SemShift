# Security Policy

## Supported Versions

SemShift is pre-1.0. Security fixes will target the latest released version.

## Reporting a Vulnerability

Please report security issues privately through GitHub Security Advisories if available:

https://github.com/VeerajSai/semshift/security/advisories/new

If advisories are not available, open a minimal issue asking for a private contact path without disclosing sensitive details.

## Scope

Relevant security issues include:

- unsafe file handling
- command injection in CLI or GitHub Action paths
- accidental credential exposure in reports or logs
- unsafe handling of GitHub tokens in the action

SemShift does not send text to paid APIs by default. Future optional LLM backends should preserve explicit opt-in behavior.

