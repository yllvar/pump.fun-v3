# Authentication

## Public Access

Most Pump.fun API endpoints are publicly accessible and do not require authentication. You can make direct HTTP requests to these endpoints without any API keys or tokens.

## Rate Limiting

To ensure fair usage, the following rate limits apply:

- **60 requests per minute** per IP address
- Additional rate limiting may apply to specific endpoints
- If you exceed these limits, you may receive HTTP 429 (Too Many Requests) responses

## Best Practices

1. **Implement Exponential Backoff**: If you encounter rate limits, implement exponential backoff in your retry logic.
2. **Cache Responses**: Cache responses when possible to reduce the number of API calls.
3. **Respect Rate Limits**: Monitor your request rate to avoid being rate-limited.

## Future Authentication

If Pump.fun introduces authenticated endpoints in the future, this section will be updated with the necessary authentication methods and requirements.

## Example: Handling Rate Limits (Python)

```python
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "POST"]
)
session.mount('https://', HTTPAdapter(max_retries=retries))

try:
    response = session.get('https://frontend-api-v3.pump.fun/trades/latest')
    response.raise_for_status()
    data = response.json()
    print(data)
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
```
