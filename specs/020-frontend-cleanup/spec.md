# Feature Specification: Frontend Cleanup & Test Consolidation

**Feature Branch**: `020-frontend-cleanup`
**Created**: 2026-01-06
**Status**: Draft
**Input**: User description: "The frontend is spiraling in different directions, has rotten code and duplicate sets of playwright e2e tests, one for localhost and another one for the booking.levy.apro.work live site. Your task is to review the frontend, holistically, clean up and organize it. Then ensure that there are no hacks in the frontend code and that all frontend tests pass"

## Clarifications

### Session 2026-01-06

- Q: How should authentication be handled in E2E tests? → A: Remove all tests using old Cognito password auth hack. Use only the OTP-based approach with Lambda trigger storing OTP in DynamoDB for E2E test retrieval.
- Q: How should placeholder contact phone number be handled? → A: Replace with real phone number: +3547798217

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Developer Runs Tests with Confidence (Priority: P1)

A developer working on the frontend needs to run tests that provide clear, reliable feedback without confusion from duplicate test files, dead code, or failing tests. When they run the test suite, all tests should pass and the test output should be meaningful.

**Why this priority**: Passing tests are the foundation for any further development. Without reliable tests, developers cannot confidently make changes or validate that the cleanup itself hasn't broken functionality.

**Independent Test**: Can be verified by running unit tests and E2E tests - all tests should pass with no skipped debug tests cluttering output.

**Acceptance Scenarios**:

1. **Given** a fresh checkout of the repository, **When** a developer runs unit tests, **Then** all unit tests pass without errors
2. **Given** a fresh checkout of the repository, **When** a developer runs E2E tests for localhost, **Then** all E2E tests pass with the local dev server
3. **Given** a fresh checkout of the repository, **When** a developer runs E2E tests for the live site, **Then** all integration tests pass against booking.levy.apro.work
4. **Given** a test failure occurs, **When** reviewing the test output, **Then** the failure message clearly indicates which feature is broken without noise from debug files

---

### User Story 2 - Codebase Free of Debug Artifacts and Hacks (Priority: P1)

A developer reviewing the codebase should find clean, production-ready code without temporary debugging files, placeholder values, or test-only code paths that pollute the production bundle. This includes removing legacy authentication workarounds.

**Why this priority**: Rotten code creates confusion, increases maintenance burden, and can accidentally ship to production. Clean code is essential for team velocity.

**Independent Test**: Can be verified by code review - no files with "debug" in the name, no hardcoded placeholder values, no legacy password auth test code.

**Acceptance Scenarios**:

1. **Given** the E2E tests directory, **When** listing all spec files, **Then** no files with "debug" prefix exist
2. **Given** the contact page source file, **When** viewing the phone number field, **Then** it displays the real phone number +3547798217 (no "XXX XXX XXX" placeholders)
3. **Given** the source directory, **When** searching for TODO comments, **Then** no TODOs reference incomplete or missing backend features that block functionality
4. **Given** the production build, **When** inspecting the bundle, **Then** no test-only mock mechanisms are included in client code
5. **Given** the auth fixture code, **When** reviewing authentication modes, **Then** no PASSWORD_AUTH or USER_PASSWORD_AUTH flow code exists - only OTP-based authentication via Lambda trigger + DynamoDB retrieval

---

### User Story 3 - Clear Test Organization with No Duplication (Priority: P2)

A developer adding new tests should understand exactly where to put them and what coverage already exists. The test structure should clearly separate localhost tests from live site tests without redundant test coverage.

**Why this priority**: Duplicate tests increase maintenance burden, slow down CI, and create confusion about which test to update when functionality changes.

**Independent Test**: Can be verified by reviewing the test directory structure - each feature should have ONE authoritative test location.

**Acceptance Scenarios**:

1. **Given** the E2E test structure, **When** a developer wants to test booking flows, **Then** there is a clear single location for localhost booking tests and a separate clear location for live integration tests
2. **Given** the auth-related test files, **When** reviewing test coverage, **Then** there is no overlapping test coverage between different auth test files
3. **Given** a new feature to test, **When** a developer looks at the test directory, **Then** the naming convention and directory structure make the correct location obvious

---

### User Story 4 - Maintainable Test Infrastructure (Priority: P3)

