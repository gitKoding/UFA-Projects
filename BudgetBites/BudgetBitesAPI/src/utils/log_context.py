from contextvars import ContextVar

# Holds the current request id for logging
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
