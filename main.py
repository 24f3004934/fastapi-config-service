import os
from pathlib import Path
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import yaml
from dotenv import dotenv_values

BASE = Path(__file__).resolve().parent
DEFAULTS = {"port": 8000, "workers": 1, "debug": False, "log_level": "info", "api_key": "default-secret-000"}
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def coerce(key, value):
    if key in ("port", "workers"):
        return int(value)
    if key == "debug":
        return str(value).lower() in ("true", "1", "yes", "on")
    return str(value)

@app.get('/effective-config')
def effective_config(set: list[str] = Query(default=[])):
    config = dict(DEFAULTS)
    environment = os.getenv('APP_ENV', 'development')
    yaml_path = BASE / f'config.{environment}.yaml'
    if yaml_path.is_file():
        config.update(yaml.safe_load(yaml_path.read_text()) or {})
    dotenv = dotenv_values(BASE / '.env')
    for key, value in dotenv.items():
        if value is not None:
            normalized = 'workers' if key == 'NUM_WORKERS' else (key[4:].lower() if key.startswith('APP_') else key.lower())
            config[normalized] = value
    for key, value in os.environ.items():
        if key.startswith('APP_') and key != 'APP_ENV':
            config[key[4:].lower()] = value
    for override in set:
        if '=' in override:
            key, value = override.split('=', 1)
            config[key.strip().lower()] = value
    result = {key: coerce(key, value) for key, value in config.items()}
    result['api_key'] = '****'
    return result
