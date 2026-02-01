import enum


class ProductStatus(str, enum.Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    ACTIVE = "active"
    ARCHIVED = "archived"


class ProductCategory(str, enum.Enum):
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    FOOTWEAR = "footwear"
    FURNITURE = "furniture"
    JEWELRY = "jewelry"
    TOYS = "toys"
    SPORTS = "sports"
    HOME_GARDEN = "home_garden"
    AUTOMOTIVE = "automotive"
    BOOKS = "books"
    OTHER = "other"


class UploadStatus(str, enum.Enum):
    PENDING = "pending"
    UPLOADED = "uploaded"
    FAILED = "failed"


class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, enum.Enum):
    SINGLE = "single"
    BATCH = "batch"


class StepName(str, enum.Enum):
    PREPROCESS = "preprocess"
    CLASSIFY = "classify"
    EXTRACT_ATTRIBUTES = "extract_attributes"
    DETECT_DEFECTS = "detect_defects"
    GENERATE_DESCRIPTION = "generate_description"


class StepStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class DefectSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DefectType(str, enum.Enum):
    SCRATCH = "scratch"
    DENT = "dent"
    MISSING_PART = "missing_part"
    DISCOLORATION = "discoloration"
    STAIN = "stain"
    CRACK = "crack"
    TEAR = "tear"
    OTHER = "other"


class AttributeName(str, enum.Enum):
    COLOR = "color"
    MATERIAL = "material"
    BRAND = "brand"
    CONDITION = "condition"
    PATTERN = "pattern"
    STYLE = "style"


class OrgRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class OrgPlan(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class WebhookEvent(str, enum.Enum):
    JOB_COMPLETED = "job.completed"
    JOB_FAILED = "job.failed"
    ANALYSIS_COMPLETED = "analysis.completed"
    ANALYSIS_FAILED = "analysis.failed"
    BATCH_COMPLETED = "batch.completed"
    PRODUCT_CREATED = "product.created"
    PRODUCT_UPDATED = "product.updated"


class ExportType(str, enum.Enum):
    ANALYSIS_CSV = "analysis_csv"
    ANALYSIS_PDF = "analysis_pdf"
    PRODUCTS_CSV = "products_csv"


class ExportStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
