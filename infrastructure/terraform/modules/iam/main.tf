# -----------------------------------------------------------------------------
# IAM Module — IRSA roles for EKS workloads
# Roles: API (S3), Worker (S3 + Bedrock), ECR Pull
# -----------------------------------------------------------------------------

locals {
  name_prefix = "${var.project_name}-${var.environment}"
  oidc_id     = replace(var.eks_oidc_provider_url, "https://", "")
}

# --- API Service Role (S3 access) ---

resource "aws_iam_role" "api" {
  name = "${local.name_prefix}-api-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Federated = var.eks_oidc_provider_arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${local.oidc_id}:aud" = "sts.amazonaws.com"
          "${local.oidc_id}:sub" = "system:serviceaccount:imagineai:imagineai-api"
        }
      }
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "api_s3" {
  name = "${local.name_prefix}-api-s3-policy"
  role = aws_iam_role.api.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [
          var.s3_bucket_arn,
          "${var.s3_bucket_arn}/*"
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GeneratePresignedUrl"]
        Resource = "${var.s3_bucket_arn}/*"
      }
    ]
  })
}

# --- Worker Role (S3 + Bedrock access) ---

resource "aws_iam_role" "worker" {
  name = "${local.name_prefix}-worker-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Federated = var.eks_oidc_provider_arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${local.oidc_id}:aud" = "sts.amazonaws.com"
          "${local.oidc_id}:sub" = "system:serviceaccount:imagineai:imagineai-worker"
        }
      }
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "worker_s3" {
  name = "${local.name_prefix}-worker-s3-policy"
  role = aws_iam_role.worker.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ]
      Resource = [
        var.s3_bucket_arn,
        "${var.s3_bucket_arn}/*"
      ]
    }]
  })
}

resource "aws_iam_role_policy" "worker_bedrock" {
  name = "${local.name_prefix}-worker-bedrock-policy"
  role = aws_iam_role.worker.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ]
      Resource = "arn:aws:bedrock:${var.aws_region}::foundation-model/*"
    }]
  })
}

# --- ECR Pull Role ---

resource "aws_iam_role" "ecr_pull" {
  name = "${local.name_prefix}-ecr-pull-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Federated = var.eks_oidc_provider_arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${local.oidc_id}:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "ecr_pull" {
  name = "${local.name_prefix}-ecr-pull-policy"
  role = aws_iam_role.ecr_pull.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability"
        ]
        Resource = var.ecr_repository_arns
      },
      {
        Effect   = "Allow"
        Action   = ["ecr:GetAuthorizationToken"]
        Resource = "*"
      }
    ]
  })
}
