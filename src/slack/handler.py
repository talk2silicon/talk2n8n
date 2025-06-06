"""
Slack event handler for processing Slack events.
"""
import logging
import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from agent.agent import Agent

logger = logging.getLogger(__name__)

class SlackHandler:
    """Handler for Slack events."""
    
    def __init__(self, agent: Agent = None):
        """
        Initialize the Slack handler.
        
        Args:
            agent: Agent for processing messages
        """
        self.agent = agent or Agent()
        
        # Initialize Slack app
        self.app = App(
            token=os.getenv("SLACK_BOT_TOKEN"),
            signing_secret=os.getenv("SLACK_SIGNING_SECRET")
        )
        
        # Register event handlers
        self._register_handlers()
        
    def _register_handlers(self):
        """Register event handlers with the Slack app."""
        # Register message handler
        self.app.message()(self.handle_message)
        
        # Register app_mention handler
        self.app.event("app_mention")(self.handle_app_mention)
        
        # Event handlers registered
    
    def start(self):
        """Start the Slack handler."""
        # Start the app
        handler = SocketModeHandler(self.app, os.getenv("SLACK_APP_TOKEN"))
        # Start handler
        handler.start()
    
    def handle_message(self, message, say):
        """
        Handle direct messages.
        
        Args:
            message: Message event from Slack
            say: Function to send a message to the channel
        """
        # Skip messages from bots
        if message.get("bot_id"):
            return
            
        # Process the message
        user_id = message.get("user")
        text = message.get("text", "")
        
        # Message received
        
        # Process the message with the agent
        # This will return an immediate acknowledgment
        response = self.agent.process_message(text)
        
        # Send the acknowledgment
        say(response)
    
    def handle_app_mention(self, event, say):
        """
        Handle app mentions in channels.
        
        Args:
            event: App mention event from Slack
            say: Function to send a message to the channel
        """
        user_id = event.get("user")
        text = event.get("text", "")
        
        # Remove the bot mention from the text
        text = text.split(">", 1)[1].strip() if ">" in text else text
        
        # App mention received
        
        # Process the message with the agent
        response = self.agent.process_message(text)
        
        # Send the acknowledgment
        say(response)
