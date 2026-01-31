#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE TABLE IF NOT EXISTS Players (
        PlayerID SERIAL PRIMARY KEY,
        TwitchId INT NOT NULL UNIQUE
    );
EOSQL
