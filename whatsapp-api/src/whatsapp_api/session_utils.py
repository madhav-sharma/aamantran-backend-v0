from starlette.middleware.sessions import SessionMiddleware

def add_session_middleware(app, secret_key="local_secret"):
    app.add_middleware(SessionMiddleware, secret_key=secret_key)
