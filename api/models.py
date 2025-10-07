# api/models.py
from pydantic import BaseModel

class WorkflowRequest(BaseModel):
    user_request: str
    repo_url: str # Add this line
    
class WorkflowResponse(BaseModel):
    workflow_id: str
    status: str