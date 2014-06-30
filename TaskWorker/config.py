import os

LOGIN_TOKEN_PREFIX  = "TOKEN:"
DEFAULT_LOGIN_EXPIRE_SECONDS = 60*60*24

# store your AUTH_KEY in os via add app.yaml
# env_variables:
#   AUTH_KEY: 'YOUR AUTH KEY'

AUTH_KEY = os.environ.get("TASK_WORKER_AUTH_KEY")
