# trunk-monkey 🐒

## Trunk full of junk?
This AI sniffs out code smells, anti-patterns, and duplicates in your main branch, keeping your trunk clean and your commits confident.  No more merge mayhem, just smooth sailing to faster deploys. ⛵

## Development
```bash
# Build the image with cli
docker buildx bake

# Init the project
# Attach project you want to analyze as subject and initialize the project
docker run -v $(pwd):/subject trunk-monkey:beta init
# This going to create a `trunk_monkey_manifest.yml` file in the root of the project


# Synchronyze the source code
docker run -v $(pwd):/subject trunk-monkey:beta sync

# Run the checks
docker run -v $(pwd):/subject trunk-monkey:beta check-all



# When you changing the source code, you can sync the source code again
docker run -v $(pwd)/src:/app -v $(pwd):/subject trunk-monkey:beta check-all
```
