# DynamoDB Module Variables

variable "name_prefix" {
  description = "Prefix for resource names (e.g., summerhouse-dev)"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}
