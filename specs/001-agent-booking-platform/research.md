# Research: Agent-First Vacation Rental Booking Platform

**Feature**: 001-agent-booking-platform
**Date**: 2025-12-27
**Status**: Complete

## Executive Summary

This document consolidates research findings for the Agent-First Vacation Rental Booking Platform. Four key technology areas were investigated to inform the implementation plan:

1. **Vercel AI SDK v6** - Frontend conversation UI framework
2. **Strands Agent Framework** - Backend agent orchestration
3. **terraform-aws-agentcore Module** - Infrastructure provisioning
4. **AWS Cognito Custom Challenge** - Passwordless authentication

All technologies align with the constitution's mandated stack (Principle VI) and support the feature requirements defined in spec.md.

---

## 1. Vercel AI SDK v6 (Frontend)

### Overview

The Vercel AI SDK (`ai` package) provides React hooks and streaming utilities for building conversational AI interfaces. Version 6 introduces improved agent support, tool calling, and streaming patterns.

### Key Findings

#### Installation & Setup

```bash
npm install ai @ai-sdk/openai  # or custom provider
```

#### Core Hooks for Chat Interface

```typescript
// app/components/ChatInterface.tsx
import { useChat } from 'ai/react';

export function ChatInterface() {
  const {
    messages,
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    error
  } = useChat({
    api: '/api/chat',
    onError: (error) => console.error('Chat error:', error),
  });

  return (
    <div className="flex flex-col h-screen">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div className={`max-w-xs px-4 py-2 rounded-lg ${
              message.role === 'user'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 text-black'
            }`}>
              {message.content}
            </div>
          </div>
        ))}
        {isLoading && <div className="text-gray-500">Thinking...</div>}
      </div>

      <form onSubmit={handleSubmit} className="p-4 border-t">
        <input
          value={input}
          onChange={handleInputChange}
          placeholder="Ask about the apartment..."
          className="w-full p-2 border rounded"
        />
      </form>
    </div>
  );
}
```

#### Custom Provider for Strands Backend

