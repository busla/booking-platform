/**
 * Pre Sign Up Lambda
 *
 * Auto-confirms users since we handle verification via custom auth challenge.
 * For the anonymous user, sets email_verified=false so tools can distinguish
 * anonymous users from verified users via JWT claims.
 */
const ANONYMOUS_USER_EMAIL = process.env.ANONYMOUS_USER_EMAIL ?? '';

export const handler = async (event) => {
  console.log('PreSignUp event:', JSON.stringify(event));

  const email = event.request.userAttributes.email;

  // Auto-confirm the user (required for sign-in)
  event.response.autoConfirmUser = true;

  // Anonymous user: do NOT verify email (email_verified=false in JWT)
  // This allows tools to check email_verified claim for authorization
  if (ANONYMOUS_USER_EMAIL && email === ANONYMOUS_USER_EMAIL) {
    console.log(`Anonymous user detected: ${email}, setting email_verified=false`);
    event.response.autoVerifyEmail = false;
  } else {
    // Regular user: verify email (we verify via custom challenge)
    event.response.autoVerifyEmail = true;
  }

  return event;
};
