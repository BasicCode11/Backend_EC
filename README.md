```
#install package
Remove-Item -Recurse -Force .venv
Remove-Item -Force uv.lock

uv sync

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