A developer maintaining tests should find reusable patterns, shared fixtures, and clear documentation that reduces the effort needed to write and update tests.

**Why this priority**: Good test infrastructure accelerates future development and reduces the likelihood of test rot returning.

**Independent Test**: Can be verified by measuring lines of code in test files - common patterns should be extracted to shared utilities.

**Acceptance Scenarios**:

1. **Given** common UI interactions (calendar selection, OTP input, form submission), **When** writing a new test, **Then** reusable helper functions or page objects exist for these interactions
2. **Given** the authentication fixture, **When** a developer needs to understand authentication testing, **Then** the documentation explains the OTP-based flow using Lambda trigger + DynamoDB retrieval
3. **Given** the test directory, **When** looking for test coverage documentation, **Then** a clear mapping exists showing which features are tested in localhost vs live environments

---

### Edge Cases

- What happens when tests fail intermittently due to timing issues? Tests should have appropriate timeouts and retry logic for flaky network operations.
- How does the system handle auth state tests that depend on expired tokens? Auth fixtures should handle token refresh or re-authentication automatically using OTP flow.
- What happens if the live site (booking.levy.apro.work) is temporarily unavailable? Live tests should have clear skip conditions or graceful failure messages.
- What happens if OTP retrieval from DynamoDB times out? Tests should have appropriate retry logic with clear error messages.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST remove all debug/temporary test files from the test suite
- **FR-002**: System MUST replace placeholder contact phone number (+34 XXX XXX XXX) with real phone number +3547798217
- **FR-003**: System MUST consolidate overlapping auth test files into a coherent test structure with clear separation of concerns
- **FR-004**: System MUST ensure all E2E tests pass for both localhost and live site environments
- **FR-005**: System MUST ensure all unit tests pass
- **FR-006**: System MUST remove or resolve TODO comments that reference incomplete features
- **FR-007**: System MUST document the test organization strategy so future developers understand where to add tests
- **FR-008**: System MUST extract common test patterns into reusable helpers or page objects where duplication exceeds 3 occurrences
- **FR-009**: System MUST ensure test-only mock mechanisms are tree-shaken from production builds or properly documented as test infrastructure
- **FR-010**: System MUST remove all tests and auth fixture code that use Cognito PASSWORD_AUTH (USER_PASSWORD_AUTH flow) - only OTP-based authentication via Lambda trigger + DynamoDB is permitted
- **FR-011**: System MUST remove SSM parameter references for test user passwords from auth fixtures

### Key Entities

- **Test Spec File**: An E2E test file that contains one or more test cases for a specific feature area
- **Test Fixture**: Reusable setup/teardown logic that provides common test prerequisites
- **Test Helper**: Utility functions that encapsulate complex test operations
- **Page Object**: A pattern for organizing selectors and interactions for a specific UI component or page
- **OTP Interceptor**: Lambda trigger that captures Cognito OTP codes and stores them in DynamoDB for E2E test retrieval

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of unit tests pass when running the test suite
- **SC-002**: 100% of E2E localhost tests pass when running against local dev server
- **SC-003**: 100% of E2E live integration tests pass when running against booking.levy.apro.work
- **SC-004**: Zero test files with "debug" prefix remain in the test suite
- **SC-005**: Zero placeholder values (e.g., "XXX XXX XXX") remain in production source code
- **SC-006**: Test file count in auth domain reduced by consolidation (target: 3 files or fewer for auth testing)
- **SC-007**: Common test patterns extracted to shared helpers (target: at least 3 reusable helper functions for calendar, OTP, and form interactions)
- **SC-008**: Test organization documented in a README within the tests directory
- **SC-009**: Zero PASSWORD_AUTH or USER_PASSWORD_AUTH code paths remain in test fixtures or test files

## Assumptions

- The booking.levy.apro.work live site is accessible and functional for running integration tests
- AWS credentials are available for DynamoDB OTP retrieval in integration tests
- The existing test architecture is appropriate and should be maintained
- The dual-environment testing strategy (localhost vs live) is intentional and valuable
- Contact phone number confirmed as +3547798217
- The OTP Lambda trigger infrastructure is already deployed and functional (019-e2e-email-otp feature)
- DynamoDB `verification_codes` table exists with TTL enabled for OTP storage
