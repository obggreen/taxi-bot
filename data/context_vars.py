import contextvars

bot_session = contextvars.ContextVar('current_session')
