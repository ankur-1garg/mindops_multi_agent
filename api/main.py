# api/main.py
import uuid
import asyncio
from fastapi import FastAPI, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
import os

from api.models import WorkflowRequest, WorkflowResponse
from agents.orchestrator import OrchestratorAgent
from state.workflow_state import WorkflowState
from catalog_builder import CatalogBuilder
import config

# --- WebSocket Manager ---


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, workflow_id: str, websocket: WebSocket):
        await websocket.accept()
        if workflow_id not in self.active_connections:
            self.active_connections[workflow_id] = []
        self.active_connections[workflow_id].append(websocket)

    def disconnect(self, workflow_id: str, websocket: WebSocket):
        self.active_connections[workflow_id].remove(websocket)

    async def broadcast(self, workflow_id: str, data: dict):
        if workflow_id in self.active_connections:
            for connection in self.active_connections[workflow_id]:
                await connection.send_json(data)


manager = ConnectionManager()

# --- In-memory storage for workflow status ---
workflow_statuses: Dict[str, WorkflowState] = {}

# --- Orchestrator Instance ---
orchestrator = OrchestratorAgent(websocket_manager=manager)


async def ensure_catalog_exists():
    """Ensures the application catalog exists by running the crawler if needed."""
    if not os.path.exists('output/catalog.json'):
        print("\n🕷️ First-time setup: Running app crawler...")
        builder = CatalogBuilder(
            app_url="https://saas-website-builder.vercel.app/",
            repo_path=config.REPO_PATH
        )
        await builder.run()
        print(" Catalog build complete!")


async def run_workflow_background(workflow_id: str, user_request: str, repo_url: str):
    # First ensure we have the catalog
    await ensure_catalog_exists()

    # Then process the user's request
    final_state = await orchestrator.process_request(workflow_id, user_request, repo_url)
    workflow_statuses[workflow_id] = final_state

# --- FastAPI App ---
app = FastAPI(title="MindOps.AI Multi-Agent API")


@app.on_event("startup")
async def startup_event():
    """Run on server startup to ensure the catalog exists."""
    await ensure_catalog_exists()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)


@app.post("/workflow", response_model=WorkflowResponse)
async def create_workflow(request: WorkflowRequest, background_tasks: BackgroundTasks):
    workflow_id = str(uuid.uuid4())

    # Use the default repository URL if none is provided
    repo_url = request.repo_url or "https://github.com/ankur-1garg/mindops_multi_agent.git"

    workflow_statuses[workflow_id] = WorkflowState(
        workflow_id=workflow_id,
        user_request=request.user_request,
        repo_url=repo_url,
        status="started"
    )

    background_tasks.add_task(
        run_workflow_background,
        workflow_id=workflow_id,
        user_request=request.user_request,
        repo_url=repo_url
    )

    return WorkflowResponse(workflow_id=workflow_id, status="started")


@app.get("/workflow/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    return workflow_statuses.get(workflow_id, {"status": "not_found"})


@app.websocket("/ws/{workflow_id}")
async def websocket_endpoint(websocket: WebSocket, workflow_id: str):
    await manager.connect(workflow_id, websocket)
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(workflow_id, websocket)
