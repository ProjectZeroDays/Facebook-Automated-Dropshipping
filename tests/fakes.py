class FakeLocator:
    def __init__(self, count=0, text=""):
        self._count, self._text = count, text
    def count(self): return self._count
    def first(self): return self
    def wait_for(self, **kw): return None
    def click(self): pass
    def fill(self, v): self._v = v

class FakePage:
    def __init__(self, email_inputs=0, body="Marketplace"):
        self.email_inputs, self.body = email_inputs, body
    def locator(self, sel):
        if "input[name='email']" in sel: return FakeLocator(self.email_inputs)
        return FakeLocator(1)
    def inner_text(self, sel): return self.body
