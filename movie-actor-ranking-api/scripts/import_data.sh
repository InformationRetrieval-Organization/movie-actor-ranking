#!/bin/bash

# Variables
CONTAINER_NAME=movieactorrankingpostgres
DATABASE_NAME=movieactorrankingdb
USERNAME=postgres
INPUT_FILE=database_dump.sql

# get current workspace directory
WORKSPACE=$(pwd)

# use file from workspace
INPUT_FILE=$WORKSPACE/$INPUT_FILE

# reset the database tables
uv run python src/db/helpers/reset_database.py

# Import the dump file into the PostgreSQL database
docker exec -i $CONTAINER_NAME pg_restore -U $USERNAME -d $DATABASE_NAME -v < $INPUT_FILE
