# Data Model: Frontend Cleanup & Test Consolidation

**Feature**: 020-frontend-cleanup
**Date**: 2026-01-06

## Overview

This is a **cleanup feature** - no new data models are introduced.

## Existing Entities Referenced

### 1. verification_codes (DynamoDB)

**Purpose**: Stores OTP codes from Cognito Custom Message trigger for E2E test retrieval

| Attribute | Type | Description |
|-----------|------|-------------|
| email | String (PK) | User email address |
| code | String | 6-digit OTP code |
| ttl | Number | Expiration timestamp (TTL enabled) |

**Usage in Tests**: The `otp-helper.ts` utility reads from this table to retrieve OTP codes programmatically, bypassing email verification friction in E2E tests.

### 2. .auth-state/user.json (Local File)

**Purpose**: Playwright storage state for test session reuse

| Field | Type | Description |
|-------|------|-------------|
| cookies | Array | Browser cookies |
| localStorage | Array | Auth tokens and session data |

**Usage in Tests**: Created by `auth.fixture.ts` after successful authentication. Reused by subsequent tests to avoid re-authenticating.

## No Schema Changes

This feature:
- Does NOT add new database tables
- Does NOT add new DynamoDB attributes
- Does NOT modify API contracts
- Does NOT introduce new entity types

All changes are to test infrastructure and source code cleanup.
