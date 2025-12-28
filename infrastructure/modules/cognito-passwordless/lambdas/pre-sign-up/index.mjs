/**
 * Pre Sign Up Lambda
 *
 * Auto-confirms users since we handle verification via custom auth challenge.
 */
export const handler = async (event) => {
  console.log('PreSignUp event:', JSON.stringify(event));

  // Auto-confirm the user
  event.response.autoConfirmUser = true;

  // Auto-verify email (we verify via custom challenge)
  event.response.autoVerifyEmail = true;

  return event;
};
