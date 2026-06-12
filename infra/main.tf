locals {
  common_tags = {
    Project     = var.project_name
    Owner       = "GregoryCarberry"
    Environment = "lab"
    ManagedBy   = "Terraform"
  }
}
