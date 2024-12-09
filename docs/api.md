# Jarvis Assistant API Documentation

## API Overview

The Jarvis Assistant API provides comprehensive endpoints for system management, task automation, and knowledge base operations. All endpoints use JSON for request and response bodies, and follow RESTful principles.

## Authentication

### JWT Authentication
```http
POST /api/auth/token
Content-Type: application/json

{
  "username": "string",
  "password": "string"
}
```

Response:
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 3600
}
```

All subsequent requests must include the JWT token in the Authorization header:
```http
Authorization: Bearer <access_token>
```

## System Operations

### Get System Status
```http
GET /api/system/status
```

Response:
```json
{
  "cpu_percent": 45.2,
  "memory_percent": 62.8,
  "disk_percent": 75.0,
  "network_io": {
    "bytes_sent": 1024000,
    "bytes_recv": 2048000
  },
  "active_tasks": 5,
  "error_count": 0,
  "is_hibernating": false
}
```

### Toggle Hibernation
```http
POST /api/system/hibernate
Content-Type: application/json

{
  "enabled": true
}
```

Response:
```json
{
  "status": "success",
  "is_hibernating": true,
  "timestamp": "2024-12-07T02:16:36-05:00"
}
```

### Update Resource Limits
```http
PUT /api/system/resources
Content-Type: application/json

{
  "cpu_percent": 80,
  "memory_percent": 80,
  "disk_percent": 90
}
```

Response:
```json
{
  "status": "success",
  "resource_limits": {
    "cpu_percent": 80,
    "memory_percent": 80,
    "disk_percent": 90
  }
}
```

## Task Management

### Create Task
```http
POST /api/tasks
Content-Type: application/json

{
  "title": "string",
  "description": "string",
  "priority": 1,
  "due_date": "2024-12-07T02:16:36-05:00",
  "tags": ["tag1", "tag2"]
}
```

Response:
```json
{
  "id": "uuid",
  "title": "string",
  "description": "string",
  "status": "pending",
  "created_at": "2024-12-07T02:16:36-05:00",
  "updated_at": "2024-12-07T02:16:36-05:00"
}
```

### Get Task Status
```http
GET /api/tasks/{task_id}
```

Response:
```json
{
  "id": "uuid",
  "status": "running",
  "progress": 45,
  "result": null,
  "error": null
}
```

### List Tasks
```http
GET /api/tasks?status=pending&limit=10&offset=0
```

Response:
```json
{
  "total": 45,
  "items": [
    {
      "id": "uuid",
      "title": "string",
      "status": "pending",
      "created_at": "2024-12-07T02:16:36-05:00"
    }
  ]
}
```

## Knowledge Base

### Add Document
```http
POST /api/knowledge/documents
Content-Type: application/json

{
  "title": "string",
  "content": "string",
  "metadata": {
    "source": "string",
    "author": "string",
    "tags": ["tag1", "tag2"]
  }
}
```

Response:
```json
{
  "id": "uuid",
  "title": "string",
  "embedding_status": "processing",
  "created_at": "2024-12-07T02:16:36-05:00"
}
```

### Search Knowledge Base
```http
GET /api/knowledge/search?query=string&limit=10
```

Response:
```json
{
  "results": [
    {
      "id": "uuid",
      "title": "string",
      "content": "string",
      "relevance_score": 0.95
    }
  ]
}
```

## File Management

### Watch Directory
```http
POST /api/files/watch
Content-Type: application/json

{
  "path": "string",
  "recursive": true,
  "ignore_patterns": ["*.tmp", ".*"]
}
```

Response:
```json
{
  "status": "success",
  "watch_id": "uuid"
}
```

### Get File Status
```http
GET /api/files/status/{watch_id}
```

Response:
```json
{
  "watch_id": "uuid",
  "watched_paths": ["string"],
  "tracked_files": 45,
  "queue_size": 0
}
```

## Metrics

### Get System Metrics
```http
GET /api/metrics
Accept: application/json
```

Response:
```json
{
  "timestamp": "2024-12-07T02:16:36-05:00",
  "metrics": {
    "cpu_usage": {
      "current": 45.2,
      "avg_1m": 42.5,
      "avg_5m": 40.1
    },
    "memory_usage": {
      "current": 62.8,
      "avg_1m": 61.2,
      "avg_5m": 60.5
    },
    "task_metrics": {
      "completed": 150,
      "failed": 2,
      "success_rate": 98.7
    }
  }
}
```

## Plugins

### List Plugins
```http
GET /api/plugins
```

Response:
```json
{
  "plugins": [
    {
      "id": "uuid",
      "name": "string",
      "version": "1.0.0",
      "status": "active",
      "capabilities": ["capability1", "capability2"]
    }
  ]
}
```

### Install Plugin
```http
POST /api/plugins/install
Content-Type: application/json

{
  "name": "string",
  "version": "1.0.0",
  "source": "string"
}
```

Response:
```json
{
  "status": "success",
  "plugin": {
    "id": "uuid",
    "name": "string",
    "version": "1.0.0",
    "status": "installed"
  }
}
```

## Error Handling

All API endpoints follow a consistent error response format:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  }
}
```

Common error codes:
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 429: Too Many Requests
- 500: Internal Server Error

## Rate Limiting

Rate limits are enforced on all endpoints:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1701928596
```

## Versioning

API versioning is handled through the URL:
```http
https://api.jarvis-assistant.com/v1/
```

## Webhooks

### Register Webhook
```http
POST /api/webhooks
Content-Type: application/json

{
  "url": "string",
  "events": ["task.completed", "system.alert"],
  "secret": "string"
}
```

Response:
```json
{
  "id": "uuid",
  "status": "active",
  "created_at": "2024-12-07T02:16:36-05:00"
}
```

Webhook payloads are signed using HMAC-SHA256:
```http
X-Hub-Signature: sha256=hash
```
