# Using docker database

## How init Pneumatic database
*Need to be installed postgresql-client on host machine*

1. Save database export file to directory ``pneumatic-backend/database/backups/dump.sql``
2. (Optional) If database already exists need recreate with commands:
```commandline
docker exec -it pneumatic-postgres sh -c "dropdb -U postgres_user postgres_db && createdb -U postgres_user --owner postgres_user postgres_db"
```
3. Import data in the database 
```commandline
docker exec -it pneumatic-postgres sh -c "psql -U postgres_user -h localhost postgres_db < /backups/dump.sql"
```
4. Connect to database
```commandline
 docker exec -it pneumatic-postgres sh -c "psql -U postgres_user postgres_db"
```