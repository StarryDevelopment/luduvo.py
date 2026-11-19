# Changelog

## 2.0.0

### Breaking changes
- Password login removed. Use authorized access/refresh token sessions or the separate OAuth2 client.
- Group ban errors propagate instead of being silently converted to False.
- Pagination validates page size and malformed responses may raise errors.

### Added
- OAuth2 authorization-code flow with PKCE and state validation.
- Token rotation, unverified JWT metadata, configurable refresh margin and asynchronous persistence callback.
- Group roles, membership management, moderation, analytics, funds and wall resources.
- User presence, bulk presence, searches, inventory, account, store, messaging and trade resources.
- Typed public interface, py.typed, consistent get_/iter_ aliases and explicit public exports.
- Usage and migration guides.
- Bounded concurrency, Retry-After handling, safe read retries and origin validation.

### Fixed
- Correct JSON moderation payload and shared member moderation implementation.
- OAuth authorization endpoint on api.luduvo.com.
- Package discovery excludes generated documentation.
- Shared pagination, concurrent cooldown rechecks and preservation of unsaved rotated tokens during close.

See docs/migration.md before upgrading. Less documented response schemas remain generic JSON.
