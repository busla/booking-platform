# Feature Specification: Frontend Cleanup and Consistency

**Feature Branch**: `011-cleanup-shadcn-auth`
**Created**: 2026-01-03
**Status**: Draft
**Input**: User description: "this feature is about alignment, cleanup and consistency. Legacy implementation and deprecated unused code shall be removed. Custom written components shall be replaced with shadcn components where possible. Special attention shall be put into the authentication flow."

## Clarifications

### Session 2026-01-03

- Q: Where should customer profile data (email, phone, name) be stored? → A: ~~Cognito stores email only~~ **UPDATED**: Cognito stores ALL three fields (email, phone, name) for improved UI session attribute rendering and future SMS login support; DynamoDB `customers` table also stores all profile fields for booking queries
- Q: Should "guest" or "customer" terminology be used? → A: Only "customer" shall be used; "guest" is deprecated and must be renamed throughout the codebase
- Q: Is data loss acceptable during DynamoDB table rename? → A: Yes, data loss is acceptable (greenfield project in development phase)
- Q: How to handle duplicate implementations? → A: Before removing any duplicate, VERIFY which implementation is correct (canonical) and which is the one to remove. Never assume - analyze behavior first.
- Q: Should Next.js frontend routes follow App Router best practices? → A: Yes, implement route convention files (`loading.tsx`, `error.tsx`) where beneficial, use route groups for organization (e.g., `(auth)` group), and ensure all inline Suspense fallbacks align with shadcn styling patterns
- Q: Which gallery/lightbox implementation should be kept vs migrated? → A: ~~`/gallery/page.tsx` uses `yet-another-react-lightbox` (KEEP); `PhotoGallery.tsx` (MIGRATE to shadcn Dialog)~~ **UPDATED**: `/gallery/page.tsx` uses `yet-another-react-lightbox` (KEEP); `PhotoGallery.tsx` is DEAD CODE (zero imports anywhere) - DELETE it entirely
- Q: Is PhotoGallery.tsx used on the website? → A: NO - verified zero imports exist; component is dead code and should be removed (not migrated)
- Q: How should DynamoDB table names be referenced across Terraform modules? → A: Table names MUST NEVER be hardcoded; they SHALL be passed as Terraform resource outputs as inputs to consuming modules
- Q: Does this feature require Test-Driven Development (TDD) with tests written before implementation? → A: This is a **refactoring feature** with existing test coverage. Existing tests already cover AuthErrorBoundary, BookingSummaryCard, and auth flows. The approach is: (1) run existing tests to verify baseline, (2) make changes, (3) verify tests still pass. New convention files (loading.tsx, error.tsx) are additive UI and don't require pre-written tests.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Developer Maintains Consistent Codebase (Priority: P1)

A developer working on the booking platform needs to understand and maintain the frontend codebase efficiently. With consistent component patterns, clear naming conventions, and standardized authentication flows, they can make changes confidently without encountering conflicting implementations or dead code paths.

**Why this priority**: Code maintainability directly impacts development velocity and reduces bugs. Inconsistent patterns lead to confusion and errors.

**Independent Test**: Can be fully tested by running the test suite and performing code review to verify no duplicate/conflicting patterns exist. Delivers cleaner, more maintainable codebase.

**Acceptance Scenarios**:

1. **Given** the frontend codebase, **When** a developer searches for authentication-related types, **Then** they find only one `AuthStep` type definition (or clearly differentiated names like `LoginStep` vs `SessionAuthStep`)
2. **Given** the frontend codebase, **When** a developer looks for UI component patterns, **Then** all cards, alerts, badges, and dialogs use shadcn components consistently
3. **Given** the package.json file, **When** reviewing dependencies, **Then** no unused packages remain (e.g., `yet-another-react-lightbox` if unused)
4. **Given** the codebase, **When** a developer searches for entity terminology, **Then** only "customer" is used (no "guest" references except in migration comments)

---

### User Story 2 - Consistent Authentication User Experience (Priority: P1)

A customer authenticating via EMAIL_OTP sees consistent UI components, error messages, and loading states throughout the authentication flow. The experience feels polished and professional regardless of which entry point triggered authentication.

**Why this priority**: Authentication is the gateway to booking functionality. Inconsistent auth UX erodes trust and increases abandonment.

**Independent Test**: Can be fully tested by completing EMAIL_OTP authentication from multiple entry points (login page, customer details form) and verifying consistent UI patterns and error handling.

**Acceptance Scenarios**:

1. **Given** a customer on the login page, **When** they enter an invalid email format, **Then** they see a standardized error message using shadcn Alert component styling
2. **Given** a customer entering OTP verification, **When** the verification code component displays, **Then** it uses consistent styling matching the design system
3. **Given** a customer on the customer details form, **When** authentication is required, **Then** the auth flow matches the standalone login page experience

---

### User Story 3 - Clean Component Library (Priority: P2)

A developer adding new UI features finds a well-organized component library using shadcn primitives consistently. Custom components are only used where shadcn lacks equivalent functionality.