```typescript
// lib/strands-provider.ts
import { LanguageModel, streamText } from 'ai';

export class StrandsAgent implements LanguageModel {
  modelId = 'strands-booking-agent';
  provider = 'strands';
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async doGenerate(params: any) {
    const response = await fetch(`${this.baseUrl}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: params.messages,
        tools: params.tools,
      }),
    });

    return {
      text: await response.text(),
      rawCall: { raw: response },
      finishReason: 'stop',
      usage: { promptTokens: 0, completionTokens: 0 },
    };
  }

  async doStream(params: any) {
    const response = await fetch(`${this.baseUrl}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: params.messages,
        tools: params.tools,
      }),
    });

    return {
      stream: response.body!,
      rawCall: { raw: response },
    };
  }
}
```

#### API Route (Next.js App Router)

```typescript
// app/api/chat/route.ts
import { streamText } from 'ai';
import { StrandsAgent } from '@/lib/strands-provider';

export const POST = async (req: Request) => {
  const { messages } = await req.json();

  const result = streamText({
    model: new StrandsAgent(process.env.STRANDS_API_ENDPOINT!),
    system: 'You are a vacation rental booking assistant...',
    messages,
  });

  return result.toDataStreamResponse();
};
```

#### Rich Content Rendering

For displaying booking summaries, calendars, and photo galleries within the conversation:

```typescript
// lib/rich-content.ts
export interface BookingSummary {
  type: 'booking-summary';
  property: { id: string; name: string; image: string; price: number };
  dates: { checkIn: string; checkOut: string; nights: number };
  total: number;
}

export interface CalendarBlock {
  type: 'calendar';
  month: string;
  year: number;
  availability: Record<number, boolean>;
}

// components/agent/RichContentRenderer.tsx
export function RichContentRenderer({ content }: { content: string }) {
  try {
    const parsed = JSON.parse(content);

    if (parsed.type === 'booking-summary') return <BookingSummaryCard data={parsed} />;
    if (parsed.type === 'calendar') return <CalendarBlock data={parsed} />;
    if (parsed.type === 'photo-gallery') return <PhotoGallery data={parsed} />;
  } catch {
    return <p>{content}</p>;
  }
}
```

### Implications for Implementation

- Use `useChat` hook for main conversation interface
- Create custom `StrandsAgent` provider to connect to backend
- Implement `RichContentRenderer` for structured responses (FR-003)
- AI SDK handles streaming automatically (SC-003 performance)

---

## 2. Strands Agent Framework (Backend)

### Overview

Strands is a Python framework for building AI agents with tool calling, conversation management, and deployment to AWS AgentCore Runtime.

### Key Findings

#### Tool Definition Pattern

```python
from strands import tool
from pydantic import BaseModel, ConfigDict
from datetime import date

# Pydantic v2 input/output models (strict=True required per FR-043/FR-044)
class CheckAvailabilityInput(BaseModel):
    model_config = ConfigDict(strict=True)
    check_in: date
    check_out: date

class CheckAvailabilityResult(BaseModel):
    model_config = ConfigDict(strict=True)
    available: bool
    dates: str

class CreateReservationInput(BaseModel):
    model_config = ConfigDict(strict=True)
    guest_email: str
    check_in: date
    check_out: date
    num_guests: int

class CreateReservationResult(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str
    reservation_id: str
    confirmation_sent: bool

class GetPricingInput(BaseModel):
    model_config = ConfigDict(strict=True)
    check_in: date
    check_out: date

class GetPricingResult(BaseModel):
    model_config = ConfigDict(strict=True)
    nightly_rate: int
    nights: int
    base_price: int
    cleaning_fee: int
    total: int

@tool
def check_availability(input: CheckAvailabilityInput) -> CheckAvailabilityResult:
    """Check property availability for a date range.

    Args:
        input: Check-in and check-out dates
    """
    # Query DynamoDB availability table
    return CheckAvailabilityResult(
        available=True,
        dates=f"{input.check_in} to {input.check_out}",
    )

@tool
def create_reservation(input: CreateReservationInput) -> CreateReservationResult:
    """Create a new reservation.

    Args:
        input: Reservation details including guest email and dates
    """
    reservation_id = generate_reservation_id()
    # Store in DynamoDB
    return CreateReservationResult(
        status="success",
        reservation_id=reservation_id,
        confirmation_sent=True
    )

@tool
def get_pricing(input: GetPricingInput) -> GetPricingResult:
    """Calculate total pricing for a stay.

    Args:
        input: Check-in and check-out dates for pricing calculation
    """
    # Calculate based on seasonal rates
    return GetPricingResult(
        nightly_rate=150,
        nights=7,
        base_price=1050,
        cleaning_fee=75,
        total=1125
    )
```

#### Agent Definition

```python
from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager

# Tool imports
from tools.availability import check_availability, get_calendar
from tools.pricing import get_pricing, calculate_total
from tools.reservations import create_reservation, get_reservation, cancel_reservation
from tools.payments import process_payment
from tools.property import get_property_details, get_photos
from tools.area_info import get_area_info
from tools.guest import verify_guest, get_guest_info

# Organize tools by category
all_tools = [
    check_availability, get_calendar,
    get_pricing, calculate_total,
    create_reservation, get_reservation, cancel_reservation,
    process_payment,
    get_property_details, get_photos,
    get_area_info,
    verify_guest, get_guest_info,
]

conversation_manager = SlidingWindowConversationManager(
    window_size=40,
    should_truncate_results=True
)

booking_agent = Agent(
    tools=all_tools,
    name="SummerhouseBookingAgent",
    conversation_manager=conversation_manager,
    system_prompt="""You are the booking assistant for Summerhouse, a vacation rental
    apartment in Quesada, Alicante, Spain. You help guests check availability,
    understand pricing, learn about the property and area, and complete bookings.

    Be warm and helpful. When a guest wants to book, only ask for their email
    when they confirm intent to proceed with a reservation. Use the verification
    tools to validate their identity before finalizing bookings.

    You can display images, calendars, and booking summaries within the conversation."""
)
```

#### AgentCore Runtime Deployment

```python
# agent_app.py
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from agent.booking_agent import booking_agent

app = BedrockAgentCoreApp()

@app.entrypoint
async def invoke(payload):
    """Handle agent invocations."""
    prompt = payload.get("prompt", "")
    session_id = payload.get("session_id")

    if not prompt:
        return {"error": "No prompt provided"}

    result = booking_agent(prompt)

    return {
        "result": result.message,
        "session_id": session_id,
        "success": True
    }

if __name__ == "__main__":
    app.run()
```

#### Session Management

```python
from strands import Agent
from strands.session.s3_session_manager import S3SessionManager

session_manager = S3SessionManager(
    session_id=f"guest-{guest_id}",
    bucket="summerhouse-sessions",
    prefix="conversations/",
    region_name="eu-west-1"
)

agent = Agent(
    tools=all_tools,
    session_manager=session_manager
)
```

### Tool Categories for Summerhouse

| Category | Tools | Spec Requirements |
|----------|-------|-------------------|
| Availability | `check_availability`, `get_calendar` | FR-014, US1, US2 |
| Pricing | `get_pricing`, `calculate_total` | FR-017, US2 |
| Reservations | `create_reservation`, `get_reservation`, `cancel_reservation`, `modify_reservation` | FR-015-019, FR-023-025 |
| Payments | `process_payment` (mocked) | FR-020-022 |
| Property | `get_property_details`, `get_photos` | FR-026, FR-028, US4 |
| Area Info | `get_area_info`, `get_recommendations` | FR-027, US3 |
| Guest | `verify_guest`, `get_guest_info`, `send_verification_code` | FR-006-013 |

### Implications for Implementation

- Use `@tool` decorator with comprehensive docstrings
- Organize tools by category for maintainability
- Implement `SlidingWindowConversationManager` for context management
- Deploy via `BedrockAgentCoreApp` to AgentCore Runtime

---

## 3. terraform-aws-agentcore Module (Infrastructure)

### Overview

The `terraform-aws-agentcore` module at `~/code/apro/agentcore-sandbox/terraform-aws-agentcore` provisions complete AgentCore infrastructure in 5 layers.

### Key Findings

#### Module Architecture

| Layer | Components |
|-------|------------|
| 0 - Foundation | Cognito User Pool, Identity Pool, SSM Parameters |
| 1 - Dependencies | Lambda Layer S3 Bucket |
| 2 - Build | ECR Repositories, Lambda Functions |
| 3 - AgentCore | Runtime, Gateway, Memory |
| 3.5 - OAuth | OAuth Callback Lambda, Interceptor |
| 4 - Extensions | Identity providers, Tools, Observability |
| 5 - IAM | Policy Attachments |

#### ⚠️ Gap: Passwordless Auth Module Required

The existing `cognito-user-pool` module in terraform-aws-agentcore (`modules/cognito-user-pool/`) only supports basic user pool configuration. It does **NOT** support:

- Custom auth challenge Lambda triggers
- `ALLOW_CUSTOM_AUTH` in ExplicitAuthFlows
- Lambda trigger configuration for DefineAuthChallenge, CreateAuthChallenge, VerifyAuthChallengeResponse

**Action Required**: A new `cognito-passwordless` module MUST be created and added to `terraform-aws-agentcore/modules/` before Summerhouse implementation. This module will provide:

1. **Cognito User Pool** with custom auth enabled
2. **Three Lambda Functions** (source code bundled inside module, NOT in consumer projects):
   - `define-auth-challenge` - Determines challenge flow
   - `create-auth-challenge` - Generates and sends 6-digit code via SES
   - `verify-auth-challenge` - Validates user-provided code
3. **SES Configuration** - Email sending for verification codes
4. **IAM Roles** - Lambda execution roles with SES permissions

**Module self-containment**: Consumer projects (like Summerhouse) do NOT provide Lambda code. They only configure business rules (SES email, code TTL, email templates). This makes the module reusable across multiple projects.

#### Minimal Configuration for Summerhouse

```hcl
# infrastructure/main.tf

# 1. Passwordless Auth (uses NEW cognito-passwordless module - to be created)
# NOTE: Lambda functions are bundled INSIDE the module, not in consumer projects
module "cognito_passwordless" {
  source = "~/code/apro/agentcore-sandbox/terraform-aws-agentcore/modules/cognito-passwordless"

  namespace   = "summerhouse"
  environment = var.environment
  name        = "auth"

  # User Pool Configuration
  auto_verified_attributes = ["email"]

  # SES Configuration (module handles Lambda triggers internally)
  ses_from_email      = "noreply@summerhouse.example.com"
  ses_verified_domain = "summerhouse.example.com"

  # Email template customization (optional)
  email_subject = "Your Summerhouse Booking Verification Code"
  email_body    = "Your verification code is: {code}. This code expires in {ttl} minutes."

  # Code expiration policy
  verification_code_ttl_minutes = 10
  max_verification_attempts     = 3
}

# 2. AgentCore Infrastructure
module "agentcore" {
  source = "~/code/apro/agentcore-sandbox/terraform-aws-agentcore"

  namespace   = "summerhouse"
  environment = var.environment
  name        = "booking-agent"

  # Reference the passwordless Cognito resources
  cognito_user_pool_id = module.cognito_passwordless.user_pool_id
  cognito_user_pool_client_id = module.cognito_passwordless.user_pool_client_id

  # Memory for Conversation State
  memory = {
    event_expiry_duration = 30
    enable_semantic_strategy = true
    semantic_strategy_namespaces = ["bookings"]
    enable_summarization_strategy = true
    summarization_strategy_namespaces = ["{sessionId}"]
  }

  # Agent Runtime
  runtime = {
    "booking-agent" = {
      dockerfile_path = "./backend/Dockerfile"
      context_path = "./backend"
      network_mode = "PUBLIC"

      environment_vars = {
        MODEL_ID = "anthropic.claude-opus-4-20250805"
        DYNAMODB_TABLE_RESERVATIONS = aws_dynamodb_table.reservations.name
        DYNAMODB_TABLE_AVAILABILITY = aws_dynamodb_table.availability.name
      }
    }
  }

  # MCP Gateway
  gateway = {
    protocol_type = "MCP"
    authorizer_type = "CUSTOM_JWT"
    use_created_user_pool = true
  }

  enable_observability = true
}
```

#### DynamoDB Tables (Outside Module)

The module does NOT provision application DynamoDB tables. These must be created separately:

```hcl
resource "aws_dynamodb_table" "reservations" {
  name = "summerhouse-${var.environment}-reservations"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "reservation_id"

  attribute {
    name = "reservation_id"
    type = "S"
  }

  attribute {
    name = "guest_email"
    type = "S"
  }

  global_secondary_index {
    name = "guest_email_index"
    hash_key = "guest_email"
    projection_type = "ALL"
  }
}

resource "aws_dynamodb_table" "availability" {
  name = "summerhouse-${var.environment}-availability"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "date"

  attribute {
    name = "date"
    type = "S"
  }
}

resource "aws_dynamodb_table" "guests" {
  name = "summerhouse-${var.environment}-guests"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "guest_id"

  attribute {
    name = "guest_id"
    type = "S"
  }

  attribute {
    name = "email"
    type = "S"
  }

  global_secondary_index {
    name = "email_index"
    hash_key = "email"
    projection_type = "ALL"
  }
}

resource "aws_dynamodb_table" "pricing" {
  name = "summerhouse-${var.environment}-pricing"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "season_id"

  attribute {
    name = "season_id"
    type = "S"
  }
}
```

### Key Outputs

```hcl
output.cognito_user_pool.id              # For frontend auth
output.runtime["booking-agent"].runtime_id
output.gateway.gateway_url               # For frontend API calls
output.memory.memory_id                  # For agent context
```

### Implications for Implementation

- Use module for all AgentCore infrastructure
- Create separate DynamoDB tables for application data
- Configure Cognito with custom challenge flow
- S3 + CloudFront for frontend hosting (not in module)

---

## 4. AWS Cognito Custom Challenge (Passwordless Auth)

### Overview

AWS Cognito supports passwordless authentication via custom challenge Lambda triggers. This enables the email + 6-digit code flow required by FR-006 to FR-013.

### Key Findings

#### Lambda Triggers Required

1. **Define Auth Challenge** - Determines what challenge to present
2. **Create Auth Challenge** - Generates the 6-digit code and sends email
3. **Verify Auth Challenge Response** - Validates user's code entry

#### Define Auth Challenge Lambda

```python
# infrastructure/lambdas/define-auth/handler.py
def handler(event, context):
    session = event['request']['session']

    # First call - issue custom challenge
    if len(session) == 0:
        event['response']['challengeName'] = 'CUSTOM_CHALLENGE'
        event['response']['issueTokens'] = False
        event['response']['failAuthentication'] = False

    # User provided correct answer - issue tokens
    elif session[-1]['challengeResult'] == True:
        event['response']['issueTokens'] = True
        event['response']['failAuthentication'] = False

    # Wrong answer - try again (up to 3 attempts per FR-011)
    elif len(session) < 3:
        event['response']['challengeName'] = 'CUSTOM_CHALLENGE'
        event['response']['issueTokens'] = False
        event['response']['failAuthentication'] = False

    # Max attempts exceeded
    else:
        event['response']['issueTokens'] = False
        event['response']['failAuthentication'] = True

    return event
```

#### Create Auth Challenge Lambda

```python
# infrastructure/lambdas/create-auth/handler.py
import random
import boto3
import time

ses = boto3.client('ses')
dynamodb = boto3.resource('dynamodb')
codes_table = dynamodb.Table('summerhouse-verification-codes')

def handler(event, context):
    email = event['request']['userAttributes']['email']

    # Generate 6-digit code
    code = str(random.randint(100000, 999999))

    # Store with 10-minute expiry (FR-010)
    codes_table.put_item(Item={
        'email': email,
        'code': code,
        'expires_at': int(time.time()) + 600,  # 10 minutes
        'attempts': 0
    })

    # Send email
    ses.send_email(
        Source='noreply@summerhouse.example.com',
        Destination={'ToAddresses': [email]},
        Message={
            'Subject': {'Data': 'Your Summerhouse verification code'},
            'Body': {
                'Text': {'Data': f'Your verification code is: {code}\n\nThis code expires in 10 minutes.'}
            }
        }
    )

    event['response']['publicChallengeParameters'] = {
        'email': email,
        'codeDeliveryDestination': email
    }
    event['response']['privateChallengeParameters'] = {
        'code': code
    }

    return event
```

#### Verify Auth Challenge Lambda

```python
# infrastructure/lambdas/verify-auth/handler.py
import boto3
import time

dynamodb = boto3.resource('dynamodb')
codes_table = dynamodb.Table('summerhouse-verification-codes')

def handler(event, context):
    email = event['request']['userAttributes']['email']
    user_answer = event['request']['challengeAnswer']
    expected_code = event['request']['privateChallengeParameters']['code']

    # Check if code matches and hasn't expired
    response = codes_table.get_item(Key={'email': email})

    if 'Item' not in response:
        event['response']['answerCorrect'] = False
        return event

    item = response['Item']

    # Check expiry
    if int(time.time()) > item['expires_at']:
        event['response']['answerCorrect'] = False
        return event

    # Check code
    if user_answer == expected_code:
        event['response']['answerCorrect'] = True
        # Clean up
        codes_table.delete_item(Key={'email': email})
    else:
        event['response']['answerCorrect'] = False
        # Increment attempt counter
        codes_table.update_item(
            Key={'email': email},
            UpdateExpression='SET attempts = attempts + :inc',
            ExpressionAttributeValues={':inc': 1}
        )

    return event
```

#### Frontend Integration

```typescript
// lib/auth.ts
import { Auth } from 'aws-amplify';

export async function initiatePasswordlessAuth(email: string) {
  try {
    const user = await Auth.signIn(email);
    return { success: true, user };
  } catch (error) {
    if (error.code === 'UserNotFoundException') {
      // Auto-create user for new guests
      await Auth.signUp({
        username: email,
        password: generateRandomPassword(),
        attributes: { email }
      });
      return initiatePasswordlessAuth(email);
    }
    throw error;
  }
}

export async function verifyCode(user: any, code: string) {
  try {
    const result = await Auth.sendCustomChallengeAnswer(user, code);
    return { success: true, authenticated: true };
  } catch (error) {
    if (error.code === 'NotAuthorizedException') {
      return { success: false, error: 'Invalid or expired code' };
    }
    throw error;
  }
}
```

#### Agent Integration

The agent requests email only when booking is confirmed (FR-006):

```python
from pydantic import BaseModel, ConfigDict
from strands import tool

# Pydantic v2 models for verification tools (per FR-043/FR-044)
class RequestVerificationInput(BaseModel):
    model_config = ConfigDict(strict=True)
    guest_email: str

class RequestVerificationResult(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str
    email: str
    message: str

class VerifyCodeInput(BaseModel):
    model_config = ConfigDict(strict=True)
    guest_email: str
    code: str

class VerifyCodeResult(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str
    guest_email: str
    message: str

@tool
def request_email_verification(input: RequestVerificationInput) -> RequestVerificationResult:
    """Request email verification code for guest.

    Args:
        input: Guest email address for verification
    """
    # This triggers the Cognito custom challenge flow
    # Frontend handles the actual Cognito API call
    return RequestVerificationResult(
        status="verification_requested",
        email=input.guest_email,
        message=f"A 6-digit code has been sent to {input.guest_email}. Please enter the code to verify your identity."
    )

@tool
def verify_email_code(input: VerifyCodeInput) -> VerifyCodeResult:
    """Verify the 6-digit code entered by guest.

    Args:
        input: Guest email and 6-digit verification code
    """
    # Validate against Cognito
    # If valid, mark guest as verified
    return VerifyCodeResult(
        status="verified",
        guest_email=input.guest_email,
        message="Email verified successfully. We can now complete your booking."
    )
```

### Cognito Configuration in Terraform

```hcl
resource "aws_cognito_user_pool" "main" {
  name = "summerhouse-${var.environment}-users"

  auto_verified_attributes = ["email"]

  lambda_config {
    define_auth_challenge = aws_lambda_function.define_auth.arn
    create_auth_challenge = aws_lambda_function.create_auth.arn
    verify_auth_challenge_response = aws_lambda_function.verify_auth.arn
  }

  schema {
    name = "email"
    attribute_data_type = "String"
    required = true
    mutable = true
  }
}

resource "aws_cognito_user_pool_client" "main" {
  name = "summerhouse-client"
  user_pool_id = aws_cognito_user_pool.main.id

  explicit_auth_flows = [
    "ALLOW_CUSTOM_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH"
  ]

  generate_secret = false  # For browser clients
}
```

### Implications for Implementation

- Implement 3 Lambda triggers for custom challenge flow
- Use SES for email delivery
- Store verification codes in DynamoDB with TTL
- Agent delays email request until booking intent confirmed (FR-006)
- Support 3 retry attempts before requiring new code (FR-011)
- 10-minute code expiry (FR-010)

---

## Research Summary

### Technology Decisions

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Frontend UI | Next.js 14 + Vercel AI SDK v6 | Streaming support, React hooks, App Router |
| Agent UI | ai-elements + custom components | Rich content rendering (FR-003) |
| Backend Agent | Strands framework | MCP tools, conversation management, AgentCore deployment |
| Infrastructure | terraform-aws-agentcore | Constitution mandate, unified AgentCore provisioning |
| Authentication | Cognito Custom Challenge | Passwordless email verification (FR-006-013) |
| Storage | DynamoDB | Serverless, pay-per-request, GSI support |
| Hosting | CloudFront + S3 | Static frontend, global CDN |

### Risk Mitigations

| Risk | Mitigation |
|------|------------|
| AI SDK v6 is beta | Use stable patterns from documentation, wrap provider for flexibility |
| AgentCore is new | Module abstracts complexity, comprehensive examples available |
| Conversation context limits | SlidingWindowConversationManager with Memory service backup |
| Double-booking race conditions | DynamoDB conditional writes, atomic operations |
| Email delivery delays | SES + monitoring, fallback messaging in agent |

### Next Steps

1. **Phase 1**: Create data-model.md with DynamoDB schemas
2. **Phase 1**: Define API contracts (MCP tools, REST endpoints)
3. **Phase 1**: Create quickstart.md for development setup
4. **Phase 2**: Generate tasks.md via `/speckit.tasks`
