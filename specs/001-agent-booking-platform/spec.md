# Feature Specification: Agent-First Vacation Rental Booking Platform

**Feature Branch**: `001-agent-booking-platform`
**Created**: 2025-12-27
**Status**: Draft
**Input**: User description: "AI agent-driven booking platform for vacation rental apartment in Quesada, Alicante. Agent-first design where the chatbot IS the website interface."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Conversational Inquiry Flow (Priority: P1)

A potential guest visits the Booking website and is immediately greeted by an AI agent. Instead of navigating traditional menus, they simply tell the agent what they're looking for: "I want to visit in March with my family of 4." The agent checks availability, shows relevant dates, displays apartment photos when asked, and explains pricing—all through natural conversation. **No sign-up or authentication required.**

**Why this priority**: This is the core value proposition. Without conversational interaction, there is no product. It validates the entire agent-first architecture with frictionless anonymous access.

**Independent Test**: Can be fully tested by having a user ask availability, pricing, and property questions through conversation alone, receiving accurate responses without any authentication.

**Acceptance Scenarios**:

1. **Given** a visitor lands on the website, **When** the page loads, **Then** the AI agent greets them with a welcoming message and invites conversation (no sign-up or authentication required).

2. **Given** a user asks "Do you have availability in March?", **When** the agent processes the request, **Then** it displays available date ranges with pricing information within the conversation.

3. **Given** a user says "What would it cost for March 15-22 for 2 adults and 2 children?", **When** the agent checks pricing, **Then** it presents a price breakdown with nightly rate, cleaning fee, and total.

4. **Given** a user asks "Can I see photos of the apartment?", **When** the agent responds, **Then** it displays a gallery of apartment images within the conversation interface.

5. **Given** a user asks about booking, **When** the agent responds, **Then** it provides contact information or instructions for making a reservation (booking flow deferred to future iteration).

---

### User Story 2 - Availability & Pricing Information (Priority: P2)

A prospective guest wants to explore options before committing. They ask the agent about different time periods, seasonal pricing, minimum stay requirements, and what's included in the rental. The agent provides this information conversationally, helping them find the best dates for their budget and needs.

**Why this priority**: Information gathering precedes booking decisions. Users need to explore options before committing.

**Independent Test**: Can be tested by asking various availability and pricing questions and verifying accurate, helpful responses.

**Acceptance Scenarios**:

1. **Given** a user asks "What are your rates?", **When** the agent responds, **Then** it explains the pricing structure including seasonal variations, cleaning fees, and any deposits.

2. **Given** a user asks "What's the cheapest time to visit?", **When** the agent checks pricing data, **Then** it recommends low-season periods with specific prices.

3. **Given** dates are already booked, **When** a user requests those dates, **Then** the agent explains unavailability and suggests alternative nearby dates.

4. **Given** a user asks about minimum stay, **When** the agent responds, **Then** it explains any minimum night requirements (which may vary by season).

---

### User Story 3 - Area Information & Trip Planning (Priority: P3)

A guest (before or after booking) wants to learn about the Quesada area. They ask the agent about nearby golf courses, beaches, restaurants, supermarkets, and activities for families. The agent provides local knowledge and can help plan their vacation itinerary.

**Why this priority**: Enhances the booking experience and helps guests maximize their stay. Differentiates from generic booking platforms.

**Independent Test**: Can be tested by asking area-related questions and verifying accurate, helpful local information.

**Acceptance Scenarios**:

1. **Given** a user asks "What golf courses are nearby?", **When** the agent responds, **Then** it provides information about local golf courses including names, distances, and key features.

2. **Given** a user asks "What beaches are closest?", **When** the agent responds, **Then** it describes nearby beaches with approximate travel times and characteristics.

3. **Given** a user asks "Can you recommend restaurants?", **When** the agent responds, **Then** it suggests local dining options with brief descriptions.

4. **Given** a user asks "What can we do with kids?", **When** the agent responds, **Then** it recommends family-friendly activities and attractions in the area.

5. **Given** a booked guest asks "Help me plan our week", **When** the agent engages, **Then** it can suggest a day-by-day itinerary based on their interests.

---

### User Story 4 - Apartment Details & Amenities (Priority: P4)

