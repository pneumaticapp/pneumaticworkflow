# Railway file-service deployment files

Railway-specific files for the file-service and its PostgreSQL database live
here, separate from the file-service's regular Dockerfile and local Compose
configuration.

## PostgreSQL service

Build the shared PostgreSQL service with
`storage/railway/postgresql/Dockerfile` and the repository root as its build
context. The image includes the shared
`scripts/postgres-init/create-file-service-db.sh` bootstrap used by Docker
Compose. On a new PostgreSQL volume, the official image runs it to create the
file-service role and its separate logical database in the same PostgreSQL
service.

Set `FILE_POSTGRES_USER`, `FILE_POSTGRES_PASSWORD`, and `FILE_POSTGRES_DB` on
the PostgreSQL service to values referenced by the file-service variables.
Initialization scripts run only when PostgreSQL initializes an empty data
directory; changing this image does not alter an existing database volume.
