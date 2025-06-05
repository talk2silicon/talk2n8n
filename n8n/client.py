"""
n8n API client for interacting with n8n workflows.
"""
import os
import requests
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import pathlib

# Initialize logger
logger = logging.getLogger(__name__)

# Load environment variables from the n8n_agent directory
n8n_agent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(n8n_agent_dir, '.env')

# Check if the .env file exists
if os.path.exists(env_path):
    logger.info(f"Loading environment variables from: {env_path}")
    load_dotenv(env_path)
    
    # Check and log important environment variables
    required_vars = [
        "N8N_WEBHOOK_BASE_URL",
        "N8N_BASE_URL",
        "N8N_API_KEY",
        "CLAUDE_API_KEY",
        "CLAUDE_MODEL"
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask API keys in logs
            if "KEY" in var and value:
                masked_value = value[:5] + "..." + value[-5:] if len(value) > 10 else "***masked***"
                logger.info(f"{var}: {masked_value}")
            else:
                logger.info(f"{var}: {value}")
        else:
            logger.warning(f"Environment variable {var} not found or empty")
else:
    logger.warning(f"Environment file not found at {env_path}, using default values")
    # Try loading from parent directory as fallback
    parent_env_path = os.path.join(os.path.dirname(n8n_agent_dir), '.env')
    if os.path.exists(parent_env_path):
        logger.info(f"Loading environment variables from parent directory: {parent_env_path}")
        load_dotenv(parent_env_path)


class N8nClient:
    """Client for interacting with n8n API and webhooks."""
    
    def __init__(self, base_url=None, api_key=None):
        """
        Initialize the n8n client.
        
        Args:
            base_url: Base URL of the n8n instance (default: from env)
            api_key: API key for n8n (default: from env)
        """
        self.base_url = base_url or os.getenv("N8N_BASE_URL", "https://n8n-app-young-feather-1595.fly.dev")
        self.api_key = api_key or os.getenv("N8N_API_KEY")
        
        if not self.api_key:
            logger.warning("N8N_API_KEY not set. API calls will likely fail.")
    
    def get_workflows(self) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch all workflows from n8n instance.
        
        Returns:
            List of workflow data if successful, None otherwise
        """
        headers = {
            "X-N8N-API-KEY": self.api_key,
            "Accept": "application/json"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/workflows",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json().get("data", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching workflows: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Status code: {e.response.status_code}")
                logger.error(f"Response: {e.response.text}")
            return None
    
    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific workflow by ID.
        
        Args:
            workflow_id: ID of the workflow to fetch
            
        Returns:
            Workflow data if successful, None otherwise
        """
        headers = {
            "X-N8N-API-KEY": self.api_key,
            "Accept": "application/json"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/workflows/{workflow_id}",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching workflow {workflow_id}: {e}")
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
                logger.warning("No webhook nodes found in workflow")
                return ""
                
            # Get the first webhook node's path from parameters
            webhook_node = webhook_nodes[0]
            path = webhook_node.get("parameters", {}).get("path", "")
            
            # Remove leading slash if present
            path = path.lstrip("/")
            
            # If path is empty, try to use the webhookId as fallback
            if not path and "webhookId" in webhook_node:
                path = f"webhook/{webhook_node['webhookId']}"
                
            logger.info(f"Extracted webhook path: {path}")
            return path
            
        except Exception as e:
            logger.error(f"Error extracting webhook path: {e}")
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
            
        # Use the fixed URL from environment
        base_url = "https://n8n-app-young-feather-1595.fly.dev/webhook-test"
        full_url = f"{base_url}/{path}"
        
        logger.info(f"Constructed webhook URL: {full_url}")
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
            logger.info(f"Triggering webhook: {webhook_url}")
            logger.debug(f"Payload: {payload}")
            
            # If webhook_url is a relative path, make it absolute
            if not webhook_url.startswith("http"):
                webhook_url = f"{self.base_url}{webhook_url if webhook_url.startswith('/') else '/' + webhook_url}"
            
            # First try POST method
            logger.info("Trying POST method first...")
            try:
                response = requests.post(
                    webhook_url,
                    json=payload,
                    timeout=10
                )
                response.raise_for_status()
                logger.info("POST request successful")
            except requests.exceptions.RequestException as e:
                logger.warning(f"POST request failed: {e}. Trying GET method...")
                
                # If POST fails, try GET with params
                response = requests.get(
                    webhook_url,
                    params=payload,
                    timeout=10
                )
                response.raise_for_status()
                logger.info("GET request successful")
            
            # Parse response
            result = response.json() if response.text else {}
            
            return {
                "status": "success",
                "data": result
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error triggering webhook: {e}")
            
            error_response = {
                "status": "error",
                "message": str(e)
            }
            
            # Add response details if available
            if hasattr(e, "response") and e.response:
                error_response["status_code"] = e.response.status_code
                try:
                    error_response["response"] = e.response.json()
                except:
                    error_response["response"] = e.response.text
                    
            return error_response
