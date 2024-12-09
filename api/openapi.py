from fastapi import FastAPI, APIRouter
from fastapi.openapi.utils import get_openapi
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import yaml
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class TaskRequest(BaseModel):
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Task description")
    type: str = Field(..., description="Task type (e.g., 'coding', 'research')")
    priority: int = Field(..., ge=1, le=5, description="Task priority (1-5)")
    parameters: Dict[str, Any] = Field(default={}, description="Additional parameters")

class TaskResponse(BaseModel):
    task_id: str = Field(..., description="Unique task ID")
    status: str = Field(..., description="Task status")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result")

class DocumentRequest(BaseModel):
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    tags: List[str] = Field(default=[], description="Document tags")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")

class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    k: int = Field(default=5, ge=1, le=100, description="Number of results")
    filters: Dict[str, Any] = Field(default={}, description="Search filters")

def setup_openapi(app: FastAPI, title: str, version: str):
    """Setup OpenAPI documentation"""
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=title,
            version=version,
            description="Jarvis Assistant API Documentation",
            routes=app.routes,
        )

        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

def create_api_documentation():
    """Create API documentation"""
    router = APIRouter()

    @router.post("/tasks", response_model=TaskResponse, tags=["Tasks"])
    async def create_task(task: TaskRequest):
        """
        Create a new task
        
        - **title**: Task title
        - **description**: Detailed task description
        - **type**: Task type (e.g., 'coding', 'research')
        - **priority**: Task priority (1-5)
        - **parameters**: Additional task parameters
        """
        pass

    @router.get("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
    async def get_task(task_id: str):
        """
        Get task details by ID
        
        - **task_id**: Unique task identifier
        """
        pass

    @router.post("/knowledge/documents", tags=["Knowledge"])
    async def add_document(document: DocumentRequest):
        """
        Add a document to the knowledge base
        
        - **title**: Document title
        - **content**: Document content
        - **tags**: List of tags
        - **metadata**: Additional metadata
        """
        pass

    @router.post("/knowledge/search", tags=["Knowledge"])
    async def search_knowledge(search: SearchRequest):
        """
        Search the knowledge base
        
        - **query**: Search query
        - **k**: Number of results to return
        - **filters**: Search filters
        """
        pass

    return router

def generate_openapi_spec(app: FastAPI, output_path: Path):
    """Generate OpenAPI specification file"""
    try:
        openapi_schema = app.openapi()
        
        # Save as YAML
        yaml_path = output_path / "openapi.yaml"
        with open(yaml_path, 'w') as f:
            yaml.dump(openapi_schema, f, sort_keys=False)
        
        # Save as JSON
        json_path = output_path / "openapi.json"
        with open(json_path, 'w') as f:
            app.openapi_schema = openapi_schema
            app.openapi()
            
        logger.info(f"OpenAPI specification generated: {yaml_path}, {json_path}")
        return True
    except Exception as e:
        logger.error(f"Error generating OpenAPI spec: {e}")
        return False
