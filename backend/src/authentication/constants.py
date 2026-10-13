from datetime import timedelta

DELEGATION_TOKEN_PREFIX = 'mcp-d_'


UPLOAD_TOKEN_PREFIX = 'mcp-u_'


MCP_TOKEN_PREFIXES = (DELEGATION_TOKEN_PREFIX, UPLOAD_TOKEN_PREFIX)


# Reserved bearers never reach regular token authentication.
MCP_TOKEN_MARKER = 'mcp-'


PKCE_METHOD = 'S256'


DELEGATION_TTL = timedelta(seconds=60)


LOGIN_CODE_TTL = timedelta(seconds=60)


CODE_BINDING_TTL = timedelta(seconds=60)


UPLOAD_CAPABILITY_TTL = timedelta(seconds=300)


FILE_AUTHORIZATION_TTL = timedelta(seconds=300)


AUTHORIZATION_REQUEST_TTL = timedelta(minutes=10)


LOGIN_SESSION_EXPIRY_SECONDS = 600


LOGIN_SESSION_KEY = 'mcp_authorization_request'


SERVICE_SECRET_HEADER = 'X-MCP-Service-Secret'


FILE_SERVICE_SECRET_HEADER = 'X-MCP-File-Service-Secret'

PRUNE_BATCH_SIZE = 500