A user wants to understand exactly what the apartment offers before booking. They ask about bedrooms, bathrooms, kitchen facilities, parking, WiFi, pool access, air conditioning, and other amenities. The agent provides detailed information and shows relevant photos.

**Why this priority**: Critical for booking decisions but secondary to the booking flow itself.

**Independent Test**: Can be tested by asking detailed apartment questions and verifying comprehensive, accurate responses.

**Acceptance Scenarios**:

1. **Given** a user asks "How many bedrooms?", **When** the agent responds, **Then** it describes the bedroom configuration with bed types and sleeping capacity.

2. **Given** a user asks "Is there a pool?", **When** the agent responds, **Then** it explains pool access (private or community) with any relevant details.

3. **Given** a user asks "What's in the kitchen?", **When** the agent responds, **Then** it lists kitchen appliances and cookware available.

4. **Given** a user asks to "see the living room", **When** the agent responds, **Then** it displays photos of the living room area.

---

### User Story 5 - Booking Management (Priority: DEFERRED)

> **⚠️ DEFERRED TO FUTURE ITERATION**: This user story requires the reservation feature which is out of scope for MVP.

An existing guest needs to modify or cancel their reservation, or retrieve their booking confirmation. They interact with the agent using their booking reference or email address to access and manage their reservation.

**Why deferred**: Requires reservation/booking capability which is being implemented in a future iteration.

**Acceptance Scenarios** (for future implementation):

1. **Given** a guest provides their booking reference, **When** the agent looks it up, **Then** it displays their reservation details.

2. **Given** a guest wants to modify dates, **When** the new dates are available, **Then** the agent updates the reservation and handles any price difference.

3. **Given** a guest wants to cancel, **When** they confirm cancellation, **Then** the agent processes cancellation according to the cancellation policy and initiates any applicable refund.

4. **Given** a guest asks "Can you resend my confirmation?", **When** verified, **Then** the agent resends the booking confirmation email.

---

### User Story 6 - Static Information Pages (Priority: P6)

A visitor prefers to quickly scan key information without engaging in conversation. They use a navigation menu to access static pages: Pricing, Location, About/Apartment (with photo gallery and amenities), Area Guide, Contact, and FAQ. These pages complement the agent experience for users who want quick visual reference.

**Why this priority**: Provides accessibility for users who prefer traditional browsing, improves SEO, and offers quick reference without conversation overhead. Lower priority than core agent functionality.

**Independent Test**: Can be tested by navigating to each static page and verifying content displays correctly without agent interaction.

**Acceptance Scenarios**:

1. **Given** a visitor lands on the website, **When** they look for navigation, **Then** a navigation menu is visible providing access to all static information pages.

2. **Given** a user clicks "Pricing" in the navigation, **When** the page loads, **Then** they see a pricing table with seasonal rates, minimum stays, and fees.

3. **Given** a user clicks "Location" in the navigation, **When** the page loads, **Then** they see an interactive map showing the apartment location in Quesada.

4. **Given** a user clicks "About" in the navigation, **When** the page loads, **Then** they see apartment details, a photo gallery, and a list of amenities.

5. **Given** a user clicks "Area Guide" in the navigation, **When** the page loads, **Then** they see information about nearby attractions, beaches, golf courses, and restaurants.

6. **Given** a user clicks "FAQ" in the navigation, **When** the page loads, **Then** they see answers to common questions about booking, the apartment, and the area.

7. **Given** a user clicks "Contact" in the navigation, **When** the page loads, **Then** they see contact information and can initiate conversation with the agent.

8. **Given** a user is on any static page, **When** they want to interact with the agent, **Then** the agent is accessible from that page (persistent presence).

---

### Edge Cases

**MVP Scope (Inquiry)**

- What happens when the agent doesn't understand the user's request? (Graceful fallback with clarifying questions)
- What if availability changes during a conversation? (Real-time availability checks on each query)
- How does the agent handle requests in languages other than English? (Multilingual support for at least English and Spanish)
- What happens if the agent takes too long to respond? (Loading indicator, timeout after 30 seconds with retry option)
- What if the availability data is stale? (Backend refreshes cache periodically; agent always queries current state)

**Deferred Edge Cases (Reservation Feature)**

- ~~How does the system handle payment failures?~~ (DEFERRED)
- ~~How are concurrent booking attempts for the same dates handled?~~ (DEFERRED)
- ~~What happens if the user abandons mid-booking?~~ (DEFERRED)
- ~~What happens if the user enters an incorrect verification code?~~ (DEFERRED)
- ~~What happens if the verification code expires?~~ (DEFERRED)
- ~~What if the user's email is already associated with a previous booking?~~ (DEFERRED)
- ~~What happens if email delivery fails?~~ (DEFERRED)
- ~~What if someone attempts to access another guest's booking data via prompt injection?~~ (DEFERRED - MVP has no guest-specific data)

## Requirements *(mandatory)*

### Functional Requirements

**Agent Interaction**

- **FR-001**: System MUST present the AI agent as the primary interface upon page load, with a minimal navigation menu providing access to static information pages
- **FR-002**: Agent MUST respond to natural language queries about availability, pricing, apartment details, and local area
- **FR-003**: Agent MUST be able to display images, calendars, and booking summaries within the conversation flow
- **FR-004**: Agent MUST maintain conversation context throughout a session
- **FR-005**: Agent MUST support at least English and Spanish languages

**Authentication & Access (Anonymous via Cognito Identity Pool)**

- **FR-006**: System MUST use Cognito Identity Pool to grant anonymous (unauthenticated) access to all visitors
- **FR-007**: AgentCore runtime MUST use IAM authentication (not Cognito User Pool JWT)
- **FR-008**: Users MUST NOT be required to sign up or authenticate to interact with the agent
- **FR-009**: All visitors have access to inquiry features: availability, pricing, property info, area info

**Guest Verification (Passwordless) - DEFERRED**

> **⚠️ DEFERRED TO FUTURE ITERATION**: Guest verification is required for the reservation feature which is out of scope for MVP.

- **FR-010**: ~~Agent MUST NOT request guest email until the user confirms intent to proceed with a reservation~~ (DEFERRED)
- **FR-011**: ~~System MUST verify guest identity using email-based passwordless authentication before accepting a reservation~~ (DEFERRED)
- **FR-012**: ~~System MUST send a 6-digit verification code to the guest's email address upon request~~ (DEFERRED)
- **FR-013**: ~~Verification codes MUST expire after 10 minutes~~ (DEFERRED)

**Data Authorization (Session-Bound) - DEFERRED**

> **⚠️ DEFERRED TO FUTURE ITERATION**: Session-bound data authorization is required for the reservation feature.

- **FR-039**: ~~System MUST automatically inject authenticated `guest_id` from Cognito session into tool execution context~~ (DEFERRED)
- **FR-040**: ~~Tools accessing guest-specific data MUST filter results to only return data owned by the session's `guest_id`~~ (DEFERRED)
- **FR-041**: For MVP, all data accessed is public (availability, pricing, property info, area info) - no guest-specific data

**Type Safety & Data Contracts**

- **FR-043**: All backend data models MUST use Pydantic v2 BaseModel with `model_config = ConfigDict(strict=True)` (Pydantic v1 `class Config:` syntax is prohibited)
- **FR-044**: All tool input parameters and return values MUST be typed using Pydantic v2 models (no raw dicts for domain data)
- **FR-045**: All API request/response bodies MUST be defined as Pydantic v2 models with strict validation
- **FR-046**: DynamoDB item serialization/deserialization MUST use Pydantic v2 models with `model_dump()` and `model_validate()` methods
- **FR-047**: Frontend MUST use TypeScript strict mode (`"strict": true` in tsconfig.json)
- **FR-048**: Shared data contracts between frontend and backend MUST be generated from Pydantic models (e.g., via pydantic-to-typescript or OpenAPI)

**Availability & Pricing Inquiry (MVP Scope)**

- **FR-014**: System MUST allow users to check availability for specific date ranges
- **FR-015**: System MUST calculate and display price estimates including base rate, cleaning fee, and seasonal adjustments
- **FR-016**: System MUST display availability calendar within conversation

**Booking & Reservations - DEFERRED**

> **⚠️ DEFERRED TO FUTURE ITERATION**: Reservation creation is out of scope for MVP.

