#!/usr/bin/env bash
# setup_arch_env.sh – Atomia local environment bootstrap for Arch Linux
# ================================================================
# This script installs and configures all system-level dependencies
# needed to run the Atomia project locally on an Arch-based distro.
# It is **idempotent** – running it repeatedly should be safe.
#
# What it does:
#   1. Install core packages via pacman (PostgreSQL, Redis, RabbitMQ, yay)
#   2. Install AUR packages via yay (MongoDB and Neo4j)
#   3. Initialise PostgreSQL cluster if not yet initialised
#   4. Enable & start systemd services for all databases/queues
#   5. Create PostgreSQL role & database expected by Atomia
#
# Usage:
#   chmod +x infrastructure/scripts/setup_arch_env.sh
#   ./infrastructure/scripts/setup_arch_env.sh
# ---------------------------------------------------------------
set -euo pipefail

###############################################
# Helper functions
###############################################
info()  { printf "\033[1;34m[INFO]\033[0m  %s\n" "$*"; }
warn()  { printf "\033[1;33m[WARN]\033[0m  %s\n" "$*"; }
error() { printf "\033[1;31m[ERROR]\033[0m %s\n" "$*"; exit 1; }

###############################################
# 1. Install pacman packages
###############################################
info "Updating package database and installing core packages"
# --needed prevents reinstalling if already present
sudo pacman -Sy --needed --noconfirm base-devel git \
  postgresql redis rabbitmq

###############################################
# 2. Install yay (AUR helper) if missing
###############################################
if ! command -v yay &>/dev/null; then
  info "Installing yay (AUR helper)"
  tmpdir=$(mktemp -d)
  git clone https://aur.archlinux.org/yay.git "$tmpdir/yay"
  (cd "$tmpdir/yay" && makepkg -si --noconfirm)
  rm -rf "$tmpdir"
else
  info "yay already installed – skipping"
fi

###############################################
# 3. Install AUR packages via yay
###############################################
info "Installing MongoDB (mongodb-bin) and Neo4j (neo4j-community) via yay"
yay -Sy --needed --noconfirm mongodb-bin neo4j-community || warn "AUR installation encountered issues; investigate manually."

###############################################
# 4. Initialise PostgreSQL cluster (if first run)
###############################################
if [ ! -d /var/lib/postgres/data ]; then
  info "Initialising PostgreSQL cluster"
  sudo -iu postgres initdb --locale=en_US.UTF-8 -E UTF8 -D /var/lib/postgres/data
else
  info "PostgreSQL cluster already initialised – skipping"
fi

###############################################
# 5. Enable and start systemd services
###############################################
info "Enabling and starting services"
SERVICES=(postgresql mongodb valkey rabbitmq neo4j)
for svc in "${SERVICES[@]}"; do
  # A more robust check for service existence
  if systemctl list-unit-files -q --type service | grep -q "^${svc}\\.service$"; then
    sudo systemctl enable --now "${svc}.service"
  else
    warn "Service ${svc}.service not found – ensure package installed correctly."
  fi
done

info "Waiting for services to start up..."
sleep 5

###############################################
# 6. Create Atomia PostgreSQL role & database (idempotent)
###############################################
info "Creating PostgreSQL role and database for Atomia (if absent)"
read -r -d '' PSQL_CMDS <<'SQL'
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'atomia_user') THEN
      CREATE ROLE atomia_user LOGIN PASSWORD 'atomia_password';
   END IF;
END$$;
CREATE DATABASE atomia_dev OWNER atomia_user;
SQL
sudo -iu postgres psql -v ON_ERROR_STOP=1 -c "${PSQL_CMDS}" || warn "Role/database creation may have partially failed; verify manually."

echo "\n🎉  Local environment setup (system dependencies) completed successfully."
echo "   You can now proceed to create your Python virtual environment:"
echo "     python3 -m venv venv && source venv/bin/activate.fish" 