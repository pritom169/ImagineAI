# ImagineAI -- API Reference

**Base URL**: `http://localhost:8000/api/v1`

All endpoints (except registration, login, and health) require a valid JWT
access token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Interactive API docs are available at `http://localhost:8000/docs` (Swagger UI)
and `http://localhost:8000/redoc` (ReDoc) when the application runs in
development mode.

---

## Table of Contents

1. [Authentication](#authentication)
2. [Products](#products)
3. [Uploads](#uploads)
4. [Analysis](#analysis)
5. [Batch Processing](#batch-processing)
6. [Processing Jobs](#processing-jobs)
7. [Dashboard](#dashboard)
8. [WebSocket Events](#websocket-events)
9. [Health Checks](#health-checks)
10. [Error Codes](#error-codes)
11. [Rate Limiting](#rate-limiting)

---

## Authentication

### Register

Create a new user account.

```
POST /api/v1/auth/register
```

**Request body**:

```json
{
  "email": "user@example.com",
  "password": "securepass123",
  "full_name": "Jane Doe"
}
```

**Response** `201 Created`:

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "email": "user@example.com",
  "full_name": "Jane Doe",
  "is_active": true,
  "created_at": "2025-01-15T10:30:00Z"
}
```

**Errors**:
- `409 Conflict` -- A user with this email already exists.
- `422 Unprocessable Entity` -- Validation error (password too short, invalid email).

---

### Login

Authenticate and receive a token pair.

```
POST /api/v1/auth/login
```

**Request body**:

```json
{
  "email": "user@example.com",
  "password": "securepass123"
}
```

**Response** `200 OK`:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Errors**:
- `401 Unauthorized` -- Invalid email or password, or account disabled.

---

### Refresh Token

Exchange a refresh token for a new token pair.

```
POST /api/v1/auth/refresh
```

**Request body**:

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response** `200 OK`:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Errors**:
- `401 Unauthorized` -- Invalid or expired refresh token.

---

### Get Current User

Return the profile of the authenticated user.

```
GET /api/v1/auth/me
```

**Response** `200 OK`:

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "email": "user@example.com",
  "full_name": "Jane Doe",
  "is_active": true,
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

## Products

### List Products

Retrieve a paginated list of the authenticated user's products.

```
GET /api/v1/products
```

**Query parameters**:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `category` | string | -- | Filter by category (e.g., `electronics`, `clothing`) |
| `status` | string | -- | Filter by status (`draft`, `processing`, `active`, `archived`) |
| `search` | string | -- | Full-text search on title and description |
| `page` | int | 1 | Page number (1-indexed) |
| `page_size` | int | 20 | Items per page (1-100) |

**Response** `200 OK`:

```json
{
  "items": [
    {
      "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "title": "Wireless Bluetooth Headphones",
      "description": "Premium over-ear headphones...",
      "category": "electronics",
      "subcategory": "audio",
      "ai_description": null,
      "status": "active",
      "metadata_": {},
      "images": [
        {
          "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
          "s3_key": "products/user-id/product-id/headphones_front.jpg",
          "original_filename": "headphones_front.jpg",
          "content_type": "image/jpeg",
          "file_size_bytes": 2500000,
          "width": 1920,
          "height": 1080,
          "is_primary": true,
          "upload_status": "uploaded",
          "created_at": "2025-01-15T10:30:00Z"
        }
      ],
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

---

### Create Product

```
POST /api/v1/products
```

**Request body**:

```json
{
  "title": "Wireless Bluetooth Headphones",
  "description": "Premium over-ear headphones with ANC.",
  "category": "electronics"
}
```

**Response** `201 Created`: Returns the full `ProductResponse` object.

---

### Get Product

```
GET /api/v1/products/{product_id}
```

**Response** `200 OK`: Returns the full `ProductResponse` object including images.

**Errors**:
- `404 Not Found` -- Product not found or not owned by current user.

---

### Update Product

```
PATCH /api/v1/products/{product_id}
```

**Request body** (all fields optional):

```json
{
  "title": "Updated Title",
  "description": "Updated description.",
  "category": "clothing",
  "status": "active"
}
```

**Response** `200 OK`: Returns the updated `ProductResponse`.

---

### Delete Product

```
DELETE /api/v1/products/{product_id}
```

**Response** `204 No Content`.

Deletes the product and all associated images, analysis results, and attributes
via cascading deletes.

---

### Get Product Analysis

Retrieve all analysis results for a product's images.

```
GET /api/v1/products/{product_id}/analysis
```

**Response** `200 OK`:

```json
[
  {
    "id": "d4e5f6a7-b8c9-0123-defa-234567890123",
    "product_image_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "model_version": "v1.2.0",
    "classification_label": "headphones",
    "classification_confidence": 0.96,
    "classification_scores": {"headphones": 0.96, "other": 0.04},
    "description_text": "Over-ear wireless headphones...",
    "description_model": "anthropic.claude-3-5-sonnet",
    "processing_time_ms": 1250,
    "status": "completed",
    "error_message": null,
    "extracted_attributes": [
      {
        "id": "e5f6a7b8-c9d0-1234-efab-345678901234",
        "attribute_name": "color",
        "attribute_value": "black",
        "confidence": 0.97
      }
    ],
    "detected_defects": [
      {
        "id": "f6a7b8c9-d0e1-2345-fabc-456789012345",
        "defect_type": "scratch",
        "severity": "low",
        "confidence": 0.72,
        "bounding_box": {"x": 120, "y": 85, "width": 45, "height": 12},
        "description": "Minor surface scratch on the spacebar area."
      }
    ],
    "created_at": "2025-01-15T10:35:00Z",
    "updated_at": "2025-01-15T10:35:00Z"
  }
]
```

---

## Uploads

### Get Presigned URL

Generate a presigned S3 URL for client-side upload.

```
POST /api/v1/uploads/presigned-url
```

**Request body**:

```json
{
  "product_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "filename": "photo.jpg",
  "content_type": "image/jpeg",
  "file_size_bytes": 2500000
}
```

**Response** `200 OK`:

```json
{
  "upload_url": "https://s3.amazonaws.com/imagineai-images/...?X-Amz-Signature=...",
  "image_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "s3_key": "products/user-id/product-id/abc123_photo.jpg",
  "expires_in": 3600
}
```

**Workflow**: The client uses the returned `upload_url` to PUT the file directly
to S3, then calls the confirm endpoint.

---

### Confirm Upload

Confirm that the client-side upload to S3 is complete and trigger processing.

```
POST /api/v1/uploads/confirm
```

**Request body**:

```json
{
  "image_id": "c3d4e5f6-a7b8-9012-cdef-123456789012"
}
```

**Response** `200 OK`:

```json
{
  "image_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "job_id": "g7h8i9j0-k1l2-3456-ghij-567890123456",
  "status": "queued",
  "message": "Image processing started"
}
```

---

### Direct Upload

Upload a file directly through the API (server-side upload to S3).

```
POST /api/v1/uploads/direct
```

**Parameters**:
- `product_id` (form field): UUID of the target product.
- `file` (multipart): The image file.

**Constraints**:
- Allowed content types: `image/jpeg`, `image/png`, `image/webp`, `image/gif`.
- Maximum file size: 50 MB.

**Response** `200 OK`:

```json
{
  "image_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "job_id": "g7h8i9j0-k1l2-3456-ghij-567890123456",
  "status": "queued",
  "message": "Image uploaded and processing started"
}
```

---

## Analysis

### Get Analysis Result

Retrieve the analysis result for a specific image.

```
GET /api/v1/analysis/{image_id}
```

**Response** `200 OK`: Returns a full `AnalysisResultResponse` (see schema
under [Get Product Analysis](#get-product-analysis)).

**Errors**:
- `404 Not Found` -- No analysis result for this image, or image not owned by
  current user.

---

### Retry Analysis

Re-queue a failed or completed analysis for reprocessing.

```
POST /api/v1/analysis/{image_id}/retry
```

**Response** `200 OK`:

```json
{
  "job_id": "g7h8i9j0-k1l2-3456-ghij-567890123456",
  "status": "queued",
  "message": "Analysis retry started"
}
```

---

## Batch Processing

### Create Batch Job

Submit multiple images for processing in a single request.

```
POST /api/v1/batch
```

**Request body**:

```json
{
  "product_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "image_ids": [
    "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "d4e5f6a7-b8c9-0123-defa-234567890123",
    "e5f6a7b8-c9d0-1234-efab-345678901234"
  ]
}
```

**Response** `201 Created`:

```json
{
  "id": "g7h8i9j0-k1l2-3456-ghij-567890123456",
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "job_type": "batch",
  "status": "queued",
  "total_images": 3,
  "processed_images": 0,
  "failed_images": 0,
  "celery_task_id": "abc12345-def6-7890-ghij-klmn12345678",
  "started_at": "2025-01-15T10:30:00Z",
  "completed_at": null,
  "error_message": null,
  "steps": [
    {
      "id": "...",
      "step_name": "preprocess",
      "status": "pending",
      "started_at": null,
      "completed_at": null,
      "duration_ms": null,
      "error_message": null,
      "result_data": {}
    }
  ],
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

**Errors**:
- `404 Not Found` -- Product not found or not owned by current user.
- `422 Unprocessable Entity` -- Some image IDs are invalid.

---

### Get Batch Job Status

```
GET /api/v1/batch/{job_id}
```

**Response** `200 OK`: Returns a `ProcessingJobResponse`.

---

### Cancel Batch Job

```
DELETE /api/v1/batch/{job_id}
```

**Response** `204 No Content`.

Revokes the Celery task and marks the job as `cancelled`.

---

## Processing Jobs

### List Jobs

Retrieve the authenticated user's processing jobs.

```
GET /api/v1/jobs
```

**Query parameters**:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `status` | string | -- | Filter by status (`queued`, `processing`, `completed`, `failed`, `cancelled`) |
| `limit` | int | 20 | Max items to return (1-100) |
| `offset` | int | 0 | Number of items to skip |

**Response** `200 OK`:

```json
{
  "items": [ ... ],
  "total": 42
}
```

---

### Get Job Detail

```
GET /api/v1/jobs/{job_id}
```

**Response** `200 OK`: Returns a `ProcessingJobResponse` including all steps.

---

## Dashboard

### Get Statistics

```
GET /api/v1/dashboard/stats
```

**Response** `200 OK`:

```json
{
  "total_products": 10,
  "total_images": 25,
  "completed_analyses": 18,
  "total_defects": 3,
  "active_jobs": 1,
  "avg_processing_time_ms": 1150
}
```

---

### Get Recent Activity

```
GET /api/v1/dashboard/recent
```

**Response** `200 OK`:

```json
[
  {
    "id": "g7h8i9j0-k1l2-3456-ghij-567890123456",
    "job_type": "batch",
    "status": "completed",
    "total_images": 5,
    "processed_images": 5,
    "created_at": "2025-01-15T10:30:00Z",
    "completed_at": "2025-01-15T10:45:00Z"
  }
]
```

---

### Get Category Distribution

```
GET /api/v1/dashboard/category-distribution
```

**Response** `200 OK`:

```json
[
  {"category": "electronics", "count": 3},
  {"category": "clothing", "count": 3},
  {"category": "footwear", "count": 2},
  {"category": "furniture", "count": 2}
]
```

---

## WebSocket Events

### Connection

```
ws://localhost:8000/ws/processing/{job_id}?token=<access_token>
```

The WebSocket connection is authenticated via the `token` query parameter.
The server subscribes to a Redis pub/sub channel for the given job and forwards
messages to the client in real time.

### Close Codes

| Code | Reason |
|---|---|
| `4001` | Invalid or missing token |
| `4003` | Access denied (user does not own the job) |

### Message Format

All messages are JSON-encoded strings:

```json
{
  "type": "step_update",
  "job_id": "g7h8i9j0-k1l2-3456-ghij-567890123456",
  "image_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "step": "classify",
  "status": "completed",
  "progress": {"completed": 2, "total": 5},
  "data": {"classification_label": "headphones", "confidence": 0.96},
  "timestamp": "2025-01-15T10:32:00Z"
}
```

### Event Types

| Type | Description |
|---|---|
| `step_update` | A pipeline step changed status (pending, running, completed, failed) |
| `job_complete` | The entire job finished successfully. Connection closes after this message. |
| `job_failed` | The job failed. Connection closes after this message. |

---

## Health Checks

### Liveness

```
GET /health
```

Returns `200 OK` with `{"status": "healthy"}`. No authentication required.

### Readiness

```
GET /ready
```

Checks database and Redis connectivity. Returns `200 OK` if all dependencies
are reachable, `503 Service Unavailable` otherwise.

```json
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "redis": "ok"
  }
}
```

---

## Error Codes

All error responses follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

| Status Code | Error Type | Description |
|---|---|---|
| `400` | Bad Request | Malformed request body or parameters |
| `401` | Unauthorized | Missing, invalid, or expired authentication token |
| `403` | Forbidden | Insufficient permissions for the requested action |
| `404` | Not Found | Resource does not exist or is not accessible to the user |
| `409` | Conflict | Resource already exists (e.g., duplicate email) |
| `422` | Unprocessable Entity | Request validation failed (Pydantic) |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Unexpected server error |
| `502` | Bad Gateway | External service failure (S3, Bedrock, ML model) |

---

## Rate Limiting

Rate limiting is applied at the infrastructure level (ALB / API Gateway in
production, nginx in local development).

| Tier | Limit |
|---|---|
| Authentication endpoints | 10 requests/minute per IP |
| Upload endpoints | 30 requests/minute per user |
| Analysis / batch endpoints | 60 requests/minute per user |
| Read-only endpoints | 120 requests/minute per user |
| WebSocket connections | 5 concurrent per user |

When rate-limited, the API returns `429 Too Many Requests` with a
`Retry-After` header indicating the number of seconds to wait.
