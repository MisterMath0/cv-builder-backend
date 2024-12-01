web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
release: apt-get update && apt-get install -y libgobject-2.0-0 libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 shared-mime-info
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT