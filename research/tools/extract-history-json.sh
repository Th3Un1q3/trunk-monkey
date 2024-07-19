#!/bin/bash

# Function to get commit history with diffs
get_commit_history() {
  # Get the list of commit hashes
  commit_hashes=$(git log --pretty=format:%H -n 150)

  # Initialize the JSON output file if it doesn't exist
  if [ ! -f commit_history.json ]; then
    echo '{ "commits": [] }' > commit_history.json
  fi

  # Iterate over each commit hash
  for commit_hash in $commit_hashes; do
    # Get commit details
    author=$(git log --format=%an -n 1 $commit_hash)
    date=$(git log --format=%ai -n 1 $commit_hash)
    message=$(git log --format=%B -n 1 $commit_hash | tr -d '\n')
    diff=$(git diff $commit_hash^! -- | sed ':a;N;$!ba;s/\n/\\n/g')

    # Create a JSON object for the commit
    commit_json=$(jq -n --arg author "$author" --arg date "$date" --arg message "$message" --arg diff "$diff" \
      '{author: $author, date: $date, message: $message, diff: $diff}')

    # Append the commit JSON object to the commits array in the file
    jq --argjson commit "$commit_json" '.commits += [$commit]' commit_history.json > tmp.$$.json && mv tmp.$$.json commit_history.json
  done
}

# Call the function
get_commit_history
