import redis

_client = None
_connection_settings = {
    'host': 'localhost',
    'port': 6379,
    'db': 0
}

def _get_client():
    global _client, _connection_settings
    if _client is None:
        _client = redis.Redis(**_connection_settings)
    return _client

def connect(**kwargs):
    global _connection_settings
    _connection_settings.update(kwargs)
    return _get_client()
