variable "aws_region" {
  description = "AWS region for the project."
  type        = string
  default     = "eu-west-2"
}

variable "project_name" {
  description = "Project name used for resource naming."
  type        = string
  default     = "event-driven-order-processing"
}
