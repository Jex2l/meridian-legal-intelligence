# Security Policy

Meridian Legal Intelligence handles legal documents on behalf of our users.
We take security reports seriously and will respond promptly.

## Reporting a Vulnerability

**Do not open a public GitHub issue for a security vulnerability.**

Instead, email **security@meridianlegal.ai** with:

- A description of the vulnerability and its potential impact
- Steps to reproduce it (a proof-of-concept, if you have one)
- Any relevant logs, screenshots, or affected URLs/endpoints

We aim to acknowledge reports within **2 business days** and to provide an
initial assessment within **5 business days**. We'll keep you updated as we
investigate and fix the issue, and will credit you in our release notes if
you'd like (or keep you anonymous, if you'd rather).

## In Scope

- The backend API (`backend/app/api/`) and its authentication, workspace
  isolation, and data-handling logic
- The client portal and marketing site (`frontend/`, `website/`)
- Dependency vulnerabilities in code we ship

## Out of Scope

- Vulnerabilities in third-party services we depend on (Anthropic, Ollama,
  your own infrastructure) — please report those directly to the
  responsible party
- Social engineering, physical security, or denial-of-service testing
  against any deployment you do not own
- Findings that require physical access to a user's device

## A Note on Workspace Isolation

Workspace isolation (one organization's documents never appearing in
another's query results) is the single most security-sensitive property of
this system — see `docs/BUILD_LOG.md` for how it's enforced and tested. If
you find a way to retrieve another workspace's documents, that is a
**critical** report; please disclose it privately per the process above
rather than publicly, and expect the fastest possible response.

## Supported Versions

This is an actively developed project without formal version releases yet.
Security fixes land on the `main` branch; there is no separate maintenance
branch at this stage.
