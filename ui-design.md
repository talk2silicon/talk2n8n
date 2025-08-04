# Talk2n8n UI Design

## Overview
A modern, desktop-style Gradio UI for interacting with n8n workflows through natural language using Claude AI.

## Layout Design
```
+----------------------------------------+
|  [Logo] Talk2n8n                 [⚙️]   |
+----------------------------------------+
|          |                             |
| Settings |     Main Chat Area          |
| Panel    |                             |
|          |     [Messages]              |
| - LLM    |                            |
| - n8n    |     [Input Box]            |
| - Tools  |     [Send] [Clear]         |
|          |                             |
+----------------------------------------+
```

## Core Components

### 1. Settings Panel

```
🔑 LLM Configuration
├── Provider: [Claude ▼]
├── API Key: [****] 
└── Model: [claude-3-opus-20240229 ▼]

🔌 n8n Connection
├── Base URL: [https://...]
├── API Key: [****]
├── [Test Connection]
└── Environment: [test ▼]

🛠️ Available Tools
├── [Refresh]
└── [Tool List with status indicators]
```

### 2. Chat Interface
- Message history with timestamps
- Code/response formatting with syntax highlighting
- Tool execution progress indicators
- Real-time status updates
- Markdown support

### 3. Modern UI Elements
- Floating action buttons
- Toast notifications
- Subtle animations
- Monospace font for code
- Command palette (Cmd/Ctrl + K)

## Project Structure

```
talk2n8n/
├── src/
│   ├── n8n/          # Existing n8n integration
│   ├── agent/        # Existing agent code
│   ├── config/       # Existing config
│   └── ui/           # New UI components
│       ├── __init__.py
│       ├── app.py    # Main Gradio app
│       ├── components/
│       │   ├── chat.py
│       │   ├── settings.py
│       │   └── tools_panel.py
│       ├── static/
│       │   ├── css/
│       │   └── js/
│       └── utils/
│           ├── storage.py
│           └── websocket.py
```

## Technical Stack

### Core UI
- Gradio 4.0+ for base components
- Custom CSS for modern styling
- LocalStorage for settings persistence
- WebSocket for real-time updates

### Dependencies

```python
# Add to requirements.txt:
gradio>=4.0.0
websockets
markdown
pygments  # for code highlighting
```

## Features

### 1. Settings Management
- Auto-save to LocalStorage
- Secure API key handling
- Connection status indicators
- Environment switching

### 2. Real-time Updates
- WebSocket for live tool status
- Progress indicators
- Toast notifications
- Error handling with retry

### 3. User Experience
- Keyboard shortcuts
- Command palette
- Context-aware help
- Tool suggestions
- Message history

### 4. Tool Integration
- Dynamic tool loading
- Status indicators
- Parameter validation
- Execution progress tracking

## Implementation Plan

### Phase 1: Basic Setup
1. Create UI folder structure
2. Set up Gradio app skeleton
3. Implement basic chat interface
4. Add settings panel structure

### Phase 2: Core Features
1. Integrate with existing ToolService
2. Add real-time updates
3. Implement settings persistence
4. Add basic styling

### Phase 3: Enhanced Features
1. Add advanced UI components
2. Implement keyboard shortcuts
3. Add command palette
4. Enhance error handling

### Phase 4: Polish
1. Add animations
2. Improve styling
3. Add help system
4. Performance optimization

## Notes
- Keep UI components modular
- Focus on user experience
- Maintain clear separation of concerns
- Use type hints throughout
- Add comprehensive error handling
- Include loading states for all operations
