"""
n8n API client for interacting with n8n workflows.
"""

# Standard library imports
import logging
from typing import Any, Dict, List, Optional

# Third-party imports
import requests

# Local application imports
from src.config.settings import settings


# Initialize logger
logger = logging.getLogger(__name__)


class N8nClient:
    """Client for interacting with n8n API and webhooks."""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize the n8n client.

        Args:
            base_url: Base URL of the n8n instance (default: from config)
            api_key: API key for n8n (default: from config)
        """
        self.base_url = base_url or settings.N8N_BASE_URL or settings.N8N_WEBHOOK_BASE_URL
        self.api_key = api_key or settings.N8N_API_KEY

        # Set up requests session with default headers
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "X-N8N-API-KEY": self.api_key or ""}
        )

        if not self.base_url:
            logger.warning("Neither N8N_BASE_URL nor N8N_WEBHOOK_BASE_URL is set in config")
        if not self.api_key:
            logger.warning("N8N_API_KEY not set in config")

    def get_workflows(self) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch all workflows from n8n instance.

        Returns:
            List of workflow data if successful, None otherwise
        """
        headers = {"X-N8N-API-KEY": self.api_key, "Accept": "application/json"}

        try:
            response = self.session.get(f"{self.base_url}/api/v1/workflows", timeout=10)
            response.raise_for_status()
            return response.json().get("data", [])
        except Exception as e:
            logger.error(f"Failed to fetch workflows: {e}")
            return None

    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific workflow by ID.

        Args:
            workflow_id: ID of the workflow to fetch

        Returns:
            Workflow data if successful, None otherwise
        """
        headers = {"X-N8N-API-KEY": self.api_key, "Accept": "application/json"}

        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/workflows/{workflow_id}", timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching workflow: {e}")
            return None

    def extract_webhook_path(self, workflow_data: Dict[str, Any]) -> str:
        """
        Extract the webhook path from a workflow.

        Args:
            workflow_data: Workflow data containing nodes

        Returns:
            Webhook path if found, empty string otherwise
        """
        try:
            # Extract nodes from the workflow
            nodes = workflow_data.get("nodes", [])

            # Find webhook nodes
            webhook_nodes = [node for node in nodes if node.get("type") == "n8n-nodes-base.webhook"]

            if not webhook_nodes:
                # No webhook nodes
                return ""

            # Get the first webhook node's path from parameters
            webhook_node = webhook_nodes[0]
            path = webhook_node.get("parameters", {}).get("path", "")

            # Remove leading slash if present
            path = path.lstrip("/")

            # If path is empty, try to use the webhookId as fallback
            if not path and "webhookId" in webhook_node:
                path = f"webhook/{webhook_node['webhookId']}"

            # Webhook path extracted
            return path

        except Exception as e:
            logger.error(f"Webhook extraction error: {e}")
            return ""

    def get_webhook_url(self, workflow_data: Dict[str, Any]) -> str:
        """
        Get the full webhook URL for a workflow using the environment URL.

        Args:
            workflow_data: Workflow data containing nodes

        Returns:
            Full webhook URL
        """
        path = self.extract_webhook_path(workflow_data)
        if not path:
            return ""

        # Use the webhook base URL from client
        if not self.base_url:
            logger.warning("No base URL available for webhook")
            return ""

        # Construct the full webhook URL
        full_url = f"{self.base_url.rstrip('/')}/{path}"

        # Webhook URL constructed
        return full_url

    def trigger_webhook(self, webhook_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trigger a webhook with the given payload. Tries both POST and GET methods.

        Args:
            webhook_url: URL of the webhook to trigger
            payload: Payload to send to the webhook

        Returns:
            Response from the webhook
        """
        try:
            # Triggering webhook

            # If webhook_url is a relative path, make it absolute
            if not webhook_url.startswith("http"):
                webhook_url = f"{self.base_url}{webhook_url if webhook_url.startswith('/') else '/' + webhook_url}"

            # First try POST method
            # Try POST
            try:
                response = self.session.post(webhook_url, json=payload, timeout=10)
                response.raise_for_status()
                # POST successful
            except Exception as e:
                # Continue with GET request for any exception
                # POST failed, trying GET

                # If POST fails, try GET with params
                response = self.session.get(webhook_url, params=payload, timeout=10)
                response.raise_for_status()
                # GET successful

            # Parse response
            result = response.json() if response.text else {}

            return {"status": "success", "data": result}

        except Exception as e:
            logger.error(f"Webhook error: {e}")

            error_response = {"status": "error", "message": str(e)}

            # Add response details if available
            if hasattr(e, "response") and e.response:
                error_response["status_code"] = e.response.status_code
                try:
                    error_response["response"] = e.response.json()
                except:
                    error_response["response"] = e.response.text

            return error_response
