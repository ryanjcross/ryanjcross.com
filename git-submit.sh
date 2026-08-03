#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")"

if ! command -v git >/dev/null 2>&1; then
  echo "Git is not installed. Install Git, then run this script again."
  exit 1
fi

commit_message="${1:-Publish Ryan portfolio}"

if [[ ! -d .git ]]; then
  echo "Initializing this folder as a Git repository..."
  git init -b main
fi

# Keep the branch name consistent for a first GitHub push.
git branch -M main

git add -A

if git diff --cached --quiet; then
  echo "There are no new changes to commit."
else
  git commit -m "$commit_message"
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  echo
  echo "Paste the GitHub repository URL you want to use."
  echo "Example: https://github.com/your-name/ryan-portfolio.git"
  read -r -p "Repository URL: " repository_url

  if [[ -z "$repository_url" ]]; then
    echo "No repository URL was entered. Create an empty repository on GitHub,"
    echo "then run this script again and paste its URL."
    exit 1
  fi

  case "$repository_url" in
    https://github.com/*.git|git@github.com:*.git)
      git remote add origin "$repository_url"
      ;;
    *)
      echo "That does not look like a GitHub repository URL ending in .git."
      exit 1
      ;;
  esac
fi

echo "Pushing the website to GitHub..."
git push -u origin main

echo
echo "Done. Your website source is now on GitHub:"
git remote get-url origin
