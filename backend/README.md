# Pneumatic backend

## Environment variables

### Required 
* DJANGO_DEBUG: "yes" / "no"
* DJANGO_SECRET_KEY: str
* DJANGO_SETTINGS_MODULE: src.settings
* ENABLE_LOGGING: "yes" / "no"

### For developers
If you need debug SQL queries, use this context manager:
```python
from src.logs.utils import log_sql
with log_sql():
   ... # code for debug here
```
After that, find "django_queries.log" in the project root 
