import samples

def _seed(env, cost=12.0, active=1, backup=None):
    with env.db() as c:
        c.execute("INSERT INTO skus(sku,title,price,cost,source,backup_source,active) "
                  "VALUES('S1','Widget',40,?,'spocket',?,?)", (cost, backup, active))

def test_alias_is_deterministic(env, monkeypatch):
    monkeypatch.setenv("ORDER_ALIAS_DOMAIN", "shop.com")
    assert samples.alias_for("S1") == "samples+S1@shop.com"

def test_pending_excludes_sampled(env):
    _seed(env)
    assert [r["sku"] for r in samples.pending()] == ["S1"]
    with env.db() as c:
        c.execute("INSERT INTO samples(sku,supplier,ordered_at,cost,verdict) "
                  "VALUES('S1','spocket',datetime('now'),12,'ordered')")
    assert samples.pending() == []

def test_order_respects_max_cost(env, monkeypatch):
    monkeypatch.setenv("SAMPLE_MAX_COST", "5")
    monkeypatch.setenv("SAMPLE_BUDGET_MONTH", "1000")
    monkeypatch.setenv("SAMPLE_ADDRESS", "1 Test St")
    _seed(env, cost=12.0)
    monkeypatch.setattr(samples.suppliers, "place_order", lambda s, o: "spocket")
    assert samples.order() == []          # 12 > cap 5

def test_order_places_within_budget(env, monkeypatch):
    monkeypatch.setenv("SAMPLE_MAX_COST", "30")
    monkeypatch.setenv("SAMPLE_BUDGET_MONTH", "1000")
    monkeypatch.setenv("SAMPLE_ADDRESS", "1 Test St")
    _seed(env, cost=12.0)
    monkeypatch.setattr(samples.suppliers, "place_order", lambda s, o: "spocket")
    assert samples.order() == ["S1"]

def test_score_demotes_slow_supplier(env):
    _seed(env, backup=None)
    with env.db() as c:
        c.execute("INSERT INTO samples(sku,supplier,ordered_at,cost,verdict) "
                  "VALUES('S1','spocket','2026-10-01 10:00:00',12,'ordered')")
        c.execute("INSERT INTO orders(fingerprint,sku,tracking,status,created_at) "
                  "VALUES('f1','S1','1Z999AA10123456784','SHIPPED','2026-10-05 10:00:00')")
    samples.score()
    with env.db() as c:
        assert c.execute("SELECT verdict FROM samples WHERE sku='S1'").fetchone()["verdict"] == "fail"
        assert c.execute("SELECT active FROM skus WHERE sku='S1'").fetchone()["active"] == 0

def test_score_passes_fast_supplier(env):
    _seed(env)
    with env.db() as c:
        c.execute("INSERT INTO samples(sku,supplier,ordered_at,cost,verdict) "
                  "VALUES('S1','spocket','2026-10-01 10:00:00',12,'ordered')")
        c.execute("INSERT INTO orders(fingerprint,sku,tracking,status,created_at) "
                  "VALUES('f1','S1','1Z999AA10123456784','SHIPPED','2026-10-02 09:00:00')")
    samples.score()
    with env.db() as c:
        assert c.execute("SELECT verdict FROM samples WHERE sku='S1'").fetchone()["verdict"] == "pass"
        assert c.execute("SELECT active FROM skus WHERE sku='S1'").fetchone()["active"] == 1
