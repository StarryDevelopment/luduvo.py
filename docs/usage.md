# Usage guide

## Public resources

```python
import asyncio
from luduvo import Client

async def main():
    async with Client() as client:
        user = await client.get_user_by_username("example")
        async for group in user.iter_groups().limit(10):
            print(group.id, group.name)

asyncio.run(main())
```

Prefer `get_*` for a single awaited result, `iter_*` for lazy paginators,
and `search_*` for searches. Existing names remain supported.
Paginators support async iteration, `limit(n)`, `first()` and `flatten()`.
The limit mutates the paginator; construct a new paginator for independent queries.

## Authorized sessions

Use only authorized sessions provided through supported platform mechanisms.
Pass `token` and optionally `refresh_token` to Client. Password login is
not supported. JWT expiration is used only to schedule refresh, not to verify identity.
Persist rotated credentials into protected storage before closing a client.
Do not share one rotating session among independent processes without coordination.

```python
async with Client(token=access_token, refresh_token=refresh_token) as client:
    me = await client.get_me()
    async for group in client.iter_my_groups():
        print(group.name)
    tokens = client.tokens  # save securely before closing
```

## Groups and roles

```python
group = await client.get_group(group_id)
roles = await group.get_roles()
member = await group.get_member(user_id)
if member.has_role(role_id):
    print("Role assigned")
```

Roles and memberships are snapshots. Fetch again after changes.
Mutations require appropriate platform permissions. A 403 indicates access was
denied; do not equate it with an empty collection. Check mutation return values
and verify server state where necessary.

## OAuth2 identity

```python
from luduvo import OAuth2Client

async with OAuth2Client(client_id, redirect_uri, client_secret=client_secret) as oauth:
    authorization = oauth.authorize()
    # Store authorization securely, bound to the initiating account.
    # Redirect the browser to authorization.url.
    # In the callback, atomically consume the stored session:
    token = await oauth.exchange(code, state, authorization)
    user = await oauth.userinfo(token)
```

The callback must use the registered redirect URI and validate the initiating
application session. PKCE and state are handled by the SDK; persistence and
single-use enforcement belong to your application. Keep OAuth identity tokens
separate from account session tokens.

## Response types and errors

User, Group, Place, Friend, Member, Presence and GroupMetrics are domain models.
Less documented resources return JSON-compatible dictionaries or lists, with
public annotations in `luduvo.models`. Unknown fields are preserved; type
annotations do not validate every server field. Group analytics includes typed
range, freshness and role count records.

HTTP errors are raised as SDK exceptions, except where a method explicitly
returns a fallback, such as get_headshot_url. Only GET and HEAD are retried for
selected transient HTTP statuses. Mutations are not automatically retried.
Use bounded concurrency and respect server limits; the SDK defaults are not
a statement of the platform's allowed request rate.
