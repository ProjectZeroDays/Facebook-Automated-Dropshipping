import fbm_core

def test_rate_limiter():
    rl = fbm_core.RateLimiter()
    assert rl is not None
