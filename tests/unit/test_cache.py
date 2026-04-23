from unittest.mock import patch, MagicMock


class TestGetRedis:
    def test_returns_redis_instance(self):
        from src.cache import get_redis, r
        assert get_redis() is r

    @patch("src.cache.redis.Redis")
    def test_redis_configured_with_env(self, mock_redis_cls, monkeypatch):
        monkeypatch.setenv("REDIS_HOST", "myhost")
        monkeypatch.setenv("REDIS_PORT", "6380")

        import importlib
        import src.cache as cache_module
        importlib.reload(cache_module)

        mock_redis_cls.assert_called_with(host="myhost", port=6380, decode_responses=True)
