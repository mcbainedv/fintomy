#!/usr/bin/env bash
#
# Fintomy one-command installer.
#
#   curl -fsSL https://raw.githubusercontent.com/mcbainedv/fintomy/main/install.sh | bash
#
# Clones the repo into ./fintomy (or updates it), writes .env from the example,
# then builds and starts the stack. Works with either Docker or Podman.
set -euo pipefail

REPO_URL="${FINTOMY_REPO:-https://github.com/mcbainedv/fintomy.git}"
TARGET_DIR="${FINTOMY_DIR:-fintomy}"

say()  { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31mError:\033[0m %s\n' "$*" >&2; exit 1; }

# --- pick a container engine -------------------------------------------------
if docker compose version >/dev/null 2>&1; then
  COMPOSE="docker compose"
elif podman compose version >/dev/null 2>&1; then
  COMPOSE="podman compose"
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE="docker-compose"
else
  die "Need Docker or Podman with the Compose plugin.
  Fedora:  sudo dnf install podman podman-compose   (or docker-compose-plugin)
  Ubuntu:  sudo apt install docker.io docker-compose-plugin
  macOS:   install Docker Desktop or Podman Desktop"
fi
say "Using: $COMPOSE"

command -v git >/dev/null 2>&1 || die "git is not installed."

# --- get the code ----------------------------------------------------------
if [ -d "$TARGET_DIR/.git" ]; then
  say "Updating existing checkout in ./$TARGET_DIR"
  git -C "$TARGET_DIR" pull --ff-only
else
  say "Cloning into ./$TARGET_DIR"
  git clone --depth 1 "$REPO_URL" "$TARGET_DIR"
fi
cd "$TARGET_DIR"

# --- config --------------------------------------------------------------
if [ ! -f .env ]; then
  cp .env.example .env
  say "Created .env (edit passwords / timezone there if you like)"
fi

# --- build & run ---------------------------------------------------------
say "Building and starting containers (first run downloads images + does a ~2y backfill)"
$COMPOSE up -d --build

PORT="$(grep -E '^WEB_PORT=' .env | cut -d= -f2)"
PORT="${PORT:-6001}"

printf '\n\033[1;32mFintomy is starting.\033[0m\n\n'
printf '  UI:        http://localhost:%s\n' "$PORT"
printf '  Progress:  %s logs -f scraper\n' "$COMPOSE"
printf '  Stop:      %s down          (add -v to also wipe the database)\n\n' "$COMPOSE"
printf 'The first backfill (2 years of daily data for ~200 companies) takes a few\n'
printf 'minutes; the dashboard fills in as it runs.\n'
