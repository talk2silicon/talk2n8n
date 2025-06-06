# Security Policy

## Reporting a Vulnerability

We take the security of talk2n8n seriously. If you believe you've found a security vulnerability, please follow these steps:

1. **Do not disclose the vulnerability publicly** until it has been addressed by the maintainers.
2. Email your findings to [INSERT SECURITY EMAIL]. If possible, encrypt your message with our PGP key (available on our website).
3. Include the following information:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested mitigations if you have them

## What to Expect

- We will acknowledge receipt of your vulnerability report within 48 hours.
- We will provide a more detailed response within 7 days, indicating the next steps in handling your submission.
- We will keep you informed about our progress in addressing the vulnerability.
- We will credit you for your discovery (unless you prefer to remain anonymous).

## Security Best Practices for Contributors

When contributing to talk2n8n, please follow these security best practices:

1. **Never commit sensitive information** such as API keys, passwords, or tokens to the repository.
2. Use environment variables or secure vaults for storing sensitive information.
3. Keep dependencies updated to avoid known vulnerabilities.
4. Follow the principle of least privilege when designing new features.
5. Validate and sanitize all user inputs.
6. Be cautious with external libraries and review their security practices.

## Security Considerations

talk2n8n interacts with several external services, each with their own security considerations:

### n8n Workflows

- Ensure your n8n instance is properly secured with authentication.
- Be careful about what data is processed in workflows.
- Review webhook security settings in n8n.

### Claude API

- Keep your API keys secure and rotate them regularly.
- Be mindful of what data is sent to the Claude API.

### Slack Integration

- Review Slack app permissions carefully.
- Use the minimum permissions necessary for your integration.

## Supported Versions

Only the latest major version of talk2n8n receives security updates. We recommend always using the most recent version.