- **FR-017**: ~~System MUST allow users to make reservations through conversation with the agent~~ (DEFERRED)
- **FR-018**: ~~System MUST collect guest information (name, email, phone, number of guests) during booking~~ (DEFERRED)
- **FR-019**: ~~System MUST prevent double-booking of overlapping dates~~ (DEFERRED)
- **FR-020**: ~~System MUST send booking confirmation via email upon successful payment~~ (DEFERRED)

**Payment Processing - DEFERRED**

> **⚠️ DEFERRED TO FUTURE ITERATION**: Payment processing is out of scope for MVP.

- **FR-021**: ~~System MUST process payments through conversation flow~~ (DEFERRED)
- **FR-022**: ~~System MUST support payment processing through a pluggable interface~~ (DEFERRED)
- **FR-023**: ~~System MUST handle payment failures gracefully with clear messaging~~ (DEFERRED)

**Booking Management - DEFERRED**

> **⚠️ DEFERRED TO FUTURE ITERATION**: Booking management requires reservation feature.

- **FR-024**: ~~System MUST allow guests to retrieve booking details using reference number or email~~ (DEFERRED)
- **FR-025**: ~~System MUST allow booking modifications when new dates are available~~ (DEFERRED)
- **FR-026**: ~~System MUST process cancellations according to defined cancellation policy~~ (DEFERRED)

**Content & Information**

- **FR-027**: Agent MUST provide accurate apartment details (bedrooms, bathrooms, amenities, capacity)
- **FR-028**: Agent MUST provide local area information (golf, beaches, restaurants, activities)
- **FR-029**: Agent MUST display apartment photos on request
- **FR-030**: System MUST maintain up-to-date pricing and availability data

**Static Pages & Navigation**

- **FR-031**: System MUST provide a navigation menu visible on all pages
- **FR-032**: System MUST include a Pricing page displaying seasonal rates, minimum stays, and fees in table format
- **FR-033**: System MUST include a Location page with an interactive map showing the apartment in Quesada
- **FR-034**: System MUST include an About/Apartment page with photo gallery, amenities list, and apartment details
- **FR-035**: System MUST include an Area Guide page with information about nearby attractions, beaches, golf, and dining
- **FR-036**: System MUST include an FAQ page with common questions and answers about booking, the apartment, and the area
- **FR-037**: System MUST include a Contact page with owner contact information
- **FR-038**: Agent MUST remain accessible from all static pages (persistent presence)
- **FR-100**: Static pages MUST share consistent styling with the main agent interface

**Data Retention & Privacy**

- **FR-101**: Conversation logs MUST be retained for 90 days for support/debugging, then anonymized or deleted
- **FR-102**: No personal guest data is collected in MVP (anonymous access); data retention requirements deferred to reservation feature

### Key Entities

**MVP Scope (Inquiry Only)**

- **Availability**: Calendar data showing which dates are available or blocked. Contains date, status (available/booked/blocked).

- **Pricing**: Rate configuration. Contains season name, date range, nightly rate, minimum stay requirement, cleaning fee. Multiple Pricing periods cover the full year.

- **Apartment**: The rental property. Contains description, photos, amenities list, address, capacity, bedroom/bathroom configuration.

- **AreaInfo**: Local area knowledge. Contains category (golf, beach, restaurant, activity), name, description, distance/location, and any relevant details.

- **Conversation**: A chat session with an anonymous user. Contains messages and timestamp.

**Deferred Entities (Reservation Feature)**

- **Reservation** (DEFERRED): A booking made by a guest. Contains check-in date, check-out date, guest count, total price, status, and payment status.

- **Guest** (DEFERRED): A person making a reservation. Contains name, email (verified), phone, preferred language.

- **Payment** (DEFERRED): Financial transaction for a Reservation. Contains amount, status, payment method, transaction reference.

## Clarifications

### Session 2025-12-27

