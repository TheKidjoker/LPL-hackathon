// Cognito sign-in for the live API. Each role in the "View as" switcher signs in as its demo
// user (demo-client, demo-advisor, demo-fraud), and API Gateway verifies the ID token, so
// the server, not the browser, decides the role.
//
// Demo convenience only: the shared demo password comes from VITE_DEMO_PASSWORD at build
// time. A production build would send people to the Cognito hosted login and never bundle
// a password.

const CLIENT_ID = import.meta.env.VITE_COGNITO_CLIENT_ID || "";
const PASSWORD = import.meta.env.VITE_DEMO_PASSWORD || "";
const ENDPOINT = "https://cognito-idp.us-east-1.amazonaws.com/";

export const AUTH_ENABLED = Boolean(CLIENT_ID && PASSWORD);

const tokens = {}; // role -> { idToken, expiresAt }

async function signIn(role) {
  const res = await fetch(ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-amz-json-1.1",
      "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
    },
    body: JSON.stringify({
      AuthFlow: "USER_PASSWORD_AUTH",
      ClientId: CLIENT_ID,
      AuthParameters: { USERNAME: `demo-${role}`, PASSWORD },
    }),
  });
  const data = await res.json().catch(() => ({}));
  const result = data.AuthenticationResult;
  if (!res.ok || !result?.IdToken) throw new Error(data.message || `Sign-in failed for the ${role} demo user`);
  // Refresh a minute early so a request never goes out with an expiring token.
  tokens[role] = { idToken: result.IdToken, expiresAt: Date.now() + (result.ExpiresIn - 60) * 1000 };
  return result.IdToken;
}

export async function idTokenFor(role) {
  const cached = tokens[role];
  if (cached && cached.expiresAt > Date.now()) return cached.idToken;
  return signIn(role);
}
