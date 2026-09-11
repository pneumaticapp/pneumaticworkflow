# Fixtures of the event pipeline (resets of its process globals, the
# fake stream) for every test of the backend: an emit call sits in
# most services, so most apps need them.
pytest_plugins = ['src.logs.events.tests.plugin']
