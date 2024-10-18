# Using docker database

## How init Pneumatic database
1. Open terminal in the ``pneumatic-backend/database`` folder
2. Start container with command
```
docker-compose up -d
```
3. Save database export file to directory ``pneumatic-backend/database/backups/dump.sql``
4. (Optional) If database already exists need recreate with commands:
``` 
docker exec -it pneumatic_postgres sh -c "dropdb -U pneumatic pneumatic && createdb -U pneumatic --owner pneumatic pneumatic"
```
5. Import data in the database 
```
docker exec -it pneumatic_postgres sh -c "psql -U pneumatic -h localhost pneumatic < /backups/dump.sql"
```


# How to connect app to the database
1. Open terminal in the ``pneumatic-backend/database`` folder
2. Start container with command
```
docker-compose up -d
```
3. Specify env variable ``POSTGRES_PORT=5433`` to the app
4. Run app
