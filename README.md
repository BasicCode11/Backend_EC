# 🔧 Authentication System - Fixes Applied
# install package
```

Remove-Item -Recurse -Force .venv
Remove-Item -Force uv.lock

uv sync
```

#run project command 
 
uv run uvicorn app.main:app --reload

#run db seed 
uv run python -m app.seed.migrations


```

```
#Check current migration status:
uv run alembic current

# View migration history:
uv run alembic history --verbose

#create a new migration:
uv run alembic revision --autogenerate -m "description_of_changes"

#If you need to rollback:
uv run alembic downgrade -1
```
 TWO Token Refresh Mechanisms:

   1. 🔄 Automatic Backend Refresh
     •  Works silently in the background
     •  New token sent via X-New-Token header when expires < 2 hours
     •  Zero friction for users
     •  Perfect for web apps

   2. 🎮 Manual Frontend Refresh
     •  Call /api/refresh endpoint with refresh token
     •  Get new access token (1 day validity)
     •  Full control over timing
     •  Perfect for mobile apps