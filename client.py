import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from .agents.base_agent import BaseAgent, StepResult
from state.workflow_state import WorkflowState
from utils.logger import setup_logger

logger = setup_logger(__name__)

class SearchAgent(BaseAgent):
    """Dynamically searches a repository to find the most relevant file."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.file_paths = []  # Simplified: a list of strings
        self.index = None

    def _build_index_on_the_fly(self):
        """Scans the repo and builds a vector index from file paths."""
        logger.info(f"[{self.repo_path}] Building file index on the fly...")
        
        for root, _, files in os.walk(self.repo_path):
            if ".git" in root:
                continue
            for file in files:
                # We only care about front-end component/page files
                if file.endswith(('.tsx', '.jsx', '.js')):
                    full_path = os.path.join(root, file)
                    # Use normalized, forward-slash paths for consistency
                    rel_path = os.path.relpath(full_path, self.repo_path).replace('\\', '/')
                    self.file_paths.append(rel_path)
        
        if not self.file_paths:
            logger.warning("No searchable source files (.tsx, .jsx, .js) found.")
            return

        logger.info(f"Found {len(self.file_paths)} source files. Building index...")
        
        # Create FAISS index from the list of file paths
        embeddings = self.embedding_model.encode(self.file_paths)
        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index = faiss.IndexIDMap(self.index)
        ids = np.array(range(len(self.file_paths)))
        self.index.add_with_ids(embeddings.astype('float32'), ids)
        logger.info("On-the-fly index built successfully.")

    async def execute(self, state: WorkflowState) -> StepResult:
        try:
            logger.info(f"[{state.workflow_id}] [Search] Agent: Finding relevant file...")
            if self.index is None:
                self._build_index_on_the_fly()

            if not self.file_paths:
                return StepResult(success=False, message="Could not find any source files in the repository.")

            query = state.intent.get('search_query', state.user_request)
            query_embedding = self.embedding_model.encode([query])
            
            _, ids = self.index.search(query_embedding.astype('float32'), k=1)
            
            if not ids.size:
                return StepResult(success=False, message="No relevant file found for the query.")
            
            best_match_index = ids[0][0]
            best_match_path = self.file_paths[best_match_index]
            
            # Create the screen object for the state
            screen_data = {
                'screen_name': os.path.basename(best_match_path),
                'description': f"Component located at {best_match_path}",
                'source_file': best_match_path
            }
            state.screen = screen_data
            
            message = f"Found best match file: {screen_data['source_file']}"
            logger.info(f"[{state.workflow_id}] {message}")
            return StepResult(success=True, data={'screen': screen_data}, message=message)
            
        except Exception as e:
            logger.error(f"[{state.workflow_id}] Unhandled error in SearchAgent: {e}", exc_info=True)
            return StepResult(success=False, message=f"Error in search agent: {e}")