# Cognito Passwordless Module - Variables
# Uses cloudposse/label/null context pattern - receives context from root module

variable "context" {
  type = any
  default = {
    enabled             = true
    namespace           = null
    tenant              = null
    environment         = null
    stage               = null
    name                = null
    delimiter           = null
    attributes          = []
    tags                = {}
    additional_tag_map  = {}
    regex_replace_chars = null
    label_order         = []
    id_length_limit     = null
    label_key_case      = null
    label_value_case    = null
    descriptor_formats  = {}
    labels_as_tags      = ["unset"]
  }
  description = <<-EOT
    Single object for setting entire context at once.
    See description of individual variables for details.
    Leave string and numeric variables as `null` to use default value.
    Individual variable settings (non-null) override settings in context object,
    except for attributes, tags, and additional_tag_map, which are merged.
  EOT

  validation {
    condition     = lookup(var.context, "label_key_case", null) == null ? true : contains(["lower", "title", "upper"], var.context["label_key_case"])
    error_message = "Allowed values: `lower`, `title`, `upper`."
  }

  validation {
    condition     = lookup(var.context, "label_value_case", null) == null ? true : contains(["lower", "title", "upper", "none"], var.context["label_value_case"])
    error_message = "Allowed values: `lower`, `title`, `upper`, `none`."
  }
}

variable "ses_from_email" {
  description = "Verified SES email address for sending verification codes"
  type        = string
}

variable "verification_table_name" {
  description = "Name of the DynamoDB table for verification codes"
  type        = string
}

variable "verification_table_arn" {
  description = "ARN of the DynamoDB table for verification codes"
  type        = string
}

variable "code_ttl_seconds" {
  description = "Time-to-live for verification codes in seconds"
  type        = number
  default     = 300 # 5 minutes
}

variable "max_attempts" {
  description = "Maximum verification attempts before code expires"
  type        = number
  default     = 3
}

variable "code_length" {
  description = "Length of the verification code"
  type        = number
  default     = 6
}

# -----------------------------------------------------------------------------
# Anonymous/Guest Access Configuration
# -----------------------------------------------------------------------------

variable "anonymous_user_email" {
  description = <<-EOT
    Email address for the shared anonymous user. When set, the custom auth Lambdas
    will auto-succeed for this email (no verification email sent). All anonymous
    visitors authenticate as this single shared user (1 MAU cost).

    The JWT for this user will have email_verified=false, which tools can check
    to distinguish anonymous users from verified users.

    Example: "anonymous@guest.local"
  EOT
  type        = string
  default     = ""
}

