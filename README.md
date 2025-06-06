# talk2n8n

An intelligent AI agent that integrates with n8n workflows, allowing you to trigger n8n workflows through natural language using Claude AI.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Features

- 🤖 AI-powered workflow interaction using Claude
- 🔄 LLM-based workflow-to-tool conversion
- 🔌 Simple webhook integration with n8n
- 🧠 Intelligent parameter extraction
- ⚡ Fast and reliable execution
- 🔒 Secure handling of API keys

## Architecture

The n8n AI Agent uses a clean, modular architecture with the following components:

1. **N8nClient**: Communicates with the n8n API to fetch workflows and trigger webhooks
2. **ToolService**: Manages workflow-to-tool conversion and execution using Claude AI
3. **Agent**: Processes user requests and executes appropriate tools

## Setup

### Prerequisites

- Python 3.9+
- n8n instance with API access
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

Set up your environment variables:

```env
# n8n Configuration
N8N_WEBHOOK_BASE_URL=https://your-n8n-instance.com
N8N_API_KEY=your-n8n-api-key
N8N_ENV=test  # 'test', 'development', 'staging', or 'production'

# Claude API Configuration
CLAUDE_API_KEY=your-claude-api-key
CLAUDE_MODEL=claude-3-opus-20240229

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

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

## Contributing

We welcome contributions to talk2n8n! Please see our [Contributing Guide](CONTRIBUTING.md) for more details on how to get started. All contributors are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md).

## Security

For information about security practices and how to report security issues, please see our [Security Policy](SECURITY.md).

## License

[MIT](LICENSE) © 2025 talk2n8n Contributors
