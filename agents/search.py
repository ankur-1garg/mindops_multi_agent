# agents/search.py
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from .base_agent import BaseAgent, StepResult
from state.workflow_state import WorkflowState
from utils.logger import setup_logger
import requests
import base64

logger = setup_logger(__name__)


class SearchAgent(BaseAgent):
    """Finds the right screen and component to modify."""

    def __init__(self, repo_path: str = None):
        logger.info("[Search] Agent: Initializing...")
        self.repo_path = repo_path

    async def execute(self, state: WorkflowState) -> StepResult:
        # For now, we'll always return the main landing page
        logger.info(
            f"[{state.workflow_id}] [Search] Agent: Finding relevant screen...")

        # Create a fixed screen entry for the main landing page
        landing_page = {
            'screen_id': 'main-landing',
            'screen_name': 'Landing Page',
            'description': 'Main landing page of the website',
            'source_file': 'src/app/site/page.tsx'
        }

        state.screen = landing_page  # Update the shared state
        logger.info(
            f"[{state.workflow_id}] Found screen: {landing_page['screen_name']}")
        return StepResult(success=True, data={'screen': landing_page}, message=f"Found screen: {landing_page['screen_name']}")
