import tracking

def test_sample_alias_recognised(env, monkeypatch):
    monkeypatch.setenv("ORDER_ALIAS_DOMAIN", "shop.com")
    assert tracking.alias_for({"fingerprint": "abc"}) == "orders+abc@shop.com"
