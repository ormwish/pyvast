
class MockAdapter:
    async def fetch(self, ctx, *, session=None):
        return "<VAST version='4.0'><Ad><InLine/></Ad></VAST>"
