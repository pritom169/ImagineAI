from fastapi import APIRouter

from fastapi_app.api.v1.admin.ab_testing import router as ab_testing_router
from fastapi_app.api.v1.admin.rate_limits import router as rate_limits_router
from fastapi_app.api.v1.analysis import router as analysis_router
from fastapi_app.api.v1.auth import router as auth_router
from fastapi_app.api.v1.batch import router as batch_router
from fastapi_app.api.v1.dashboard import router as dashboard_router
from fastapi_app.api.v1.exports import router as exports_router
from fastapi_app.api.v1.health import router as health_router
from fastapi_app.api.v1.jobs import router as jobs_router
from fastapi_app.api.v1.organizations import router as organizations_router
from fastapi_app.api.v1.products import router as products_router
from fastapi_app.api.v1.uploads import router as uploads_router
from fastapi_app.api.v1.webhooks import router as webhooks_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(organizations_router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(products_router, prefix="/products", tags=["Products"])
api_router.include_router(uploads_router, prefix="/uploads", tags=["Uploads"])
api_router.include_router(analysis_router, prefix="/analysis", tags=["Analysis"])
api_router.include_router(batch_router, prefix="/batch", tags=["Batch Processing"])
api_router.include_router(jobs_router, prefix="/jobs", tags=["Processing Jobs"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(webhooks_router, prefix="/webhooks", tags=["Webhooks"])
api_router.include_router(exports_router, prefix="/exports", tags=["Exports"])
api_router.include_router(ab_testing_router, prefix="/admin/ab-testing", tags=["Admin - A/B Testing"])
api_router.include_router(rate_limits_router, prefix="/admin/rate-limits", tags=["Admin - Rate Limits"])
api_router.include_router(health_router, tags=["Health"])
