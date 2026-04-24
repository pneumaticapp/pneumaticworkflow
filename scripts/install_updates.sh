# Install updates from the stable version
docker compose down
docker images --format "{{.ID}}" --filter "reference=pneumaticworkflow/*" | xargs -r docker rmi
git pull origin master
docker compose up -d