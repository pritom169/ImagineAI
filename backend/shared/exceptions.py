class ImagineAIError(Exception):
    """Base exception for ImagineAI."""

    def __init__(self, message: str = "An error occurred", status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(ImagineAIError):
    def __init__(self, resource: str = "Resource", resource_id: str = ""):
        detail = f"{resource} not found" if not resource_id else f"{resource} '{resource_id}' not found"
        super().__init__(message=detail, status_code=404)


class AuthenticationError(ImagineAIError):
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message=message, status_code=401)


class AuthorizationError(ImagineAIError):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message=message, status_code=403)


class ConflictError(ImagineAIError):
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message=message, status_code=409)


class ValidationError(ImagineAIError):
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message=message, status_code=422)


class StorageError(ImagineAIError):
    def __init__(self, message: str = "Storage operation failed"):
        super().__init__(message=message, status_code=502)


class ModelInferenceError(ImagineAIError):
    def __init__(self, message: str = "ML model inference failed"):
        super().__init__(message=message, status_code=502)


class ExternalServiceError(ImagineAIError):
    def __init__(self, service: str = "external service", message: str = ""):
        detail = f"{service} error" if not message else f"{service}: {message}"
        super().__init__(message=detail, status_code=502)


class RateLimitExceededError(ImagineAIError):
    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(message="Rate limit exceeded", status_code=429)