**Why this priority**: Component consistency reduces cognitive load and ensures visual harmony across the application.

**Independent Test**: Can be fully tested by auditing components directory and verifying shadcn usage where appropriate.

**Acceptance Scenarios**:

1. **Given** the AuthErrorBoundary component, **When** rendering an error state, **Then** it uses shadcn Alert component for error display
2. **Given** the BookingSummaryCard component, **When** displaying status badges, **Then** it uses shadcn Badge component with theme-appropriate variants
3. ~~**Given** the PhotoGallery component, **When** opening the lightbox modal, **Then** it uses shadcn Dialog~~ **REMOVED**: PhotoGallery.tsx is dead code (zero imports) - delete entirely instead of migrating

---

### User Story 4 - Removed Dead Code (Priority: P2)

A developer exploring the codebase finds no dead code, unused exports, or deprecated patterns. Every file and export serves a purpose.

**Why this priority**: Dead code creates confusion, increases bundle size, and may introduce security vulnerabilities if left unmaintained.

**Independent Test**: Can be fully tested by running static analysis tools and manual review to confirm no unused exports.

**Acceptance Scenarios**:

1. **Given** the amplify-config.ts file, **When** reviewing exports, **Then** `amplifyAuthServices` and `amplifyFormFields` are removed (or documented if needed for future use)
2. **Given** the package.json dependencies, **When** auditing unused packages, **Then** only truly unused packages are removed (note: `yet-another-react-lightbox` IS used by `/gallery/page.tsx` - do NOT remove)
3. **Given** any component file, **When** searching for TODO or placeholder comments, **Then** placeholder data (like `+34 XXX XXX XXX`) is either replaced with real data or marked with clear documentation

---

### User Story 5 - Standardized Styling Patterns (Priority: P3)

A developer styling new components follows established patterns using the `cn()` utility for conditional classNames and theme-aware color variants instead of hardcoded Tailwind classes.

**Why this priority**: Consistent styling patterns make theming easier and improve code readability.

**Independent Test**: Can be fully tested by code review verifying no hardcoded color strings and consistent use of `cn()` utility.

**Acceptance Scenarios**:

1. **Given** any component with conditional styling, **When** applying variant classes, **Then** it uses the `cn()` utility from class-variance-authority
2. **Given** components with status-dependent colors, **When** determining colors, **Then** they use theme variants (e.g., `destructive`, `secondary`) not hardcoded colors like `bg-red-50`

---

### User Story 6 - Complete Customer Profile Storage (Priority: P1)

A customer completing the details form has all their profile information (email, phone number, name) persisted correctly. Email is used for Cognito authentication, while all profile fields are stored in the DynamoDB `customers` table for booking and communication purposes.

**Why this priority**: Data integrity is critical for bookings - missing phone/name would prevent property manager contact.

**Independent Test**: Can be fully tested by completing registration and verifying all three fields appear in DynamoDB `customers` table.

**Acceptance Scenarios**:

1. **Given** a customer completing the details form, **When** they submit email, phone, and name, **Then** all three fields are persisted to both Cognito user attributes AND DynamoDB `customers` table
2. **Given** a customer authenticating via EMAIL_OTP, **When** authentication succeeds, **Then** Cognito user attributes include all three fields (email, phone_number, name)
3. **Given** an authenticated customer, **When** the UI renders customer info, **Then** profile fields are retrieved from Cognito session attributes (not requiring DynamoDB lookup)

---

### Edge Cases

- What happens when shadcn component behavior differs from current custom behavior?
  - Custom behavior should be evaluated; if essential, document why custom implementation is kept
- How does system handle components that are partially shadcn (mixed patterns)?
  - Fully migrate to shadcn or document the specific reason for custom elements
- What if dead code removal breaks undiscovered functionality?
  - Run full test suite before and after removal; perform manual E2E testing of all user flows
- What happens to existing "guest" data during terminology migration?
  - Delete old `guests` table and create new `customers` table via Terraform; data loss is acceptable (greenfield project)
- How to handle duplicate/conflicting implementations (e.g., two `AuthStep` types)?
  - **CRITICAL**: Before removing duplicates, analyze BOTH implementations to identify which is canonical (correct behavior)
  - Document the analysis: what each implementation does, which tests cover it, which is more widely used
  - Only remove the non-canonical implementation after verification
  - Example: For AuthStep, analyze `useAuthenticatedUser.ts` (session-level) vs `login/page.tsx` (UI flow) - these may BOTH be valid for different purposes

## Requirements *(mandatory)*

### Functional Requirements

**Authentication Flow Consistency:**
- **FR-001**: System MUST have a single, clearly-named type definition for authentication steps (no conflicting `AuthStep` types)
- **FR-002**: System MUST use consistent error message presentation across all authentication entry points
- **FR-003**: System MUST display loading and verification states consistently using shadcn primitives

