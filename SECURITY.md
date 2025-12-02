# Security Policy

## Supported Versions

We currently support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| latest  | :white_check_mark: |
| YYYY-MM-DD (nightly) | :white_check_mark: |

## Reporting a Vulnerability

We take the security of tail-lookup seriously. If you discover a security vulnerability, please follow responsible disclosure practices:

### For Critical Vulnerabilities

**DO NOT** create a public GitHub issue. Instead:

1. **Use GitHub Security Advisories** (preferred):
   - Go to https://github.com/ryakel/tail-lookup/security/advisories/new
   - Provide detailed information about the vulnerability
   - Wait for acknowledgment before public disclosure

2. **Contact the maintainer directly**:
   - Check [CODEOWNERS](/.github/CODEOWNERS) for contact information
   - Provide a clear description of the vulnerability
   - Include steps to reproduce if possible

### What Qualifies as Critical?

- Authentication/authorization bypasses
- SQL injection or other injection vulnerabilities
- Remote code execution
- Exposure of sensitive data
- Any issue that could be actively exploited

### For Non-Critical Security Concerns

For security best practices, configuration improvements, or dependency updates with known CVEs:

- Use our [Security Vulnerability Report](https://github.com/ryakel/tail-lookup/issues/new?template=security_report.yml) issue template
- These reports are public, so avoid sharing exploit details

## What to Expect

1. **Acknowledgment**: We'll acknowledge receipt within 48-72 hours
2. **Investigation**: We'll investigate and validate the vulnerability
3. **Fix Development**: A patch will be developed and tested
4. **Disclosure Timeline**: We aim to patch critical vulnerabilities within 30-90 days
5. **Credit**: You may be credited in the security advisory (if desired)

## Security Best Practices for Deployment

When deploying tail-lookup:

- Keep Docker images updated to the latest version
- Monitor for security advisories on our [GitHub Security](https://github.com/ryakel/tail-lookup/security) page
- Follow the principle of least privilege for container permissions
- Use network isolation where possible
- Enable Docker health checks for monitoring

## Scope

This security policy applies to:

- The tail-lookup API (FastAPI application)
- Docker images published to Docker Hub
- Database generation scripts
- CI/CD workflows and automation

## Out of Scope

The following are considered out of scope:

- Issues in third-party dependencies (report to upstream projects)
- Social engineering attacks
- Physical security issues
- Denial of service (DoS) attacks

## Contact

- **Security Issues**: Use GitHub Security Advisories or issue templates
- **General Questions**: Open a [Discussion](https://github.com/ryakel/tail-lookup/discussions)
- **Code Owner**: See [CODEOWNERS](/.github/CODEOWNERS)

Thank you for helping keep tail-lookup and its users secure! 🛡️
