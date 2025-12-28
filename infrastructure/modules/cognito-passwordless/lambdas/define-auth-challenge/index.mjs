/**
 * Define Auth Challenge Lambda
 *
 * Determines the next step in the custom auth flow:
 * - If no sessions: Start with CUSTOM_CHALLENGE
 * - If previous challenge answered correctly: Issue tokens
 * - If previous challenge failed: Fail auth
 */
export const handler = async (event) => {
  console.log('DefineAuthChallenge event:', JSON.stringify(event));

  const session = event.request?.session ?? [];

  if (session.length === 0) {
    // First call - start custom challenge
    event.response.issueTokens = false;
    event.response.failAuthentication = false;
    event.response.challengeName = 'CUSTOM_CHALLENGE';
  } else if (session.at(-1)?.challengeResult === true) {
    // Challenge answered correctly - issue tokens
    event.response.issueTokens = true;
    event.response.failAuthentication = false;
  } else {
    // Challenge failed
    event.response.issueTokens = false;
    event.response.failAuthentication = true;
  }

  console.log('DefineAuthChallenge response:', JSON.stringify(event.response));
  return event;
};