**Component Standardization:**
- **FR-004**: AuthErrorBoundary component MUST use shadcn Alert component for error display
- **FR-005**: AuthErrorBoundary component MUST use shadcn Button component for retry action
- **FR-006**: BookingSummaryCard component MUST use shadcn Badge component for status indicators
- **FR-008**: All conditional className composition MUST use the `cn()` utility

**Dead Code Removal:**
- **FR-009**: System MUST NOT export unused authentication configuration (`amplifyAuthServices`, `amplifyFormFields`)
- **FR-010**: System MUST NOT include unused npm dependencies
- **FR-011**: System MUST NOT contain placeholder data in production code without clear documentation

**Styling Consistency:**
- **FR-012**: Components MUST NOT use hardcoded color strings (e.g., `bg-red-50`) for status-dependent styling
- **FR-013**: Components MUST use theme-aware variants provided by shadcn

**Customer Data Storage:**
- **FR-014**: Customer Details form MUST persist all profile fields (email, phone, name) to both Cognito and DynamoDB `customers` table
- **FR-015**: Cognito MUST store all three profile fields (email as username, phone_number, name) for session attributes and future SMS login support
- **FR-016**: System MUST retrieve customer profile from Cognito session attributes for UI rendering (faster than DynamoDB lookup)

**Terminology Standardization:**
- **FR-017**: All codebase references to "guest" MUST be renamed to "customer"
- **FR-018**: DynamoDB table `guests` MUST be replaced with new `customers` table (data loss acceptable)
- **FR-019**: Frontend components (e.g., `GuestDetailsForm`) MUST be renamed using "customer" terminology

**Infrastructure Module Dependencies:**
- **FR-024**: DynamoDB table names MUST NOT be hardcoded in consuming Terraform modules; they MUST be passed as outputs from the DynamoDB module
- **FR-025**: Lambda functions and other resources requiring table names MUST receive them via module input variables, not string literals

**Next.js Routing Best Practices:**
- **FR-020**: Auth routes (`/auth/*`) SHOULD be organized under an `(auth)` route group with a shared layout for consistent auth page styling
- **FR-021**: Auth routes MUST have `loading.tsx` convention file(s) using shadcn Skeleton or consistent spinner patterns
- **FR-022**: Auth routes MUST have `error.tsx` convention file(s) using shadcn Alert for error recovery UI
- **FR-023**: Inline Suspense fallback components MUST use shadcn styling patterns (no hardcoded colors like `bg-gray-50`)

### Key Entities

- **shadcn Component**: A pre-built, accessible UI component from the shadcn/ui library that follows Radix UI primitives
- **Authentication Step**: A discrete state in the EMAIL_OTP authentication flow (email entry, OTP verification, success, error)
- **Theme Variant**: A named color scheme option (e.g., `default`, `destructive`, `secondary`) defined by the design system
- **Customer** (formerly "guest"): A person making a booking; profile stored in BOTH Cognito (email, phone_number, name attributes for session/UI) AND DynamoDB (for booking queries/relationships)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero conflicting type definitions for authentication-related state (currently 2, target: 1 unified or 2 clearly differentiated)
- **SC-002**: 100% of error displays in authentication flows use shadcn Alert component
- **SC-003**: Zero unused npm dependencies remain after cleanup (run `npx depcheck` and remove any findings)
- **SC-004**: Zero unused exports remain in authentication configuration files
- **SC-005**: 100% of NEW modal/dialog usage implements shadcn Dialog component (excludes `/gallery/page.tsx` which uses `yet-another-react-lightbox` for advanced lightbox features)
- **SC-006**: 100% of badge/status indicators use shadcn Badge component
- **SC-007**: Zero hardcoded color strings (like `bg-red-50`, `border-blue-500`) in status-dependent conditional styling
- **SC-008**: All test suites pass after refactoring (no regression)
- **SC-009**: Build bundle size does not increase (target: same or smaller due to removed dead code)
- **SC-010**: 100% of customer profile fields (email, phone, name) persisted to both Cognito AND DynamoDB after form submission
- **SC-011**: Zero references to "guest" terminology remain in codebase (excluding migration comments)
- **SC-012**: Auth routes have `loading.tsx` and `error.tsx` convention files using shadcn components
- **SC-013**: Zero hardcoded color strings in Suspense fallback/loading components (e.g., no `bg-gray-50`, `text-gray-500`)
- **SC-014**: Zero hardcoded DynamoDB table name strings in Terraform modules outside the DynamoDB module itself; all references use module outputs

## Assumptions

- shadcn/ui components provide sufficient customization to match current UX without regression
- The `cn()` utility from class-variance-authority is already available in the codebase
- EMAIL_OTP authentication flow core logic remains unchanged; only UI presentation is standardized
- Existing Amplify configuration for runtime authentication continues to work; only unused export code is removed
- The project already has shadcn components installed (Button, Card, Dialog, etc.) based on codebase exploration
- This is a greenfield project in development phase; data loss during DynamoDB table changes is acceptable
- Backend API endpoints referencing "guest" will also be updated to "customer" as part of this feature
