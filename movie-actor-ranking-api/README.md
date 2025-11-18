# movie actor ranking - api

## requirements

* Python >=3.12
* [uv](https://docs.astral.sh/uv/) - Fast Python package installer
* Visual Studio Code

## Python

### Install uv (if not already installed)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install dependencies
```bash
uv sync
```

## Environment variables
* copy and rename the `.env.sample` file to `.env`

## Database 
```bash
docker compose -f compose.yml up -d
uv run python -m prisma db push
uv run python -m prisma generate
sh scripts/import_data.sh
```

### Run application
```bash
uv run gunicorn main:app -c gunicorn.conf.py
```

### optional: pgadmin
Open `http://localhost:5050/`
1) Email: root@root.com
2) Password: root

Click with the right mouse button on Servers and select Register -> Server.

Connection tab requires to type:
1) Host name/address: host.docker.internal
2) Port: 5433
3) Database: movieactorrankingdb
4) Username: postgres
5) Password: postgres

## optional: swagger
Open `http://localhost:8000/docs` to see the swagger UI

## optional: Docker
building
```bash
docker build --tag tonylukeregistry.azurecr.io/tonylukeregistry/information-retrieval/api:latest .
```

running container locally
```bash
docker run --detach --publish 3100:3100 tonylukeregistry.azurecr.io/tonylukeregistry/information-retrieval/api:latest
```


## optional: azure deployment
change connection string;
```bash
postgresql://<dbuser>:<dbpassword>@<dbservername>.postgres.database.azure.com:<port>/<bdname>?schema=public&sslmode=require
```