- Q: What authentication model should be used for AgentCore runtime? → A: **IAM authentication via Cognito Identity Pool**. AgentCore runtime uses IAM (not Cognito User Pool JWT). Cognito Identity Pool grants **anonymous (unauthenticated) access** to all visitors. Users are NOT required to sign up or authenticate to interact with the agent. This enables frictionless conversation for all visitors.
- Q: Is the reservation/booking feature in scope for MVP? → A: **No, out of scope**. Reservation, payment processing, booking management, and guest verification features are deferred to a future iteration. MVP focuses on conversational inquiry: availability checks, pricing information, property details, and area information. No booking commitment required.
- Q: Should static pages be added for basic info? → A: Yes, add navigation menu with Pricing, Location, and Contact pages
- Q: Which additional static pages should be included? → A: All options - About/Apartment (photos + amenities), Area Guide, and FAQ
- Q: How should guest identity be verified? → A: ~~Passwordless flow using AWS Cognito custom challenge~~ **SUPERSEDED**: MVP uses anonymous access via Cognito Identity Pool. Guest verification deferred to reservation feature.
- Q: Should tools be implemented as Strands native tools or AgentCore Gateway Lambda targets? → A: Strands native tools using @tool decorator. Tools are defined as Python functions with docstrings and type hints; schemas auto-generate from code. No separate schema files needed (deleted mcp-tools.json). Tool interfaces documented in agent-tools.json. Gateway + Lambda pattern reserved for future external service integrations (payment providers, email services).
- Q: How do we guarantee the agent retrieves only the current customer's data, not another guest's? → A: ~~Session-bound guest_id injection~~ **SUPERSEDED**: MVP has no guest-specific data (anonymous access only). All data is public (availability, pricing, property info). Guest-specific data authorization deferred to reservation feature.
- Q: How should type safety be enforced for data contracts? → A: Pydantic v2 strict mode EVERYWHERE. All backend data models, tool inputs/outputs, API request/response schemas, and DynamoDB item serialization must use Pydantic v2 BaseModel with `model_config = ConfigDict(strict=True)`. Frontend uses TypeScript strict mode. No untyped dictionaries for domain data. Pydantic v1 syntax (`class Config:`) is NOT permitted.
- Q: Does terraform-aws-agentcore already support passwordless Cognito auth? → A: ~~cognito-passwordless module needed~~ **SUPERSEDED**: MVP uses Cognito Identity Pool for anonymous access, not User Pool with custom auth. Passwordless auth deferred to reservation feature.
- Q: Where should the Cognito custom auth Lambda functions live? → A: ~~Lambda functions in cognito-passwordless module~~ **SUPERSEDED**: No custom auth Lambda functions needed for MVP. Anonymous access via Identity Pool.
- Q: How should Terraform backend be configured per environment? → A: Each `infrastructure/environments/` directory shall have a Terraform backend config file to pin deployments to an AWS_PROFILE. For **dev**: `profile = "apro-sandbox"`, `allowed_account_ids = ["195275641848"]`. Prod configuration to be defined separately.
- Q: How should Terraform commands be executed? → A: All Terraform commands MUST be run via `Taskfile.yaml` in the repo root (adapted from template). **NEVER run terraform commands manually** (e.g., `terraform plan`, `terraform apply`). Use syntax `task tf:<action>:<env>` (e.g., `task tf:plan:dev`, `task tf:apply:prod`). The Taskfile handles environment selection, backend config, and consistent execution.
- Q: What package manager and deployment strategy for the frontend? → A: Frontend MUST use **Yarn Berry** with `nodeLinker: node-modules` (not PnP). Deployed to **S3 behind CloudFront** via a new `static-website` module in `terraform-aws-agentcore/modules/`. The module MUST use **terraform-aws-modules** (community modules) for all resources (S3, CloudFront, IAM). **Always use latest stable versions** of terraform-aws-modules (e.g., `source = "terraform-aws-modules/cloudfront/aws"`, `version = "6.0.2"`).
- Q: How should frontend build and deployment be orchestrated? → A: **All operations MUST stay within the Terraform domain**—no external CLI commands (e.g., manual `aws s3 sync`, `yarn build`). Use `terraform_data` resource with `local-exec` provisioner to build the frontend and sync to S3. **CloudFront invalidation is NEVER required**: Next.js build MUST export artifacts with **content-hash filenames** (e.g., `main-abc123.js`), ensuring cache-busting via filename changes rather than invalidation API calls. Configure aggressive CloudFront caching with long TTLs since filenames change when content changes.
- Q: What structured logging format should be used? → A: Use **Strands and AgentCore default logging formats**—no custom log schema required. AgentCore provides built-in structured logging to CloudWatch with trace IDs, timestamps, and request context. Backend Python code uses standard `logging` module with JSON formatter for consistency. Log levels: DEBUG (development), INFO (production), ERROR (always).
- Q: What email templates should be used? → A: **Two email types required**: (1) **Verification code email**: Plain text via SES with 6-digit code, sent by cognito-passwordless Lambda trigger. Subject: "Your Booking verification code". (2) **Booking confirmation email**: HTML template with reservation details, dates, price breakdown, property address, and check-in instructions. Use SES templates stored in Terraform config. Both emails MUST include "Booking" branding in sender name.
- Q: How should we proceed with infrastructure given the module dependencies? → A: **Inline modules locally**. Implement cognito-passwordless and static-website directly in Booking's `infrastructure/modules/` directory (not in terraform-aws-agentcore). This unblocks infrastructure immediately. Modules can be extracted to a shared repo later if needed.
- Q: Which AWS region should infrastructure resources be deployed to? → A: **eu-west-1 (Ireland)**. All resources (DynamoDB, Cognito, backend, CloudFront origin) deploy to eu-west-1 for EU data residency (GDPR compliance for Spanish property). Claude Sonnet is available in this region. State storage also in eu-west-1.
- Q: What backend deployment strategy should we use for the Strands agent? → A: **AgentCore Runtime** via the existing `terraform-aws-agentcore` module. Module location: `~/code/apro/agentcore-sandbox/terraform-aws-agentcore`. Reference implementation: `~/code/apro/agentcore-sandbox/terraform/workspaces/sandbox`. This is a production-ready custom module.
- Q: How should the SSL certificate be handled? → A: **Use existing wildcard cert**. Reference existing `*.levy.apro.work` ACM certificate in us-east-1 via data lookup or ARN. CloudFront requires certs in us-east-1 for custom domains. No new cert creation needed.
- Q: What SES sender email should be used? → A: `noreply@levy.apro.work`. Domain must be verified in SES (eu-west-1). Used for verification codes and booking confirmation emails.

