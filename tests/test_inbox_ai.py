import inbox_ai

def _draft(conf=0.9, human=False, text="Hi! It ships in 5-8 days."):
    return {"reply": text, "confidence": conf, "needs_human": human}

def test_process_autosends_high_confidence(env, monkeypatch):
    monkeypatch.setattr(inbox_ai, "draft", lambda raw: _draft(0.95))
    assert inbox_ai.process("t1", "when will it ship?") is True
    with env.db() as c:
        assert c.execute("SELECT status FROM drafts WHERE thread_id='t1'").fetchone()["status"] == "auto_sent"

def test_process_queues_low_confidence(env, monkeypatch):
    monkeypatch.setattr(inbox_ai, "draft", lambda raw: _draft(0.5))
    inbox_ai.process("t2", "can i get a refund?")
    with env.db() as c:
        assert c.execute("SELECT status FROM drafts WHERE thread_id='t2'").fetchone()["status"] == "pending"

def test_needs_human_overrides_high_confidence(env, monkeypatch):
    monkeypatch.setattr(inbox_ai, "draft", lambda raw: _draft(0.99, human=True))
    inbox_ai.process("t3", "refund $80 please")
    with env.db() as c:
        assert c.execute("SELECT status FROM drafts WHERE thread_id='t3'").fetchone()["status"] == "pending"

def test_dry_run_never_marks_autosent(env, monkeypatch):
    monkeypatch.setattr(inbox_ai, "draft", lambda raw: _draft(0.99))
    inbox_ai.process("t4", "thanks!", dry=True)
    with env.db() as c:
        assert c.execute("SELECT status FROM drafts WHERE thread_id='t4'").fetchone()["status"] == "pending"

def test_approve_promotes_draft(env):
    with env.db() as c:
        c.execute("INSERT INTO drafts(id,thread_id,text,confidence,status,created_at) "
                  "VALUES('t5','t5','original',0.5,'pending',datetime('now'))")
    inbox_ai.approve("t5", "edited text")
    with env.db() as c:
        row = c.execute("SELECT status,text FROM drafts WHERE thread_id='t5'").fetchone()
    assert row["status"] == "approved" and row["text"] == "edited text"

def test_approve_without_edit_keeps_text(env):
    with env.db() as c:
        c.execute("INSERT INTO drafts(id,thread_id,text,confidence,status,created_at) "
                  "VALUES('t6','t6','keep me',0.5,'pending',datetime('now'))")
    inbox_ai.approve("t6")
    with env.db() as c:
        assert c.execute("SELECT text FROM drafts WHERE thread_id='t6'").fetchone()["text"] == "keep me"
