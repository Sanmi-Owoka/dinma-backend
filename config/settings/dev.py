# pylint: skip-file
import dj_database_url

from .base import *

DATABASES = {
    "default": dj_database_url.parse(os.getenv("DATABASE_URL"), conn_max_age=600)
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
