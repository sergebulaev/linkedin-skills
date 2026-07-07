# Security Policy

## Supported Versions

Only the latest released version of this skill bundle receives security
updates. Install from the `main` branch or the newest tagged release.

| Version | Supported |
| ------- | --------- |
| latest release | yes |
| older tags | no |

## Reporting a Vulnerability

If you find a security issue in this repository (for example: a skill
instruction that could be abused for prompt injection, a script that
mishandles credentials, or an unsafe command pattern), please report it
privately:

- **Preferred:** open a private report via
  [GitHub Security Advisories](https://github.com/sergebulaev/linkedin-skills/security/advisories/new)
- **Alternative:** email `s@bulaev.org` with subject `[SECURITY] linkedin-skills`

Please include:

1. A description of the issue and where it lives (file path, skill name)
2. Steps to reproduce or a proof of concept
3. The impact you believe it has

You can expect an acknowledgement within 72 hours and a fix or a public
disclosure decision within 14 days.

## Scope notes

- This bundle never ships hardcoded credentials. API tokens (Apify,
  Publora) are read from environment variables or `.env` files that are
  gitignored; see `.env.example`.
- Scripts in `lib/` and `scripts/` perform HTTP calls only to the Apify
  and Publora APIs and never execute shell commands built from remote
  content.
- Please do not test vulnerabilities against third-party services
  (LinkedIn, Apify, Publora) outside their own disclosure programs.
