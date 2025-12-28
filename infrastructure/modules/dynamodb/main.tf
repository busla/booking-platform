# DynamoDB Tables for Summerhouse
# Defines all tables per data-model.md specification

# Reservations Table
resource "aws_dynamodb_table" "reservations" {
  name         = "${var.name_prefix}-reservations"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "reservation_id"

  attribute {
    name = "reservation_id"
    type = "S"
  }

  attribute {
    name = "guest_id"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  attribute {
    name = "check_in"
    type = "S"
  }

  # GSI for querying by guest with check_in sort
  global_secondary_index {
    name            = "guest-checkin-index"
    hash_key        = "guest_id"
    range_key       = "check_in"
    projection_type = "ALL"
  }

  # GSI for querying by status with check_in sort
  global_secondary_index {
    name            = "status-index"
    hash_key        = "status"
    range_key       = "check_in"
    projection_type = "ALL"
  }

  tags = {
    Table = "reservations"
  }
}

# Guests Table
resource "aws_dynamodb_table" "guests" {
  name         = "${var.name_prefix}-guests"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "guest_id"

  attribute {
    name = "guest_id"
    type = "S"
  }

  attribute {
    name = "email"
    type = "S"
  }

  # GSI for querying by email
  global_secondary_index {
    name            = "email-index"
    hash_key        = "email"
    projection_type = "ALL"
  }

  tags = {
    Table = "guests"
  }
}

# Availability Table
resource "aws_dynamodb_table" "availability" {
  name         = "${var.name_prefix}-availability"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "date"

  attribute {
    name = "date"
    type = "S"
  }

  tags = {
    Table = "availability"
  }
}

# Pricing Table
resource "aws_dynamodb_table" "pricing" {
  name         = "${var.name_prefix}-pricing"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "season_id"

  attribute {
    name = "season_id"
    type = "S"
  }

  tags = {
    Table = "pricing"
  }
}

# Payments Table
resource "aws_dynamodb_table" "payments" {
  name         = "${var.name_prefix}-payments"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "payment_id"

  attribute {
    name = "payment_id"
    type = "S"
  }

  attribute {
    name = "reservation_id"
    type = "S"
  }

  # GSI for querying by reservation
  global_secondary_index {
    name            = "reservation-index"
    hash_key        = "reservation_id"
    projection_type = "ALL"
  }

  tags = {
    Table = "payments"
  }
}

# Verification Codes Table (with TTL)
resource "aws_dynamodb_table" "verification_codes" {
  name         = "${var.name_prefix}-verification-codes"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "email"

  attribute {
    name = "email"
    type = "S"
  }

  # TTL for automatic expiration
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = {
    Table = "verification-codes"
  }
}
