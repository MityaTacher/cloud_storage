#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$ROOT/frontend"

# ── Colour helpers ──────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()    { echo -e "${CYAN}[dev]${NC} $*"; }
success() { echo -e "${GREEN}[dev]${NC} $*"; }
warn()    { echo -e "${YELLOW}[dev]${NC} $*"; }
error()   { echo -e "${RED}[dev]${NC} $*"; exit 1; }

# ── Cleanup on Ctrl-C ───────────────────────────────────────────────────────
cleanup() {
  echo ""
  info "Shutting down..."
  # Kill background frontend process
  [[ -n "$FRONTEND_PID" ]] && kill "$FRONTEND_PID" 2>/dev/null || true
  # Stop docker containers
  if command -v docker-compose &>/dev/null; then
    docker-compose -f "$ROOT/docker-compose.yml" down
  else
    docker stop cloud_db cloud_app 2>/dev/null || true
    docker rm  cloud_db cloud_app 2>/dev/null || true
  fi
  success "Done."
}
trap cleanup EXIT INT TERM

# ── 1. Start backend ────────────────────────────────────────────────────────
info "Starting backend (docker-compose)..."
cd "$ROOT"

if command -v docker-compose &>/dev/null; then
  docker-compose up -d --build
else
  warn "docker-compose not found, using raw docker commands"

  # Remove stale containers if any
  docker rm -f cloud_db cloud_app 2>/dev/null || true

  # Postgres
  docker run -d \
    --name cloud_db \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_DB=postgres \
    -p 5432:5432 \
    postgres:16

  # Wait for postgres
  info "Waiting for postgres to be ready..."
  for i in $(seq 1 30); do
    docker exec cloud_db pg_isready -U postgres -q 2>/dev/null && break
    sleep 1
    [[ $i -eq 30 ]] && error "Postgres didn't start in time"
  done

  # Build app image
  docker build -t cloud_storage_app "$ROOT"

  # App container
  docker run -d \
    --name cloud_app \
    --env-file "$ROOT/.env" \
    -e DATABASE_URL=postgresql+asyncpg://postgres:postgres@cloud_db:5432/postgres \
    --link cloud_db:db \
    -p 8000:8000 \
    -v "$ROOT/uploads:/app/uploads" \
    -v "$ROOT/alembic:/app/alembic" \
    cloud_storage_app \
    bash -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"
fi

# ── 2. Wait for backend to be healthy ──────────────────────────────────────
info "Waiting for backend at http://localhost:8000 ..."
for i in $(seq 1 40); do
  if curl -sf http://localhost:8000/ >/dev/null 2>&1; then
    success "Backend is up!"
    break
  fi
  sleep 2
  [[ $i -eq 40 ]] && error "Backend didn't come up in time. Check: docker logs cloud_app"
done

# ── 3. Install frontend deps if needed ─────────────────────────────────────
if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  info "Installing frontend dependencies..."
  cd "$FRONTEND_DIR" && npm install
fi

# ── 4. Start frontend ───────────────────────────────────────────────────────
info "Starting frontend (Vite) at http://localhost:5173 ..."
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!

success "═══════════════════════════════════════════"
success "  CloudVault is running!"
success "  Frontend → http://localhost:5173"
success "  Backend  → http://localhost:8000"
success "  API docs → http://localhost:8000/docs"
success "  Press Ctrl-C to stop everything."
success "═══════════════════════════════════════════"

# Wait for frontend to exit (keeps script alive)
wait "$FRONTEND_PID"
