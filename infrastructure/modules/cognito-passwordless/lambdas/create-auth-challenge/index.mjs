/**
 * Create Auth Challenge Lambda
 *
 * Generates a verification code, stores it in DynamoDB, and sends via SES.
 */
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, PutCommand } from '@aws-sdk/lib-dynamodb';
import { SESClient, SendEmailCommand } from '@aws-sdk/client-ses';

const dynamoClient = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(dynamoClient);
const sesClient = new SESClient({});

const TABLE_NAME = process.env.VERIFICATION_TABLE;
const FROM_EMAIL = process.env.FROM_EMAIL;
const CODE_TTL = parseInt(process.env.CODE_TTL ?? '300', 10);
const CODE_LENGTH = parseInt(process.env.CODE_LENGTH ?? '6', 10);
const MAX_ATTEMPTS = parseInt(process.env.MAX_ATTEMPTS ?? '3', 10);

/**
 * Generate a random numeric code
 */
const generateCode = (length) => {
  let code = '';
  for (let i = 0; i < length; i++) {
    code += Math.floor(Math.random() * 10).toString();
  }
  return code;
};

export const handler = async (event) => {
  console.log('CreateAuthChallenge event:', JSON.stringify(event));

  const email = event.request.userAttributes.email;
  const code = generateCode(CODE_LENGTH);
  const now = Math.floor(Date.now() / 1000);
  const ttl = now + CODE_TTL;

  // Store in DynamoDB
  await docClient.send(new PutCommand({
    TableName: TABLE_NAME,
    Item: {
      email,
      code,
      attempts: 0,
      max_attempts: MAX_ATTEMPTS,
      expires_at: ttl,
      created_at: now,
    },
  }));

  // Send email via SES
  try {
    await sesClient.send(new SendEmailCommand({
      Source: FROM_EMAIL,
      Destination: { ToAddresses: [email] },
      Message: {
        Subject: { Data: 'Your Booking Verification Code' },
        Body: {
          Text: {
            Data: `Your verification code is: ${code}\n\nThis code expires in ${Math.floor(CODE_TTL / 60)} minutes.`,
          },
          Html: {
            Data: `
              <html>
              <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>Welcome to Booking!</h2>
                <p>Your verification code is:</p>
                <h1 style="color: #1d4ed8; letter-spacing: 4px;">${code}</h1>
                <p>This code expires in ${Math.floor(CODE_TTL / 60)} minutes.</p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                  If you didn't request this code, please ignore this email.
                </p>
              </body>
              </html>
            `,
          },
        },
      },
    }));
    console.log(`Verification code sent to ${email}`);
  } catch (error) {
    console.error('Failed to send email:', error);
    throw error;
  }

  // Set challenge parameters (code is private, not sent to client)
  event.response.publicChallengeParameters = {
    email,
    codeLength: CODE_LENGTH.toString(),
  };
  event.response.privateChallengeParameters = { code };
  event.response.challengeMetadata = `CODE-${email}`;

  return event;
};
