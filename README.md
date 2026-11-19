<img src="https://raw.githubusercontent.com/StarryDevelopment/luduvo.py/refs/heads/master/gh-assets/wordmark.svg" alt="luduvo" height=128/>

[Documentation](https://starrydevelopment.github.io/luduvo.py) • [Discord Support Server](https://discord.com/invite/8jsEtksQvD)

> **Disclaimer**  
> This wrapper is community-maintained and is not officially affiliated with Luduvo or its developers.  
> It is an independent project created by members of the community to simplify interaction with the Luduvo API.

## Overview
A modern, asynchronous Python wrapper for the Luduvo API.

## Features
- **Asynchronous**: Works well with asynchronous frameworks like [FastAPI](https://fastapi.tiangolo.com/) and 
[discord.py](https://github.com/Rapptz/discord.py).  
- **Clean Architecture**: Object-oriented structure that maps API resources to intuitive Python classes.
- **Flexible**: Suitable for small scripts, bots, and large-scale backend services.
- **Lightweight**: Minimal overhead and dependencies.

## Installation
To Install the latest stable version run the following command:
```bash
python3 -m pip install luduvo
```

Or to install the latest **unstable** version of luduvo, install [git-scm](https://git-scm.com/downloads) and run the following:

```bash
python3 -m pip install git+https://github.com/StarryDevelopment/luduvo.py.git
```
> [!WARNING]
> Do not install the unstable version in production environments, as it is untested and may contain breaking changes or bugs.

## Authentication

Public API requests do not require credentials. Password login has been
removed because the website uses an interactive CAPTCHA. Use only
authorized sessions obtained through supported platform mechanisms.

```python
import luduvo

async with luduvo.Client(token=access_token, refresh_token=refresh_token) as client:
    me = await client.get_authenticated_user()
    # client.tokens contains the current pair, including rotated tokens.
```

Keep credentials in protected storage; never log them. OAuth2 identity
verification uses the separate OAuth2Client. Token refresh requires a valid
refresh token and is subject to the platform's authorization policy.

See the [usage guide](https://starrydevelopment.github.io/luduvo.py/usage/) and [migration guide](https://starrydevelopment.github.io/luduvo.py/migration/) for typed responses and preferred method names.