### Session 2025-12-28

- Q: What is the scope of Cognito Identity Pool implementation for MVP? → A: **Hybrid approach** - Deploy both Identity Pool (for anonymous access) and User Pool (stubbed for future authenticated flows). Identity Pool grants unauthenticated credentials to all visitors for AgentCore invocation. User Pool is deployed but unused in MVP, ready for reservation feature.
- Q: How should AgentCore runtime authenticate incoming requests from the frontend? → A: **SigV4 signing** - Frontend uses AWS SDK (`@aws-sdk/client-cognito-identity` + `@aws-sdk/credential-providers`) to obtain temporary credentials from Identity Pool, then signs HTTP requests to AgentCore using SigV4. AgentCore runtime validates the IAM signature. No JWT tokens involved.

## Assumptions

- The property is a single apartment (not multiple units) in Quesada, Alicante
- Pricing follows seasonal patterns typical for Costa Blanca vacation rentals
- **Cancellation policy**: Free cancellation up to 14 days before check-in; 50% refund 7-14 days before; no refund under 7 days
- **Minimum stay requirements**: 7 nights in high season (Jul-Aug, Christmas/New Year), 3 nights otherwise
- **Check-in/check-out times**: Check-in 3 PM, check-out 10 AM
- Area information will be curated/maintained by the property owner
- Payment processing will use a mocked interface initially; real provider (e.g., Stripe) to be integrated in a future iteration

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete a full booking (from landing to payment confirmation) in under 5 minutes through conversation
- **SC-002**: 80% of users who start a booking conversation successfully complete the reservation *(Measurement: conversation events tracked via AgentCore observability; "start booking" = user asks about availability/dates; "complete" = confirmed reservation)*
- **SC-003**: Agent responds to user queries within 3 seconds
- **SC-004**: System achieves 99.9% accuracy in availability information (no false availability shown)
- **SC-005**: 90% of user questions are answered without requiring human intervention
- **SC-006**: Zero double-bookings occur
- **SC-007**: 85% of users rate the booking experience as "easy" or "very easy" *(Measurement: optional post-booking feedback prompt in confirmation email; deferred to post-MVP)*
- **SC-008**: System handles 100 concurrent conversations without degradation
- **SC-009**: Booking confirmation emails delivered within 1 minute of payment completion
- **SC-010**: Guest can retrieve and manage existing bookings within 2 minutes through conversation
