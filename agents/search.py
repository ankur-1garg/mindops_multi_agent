# agents/search.py
import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from .base_agent import BaseAgent, StepResult
from state.workflow_state import WorkflowState
from utils.logger import setup_logger

logger = setup_logger(__name__)

class SearchAgent(BaseAgent):
    """Dynamically searches a repository to find the most relevant file."""

    def __init__(self, repo_path: str): # <<< ADD repo_path HERE
        self.repo_path = repo_path # <<< ADD this line        self.repo_path = repo_path
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.file_catalog = []
        self.index = None

    def _build_index_on_the_fly(self):
        """Scans the temporary repo and builds a vector index in memory."""
        logger.info(f"[{self.repo_path}] Building file index on the fly...")
        for root, _, files in os.walk(self.repo_path):
            if ".git" in root:
                continue
            for file in files:
                if file.endswith(('.tsx', '.jsx', '.js')):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.repo_path)
                    
                    # For a simple index, we can use the file path itself as text
                    self.file_catalog.append({
                        "source_file": rel_path.replace('\\', '/'),
                        "content_for_search": f"File path is {rel_path}. This file is a component."
                    })
        
        if not self.file_catalog:
            logger.warning("No searchable files found in the repository.")
            return

        # Create FAISS index
        content_to_embed = [item['content_for_search'] for item in self.file_catalog]
        embeddings = self.embedding_model.encode(content_to_embed)
        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index = faiss.IndexIDMap(self.index)
        ids = np.array(range(len(self.file_catalog)))
        self.index.add_with_ids(embeddings.astype('float32'), ids)
        logger.info(f"On-the-fly index built with {len(self.file_catalog)} files.")

    async def execute(self, state: WorkflowState) -> StepResult:
        logger.info(f"[{state.workflow_id}] [Search] Agent: Finding relevant screen...")
        
        # Build the index if it hasn't been built yet
        if self.index is None:
            self._build_index_on_the_fly()

        if not self.file_catalog:
            return StepResult(success=False, message="Could not find any source files in the repository.")

        # Perform the search
        query = state.intent.get('search_query', state.user_request)
        query_embedding = self.embedding_model.encode([query])
        
        distances, ids = self.index.search(query_embedding.astype('float32'), k=1)
        
        if not ids.size:
            return StepResult(success=False, message="No relevant file found in the repository.")
        
        best_match_index = ids[0][0]
        best_match = self.file_catalog[best_match_index]
        
        # Create a simplified screen object for the state
        screen_data = {
            'screen_id': f"file-{best_match_index}",
            'screen_name': os.path.basename(best_match['source_file']),
            'description': f"Component located at {best_match['source_file']}",
            'source_file': best_match['source_file']
        }

        state.screen = screen_data
        logger.info(f"[{state.workflow_id}] Found best match file: {screen_data['source_file']}")
        return StepResult(success=True, data={'screen': screen_data}, message=f"Found file: {screen_data['source_file']}")