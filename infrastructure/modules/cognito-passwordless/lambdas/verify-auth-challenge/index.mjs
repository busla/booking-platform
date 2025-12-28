/**
 * Verify Auth Challenge Lambda
 *
 * Validates the code entered by the user against DynamoDB.
 * Implements rate limiting via attempt counter.
 * For the anonymous user (ANONYMOUS_USER_EMAIL), auto-succeeds with static code.
 */
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import {
  DynamoDBDocumentClient,
  GetCommand,
  DeleteCommand,
  UpdateCommand,
} from '@aws-sdk/lib-dynamodb';

const dynamoClient = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(dynamoClient);

const TABLE_NAME = process.env.VERIFICATION_TABLE;
const MAX_ATTEMPTS = parseInt(process.env.MAX_ATTEMPTS ?? '3', 10);
const ANONYMOUS_USER_EMAIL = process.env.ANONYMOUS_USER_EMAIL ?? '';

export const handler = async (event) => {
  console.log('VerifyAuthChallenge event:', JSON.stringify(event));

  const email = event.request.userAttributes.email;
  const userCode = event.request.challengeAnswer;

  // Anonymous user: auto-succeed with static code
  if (ANONYMOUS_USER_EMAIL && email === ANONYMOUS_USER_EMAIL) {
    const isCorrect = userCode === 'ANONYMOUS';
    console.log(`Anonymous user verification: ${isCorrect ? 'success' : 'failed'}`);
    event.response.answerCorrect = isCorrect;
    return event;
  }

  // Regular user: verify against DynamoDB
  try {
    // Get stored code
    const { Item: item } = await docClient.send(new GetCommand({
      TableName: TABLE_NAME,
      Key: { email },
    }));

    if (!item) {
      console.log(`No verification code found for ${email}`);
      event.response.answerCorrect = false;
      return event;
    }

    const { code: storedCode, attempts = 0, expires_at: expiresAt = 0 } = item;
    const now = Math.floor(Date.now() / 1000);

    // Check if expired
    if (now > expiresAt) {
      console.log(`Code expired for ${email}`);
      await docClient.send(new DeleteCommand({
        TableName: TABLE_NAME,
        Key: { email },
      }));
      event.response.answerCorrect = false;
      return event;
    }

    // Check attempts
    if (attempts >= MAX_ATTEMPTS) {
      console.log(`Max attempts exceeded for ${email}`);
      await docClient.send(new DeleteCommand({
        TableName: TABLE_NAME,
        Key: { email },
      }));
      event.response.answerCorrect = false;
      return event;
    }

    // Validate code
    if (userCode === storedCode) {
      console.log(`Code verified successfully for ${email}`);
      await docClient.send(new DeleteCommand({
        TableName: TABLE_NAME,
        Key: { email },
      }));
      event.response.answerCorrect = true;
    } else {
      // Increment attempts
      await docClient.send(new UpdateCommand({
        TableName: TABLE_NAME,
        Key: { email },
        UpdateExpression: 'SET attempts = attempts + :inc',
        ExpressionAttributeValues: { ':inc': 1 },
      }));
      console.log(`Invalid code for ${email}, attempts: ${attempts + 1}`);
      event.response.answerCorrect = false;
    }
  } catch (error) {
    console.error('DynamoDB error:', error);
    event.response.answerCorrect = false;
  }

  return event;
};
