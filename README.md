# talk2n8n

An intelligent AI agent that integrates with n8n workflows and Slack, allowing you to trigger n8n workflows through natural language in Slack.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Features

- 🤖 AI-powered workflow interaction through Slack
- 🔄 Automatic conversion of n8n workflows to LLM tools
- 🔌 Simple webhook integration with n8n
- 🧠 Uses Claude AI to understand and process requests
- ⚡ Asynchronous processing for time-consuming tasks
- 🔒 Secure handling of API keys and sensitive data
- 🌐 Easy deployment to cloud platforms

## Architecture

The n8n AI Agent uses a clean, modular architecture with the following components:

1. **N8nClient**: Communicates with the n8n API to fetch workflows and trigger webhooks
2. **LLM-powered Workflow Analysis**: Uses Claude AI to analyze n8n workflows and extract tool definitions
3. **ToolRegistry**: Manages the collection of tools extracted from n8n workflows
4. **Agent**: Processes messages using LLM and executes selected tools
5. **SlackHandler**: Handles incoming Slack messages and routes them to the Agent

## Setup

### Prerequisites

- Python 3.9+
- n8n instance with API access
- Slack workspace with bot permissions
- Claude API key from Anthropic

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/talk2n8n.git
   cd talk2n8n
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   ```

## Configuration

1. Copy the example environment file and update it with your settings:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your configuration:
   ```env
   # ========== Required Settings ==========
   
   # n8n Configuration
   N8N_WEBHOOK_BASE_URL=https://your-n8n-instance.com
   N8N_API_KEY=your-n8n-api-key
   N8N_ENV=test  # 'test', 'development', 'staging', or 'production'
   
   # Claude API Configuration (required for workflow conversion)
   CLAUDE_API_KEY=your-claude-api-key
   CLAUDE_MODEL=claude-3-opus-20240229  # or another supported model

   # ========== Optional Settings ==========
   
   # Logging
   LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
   
   # Slack Integration (optional)
   # SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
   # SLACK_SIGNING_SECRET=your-slack-signing-secret
   # SLACK_APP_TOKEN=xapp-your-slack-app-token
   ```

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `N8N_WEBHOOK_BASE_URL` | Yes | Base URL of your n8n instance | - |
| `N8N_API_KEY` | Yes | API key for n8n authentication | - |
| `N8N_ENV` | No | Environment: 'test', 'development', 'staging', or 'production' | 'test' |
| `CLAUDE_API_KEY` | Yes | API key for Anthropic's Claude API | - |
| `CLAUDE_MODEL` | No | Claude model to use | 'claude-3-opus-20240229' |
| `LOG_LEVEL` | No | Logging level | 'INFO' |
| `SLACK_BOT_TOKEN` | No | Slack bot token (required for Slack integration) | - |
| `SLACK_SIGNING_SECRET` | No | Slack signing secret (required for Slack integration) | - |
| `SLACK_APP_TOKEN` | No | Slack app token (required for Socket Mode) | - |

### Configuration Best Practices

1. **Security**:
   - Never commit your `.env` file to version control
   - Use environment variables or a secret management service in production
   - Rotate API keys and tokens regularly

2. **Performance**:
   - Set `LOG_LEVEL=WARNING` in production to reduce log noise
   - For development, use `LOG_LEVEL=DEBUG` for detailed logging

3. **Testing**:
   - Use `N8N_ENV=test` for testing to avoid affecting production data
   - Create a separate n8n instance for testing if possible

### Running the Agent

Start the agent with:

```bash
python -m main
```

### Testing Interactively

You can test the agent interactively without Slack:

```bash
python -m tests.test_interactive
```

This will allow you to:
1. Test fetching workflows from n8n
2. Test the LLM-based workflow conversion
3. Test the agent interactively with your own messages

## n8n Workflow Setup

For your n8n workflows to be compatible with the agent:

1. Each workflow should have a webhook node as its trigger
2. The webhook should have a clear path (e.g., `/send-email`)
3. Parameters should be well-defined in the workflow
4. Workflows should have clear names and descriptions for better LLM analysis
5. Consider adding comments to complex nodes to help the LLM understand their purpose

## Deployment to fly.io

To deploy the agent to fly.io:

1. Install the flyctl CLI:
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. Login to fly.io:
   ```bash
   flyctl auth login
   ```

3. Create a new app:
   ```bash
   flyctl launch
   ```

4. Set secrets:
   ```bash
   flyctl secrets set N8N_API_KEY=your-n8n-api-key
   flyctl secrets set N8N_BASE_URL=https://your-n8n-instance.com
   flyctl secrets set SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
   flyctl secrets set SLACK_SIGNING_SECRET=your-slack-signing-secret
   flyctl secrets set SLACK_APP_TOKEN=xapp-your-slack-app-token
   flyctl secrets set CLAUDE_API_KEY=your-claude-api-key
   flyctl secrets set CLAUDE_MODEL=claude-3-opus-20240229
   ```

5. Deploy the app:
   ```bash
   flyctl deploy
   ```

## Contributing

We welcome contributions to talk2n8n! Please see our [Contributing Guide](CONTRIBUTING.md) for more details on how to get started. All contributors are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md).

## Security

For information about security practices and how to report security issues, please see our [Security Policy](SECURITY.md).

## License

[MIT](LICENSE) © 2025 talk2n8n Contributors
