import redis

_client = None
_connection_settings = {
    'host': 'localhost',
    'port': 6379,
    'db': 0
}

def _get_client(changed=False):
    global _client, _connection_settings
    if changed or _client is None:
        _client = redis.Redis(**_connection_settings)
    return _client

def connect(**kwargs):
    """Updates the current Redis client."""
    global _connection_settings
    if _connection_settings == kwargs:
        return _get_client()
    else:
        _connection_settings.update(kwargs)
    return _get_client(True)
