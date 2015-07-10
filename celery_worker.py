import os
from app import celery, create_app

app = create_app(os.getenv('CONFIG_ENV') or 'default')
app.app_context().push()
