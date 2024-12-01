
from json import tool


[tool.poetry.scripts]
dev = "uvicorn app.main:app --reload"
init-db = "python -m app.scripts.init_db"
init-templates = "python -m app.scripts.init_templates"