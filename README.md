# trunk-monkey 🐒

## Trunk full of junk?
This AI sniffs out code smells, anti-patterns, and duplicates in your main branch, keeping your trunk clean and your commits confident.  No more merge mayhem, just smooth sailing to faster deploys. ⛵

## Development
```bash
# Build and run the container
docker-compose up --build -d

# Init the project
docker-compose exec dev python cli.py init

docker-compose exec dev python cli.py sync

docker-compose exec dev python cli.py check-all

```
