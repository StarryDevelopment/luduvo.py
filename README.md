
# luduvo-api-wrapper

A Python wrapper for the Luduvo API.

## Installation

```bash
pip install luduvo
```

## Usage

```python
import asyncio
from luduvo import Client

client = Client()
async def main ():
    user await client.get_user(1)
    print(user.username) # > Luduvo

asyncio.run(main)
```

## License

MIT
