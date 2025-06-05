# talk2n8n

A simple AI agent that integrates with n8n workflows and Slack, allowing you to trigger n8n workflows through natural language in Slack.

## Features

- 🤖 AI-powered workflow interaction through Slack
- 🔄 Automatic conversion of n8n workflows to LLM tools
- 🔌 Simple webhook integration with n8n
- 🧠 Uses Claude AI to understand and process requests
- ⚡ Asynchronous processing for time-consuming tasks

## Architecture

The n8n AI Agent uses a simple architecture with the following components:

1. **N8nClient**: Communicates with the n8n API to fetch workflows and trigger webhooks
2. **WorkflowConverter**: Extracts tool definitions from n8n workflow JSON
3. **ToolRegistry**: Manages the collection of tools extracted from n8n workflows
4. **Agent**: Processes messages using LLM and executes selected tools
5. **SlackHandler**: Handles incoming Slack messages and routes them to the Agent

## Setup

### Prerequisites

- Python 3.8+
- n8n instance with API access
- Slack workspace with bot permissions
- Claude API key

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/talk2n8n.git
   cd talk2n8n
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your configuration:
   ```
   # n8n Configuration
   N8N_API_KEY=your-n8n-api-key
   N8N_BASE_URL=https://your-n8n-instance.com

   # Slack Configuration
   SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
   SLACK_SIGNING_SECRET=your-slack-signing-secret
   SLACK_APP_TOKEN=xapp-your-slack-app-token

   # LLM Configuration
   CLAUDE_API_KEY=your-claude-api-key
   CLAUDE_MODEL=claude-3-opus-20240229
   ```

### Running the Agent

Start the agent with:

```bash
python -m n8n_agent.main
```

### Testing Interactively

You can test the agent interactively without Slack:

```bash
python -m n8n_agent.tests.test_interactive
```

This will allow you to:
1. Test fetching workflows from n8n
2. Test converting workflows to tools
3. Test the agent interactively with your own messages

## n8n Workflow Setup

For your n8n workflows to be compatible with the agent:

1. Each workflow should have a webhook node as its trigger
2. The webhook should have a clear path (e.g., `/send-email`)
3. Parameters should be well-defined in the workflow

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

## License

MIT
