/**
 * Chat API Route - NOT USED IN PRODUCTION
 *
 * This file exists for documentation purposes only.
 *
 * Architecture Note:
 * This project uses static export (output: 'export' in next.config.js),
 * which means API routes are NOT included in the production build.
 * The frontend is hosted on S3 + CloudFront as static files.
 *
 * Instead of API routes, the frontend calls AgentCore Runtime directly
 * from the browser using:
 * - Cognito Identity Pool for anonymous AWS credentials
 * - SigV4 signing for IAM authentication
 *
 * See:
 * - /src/hooks/useAgentChat.ts - Custom chat hook
 * - /src/lib/sigv4-fetch.ts - Browser-side SigV4 signing
 * - /src/lib/aws-credentials.ts - Cognito credential management
 */

import { NextResponse } from 'next/server'

export async function POST() {
  return NextResponse.json(
    {
      error: 'API routes are not available in static export',
      message:
        'This frontend uses direct browser-to-AgentCore communication. ' +
        'See /src/hooks/useAgentChat.ts for the implementation.',
    },
    { status: 501 }
  )
}

export async function GET() {
  return NextResponse.json({
    status: 'static-export',
    message: 'API routes are not included in the production build',
    architecture: 'Browser → Cognito Identity Pool → AgentCore Runtime (SigV4)',
  })
}
