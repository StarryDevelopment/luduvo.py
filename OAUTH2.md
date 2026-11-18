# Experimental OAuth2 integration

The OAuth endpoint contract is based on community documentation at
https://pypi.org/project/luduvo.py/ (a separate package). It has not been
verified against the live service. The authorization URL can be configured
if the provider uses a different browser endpoint.

Use a registered application and the exact registered redirect URI.
Create an OAuth2Client, call authorize(), and store the returned Authorization
server-side with the initiating Discord user and session. Redirect the browser
to its URL. On callback atomically retrieve and consume the session, verify
that it belongs to the initiating user, handle provider errors, and call
exchange(code, state, authorization). Then use userinfo(token).

Never log authorization URLs, codes, verifiers, client secrets or tokens.
Do not use OAuth access tokens for ordinary account authentication.
The application is responsible for session persistence, state replay prevention,
account linking policy, and deletion of tokens after identity verification.
OAuth app management and token refresh/revocation are not implemented.
