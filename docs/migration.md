# Migration guide

Password login has been removed. Use anonymous, authorized token sessions, or
the separate OAuth2 client.

The following preferred names are additive aliases. Existing callers do not
need to migrate immediately.

| Existing Client method | Preferred name |
| --- | --- |
| `get_authenticated_user` | `get_me` |
| `get_my_groups` | `iter_my_groups` |
| `my_inventory` | `iter_my_inventory` |
| `my_friends` | `iter_my_friends` |
| `pending_friends` | `iter_pending_friends` |
| `my_ignores` | `iter_my_ignores` |
| `my_balance` | `get_my_balance` |
| `my_outfits` | `get_my_outfits` |
| `recently_played` | `iter_recently_played` |
| `conversations` | `iter_conversations` |
| `conversation_messages` | `get_conversation_messages` |
| `trade_counts` | `get_trade_counts` |
| `trades` | `iter_trades` |
| `site_banners` | `get_site_banners` |
| `site_promos` | `get_site_promos` |
| `featured_events` | `get_featured_events` |
| `official_messages` | `get_official_messages` |
| `pending_payments` | `get_pending_payments` |

For groups, use `get_roles`, `get_metrics`, `get_pending_transfer`, and
`iter_members`, `iter_bans`, `iter_announcements`, `iter_wall_posts`,
`iter_places`, `iter_store_items`, `iter_funds`. For users, use
`iter_groups`, `iter_usernames`, `iter_places`, `iter_inventory`, `iter_friends`.

HTTP paths and successful response shapes stay unchanged. Shared pagination
now handles absent totals consistently; malformed responses may raise errors
instead of being interpreted as empty results. Ban errors are propagated.
