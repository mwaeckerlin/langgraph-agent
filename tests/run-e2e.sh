#!/usr/bin/env bash
# E2E tests for mwaeckerlin/langgraph-agent: API, authentication, graphs,
# threads with PostgreSQL checkpoints, persistence across a restart, and the
# refusal to start without a database.
# Usage: bash tests/run-e2e.sh
set -uo pipefail

cd "$(dirname "$0")/.."
COMPOSE="tests/e2e/docker-compose.yml"
_compose() { docker compose -f "$COMPOSE" --profile tester --profile nodb "$@"; }

cleanup() { _compose down -v --remove-orphans > /dev/null 2>&1 || true; }
trap cleanup EXIT

cleanup
echo "==> Starting database and agents..."
docker compose -f "$COMPOSE" up -d --build --wait db fake-llm agent agent-secret agent-open agent-llm > /dev/null 2>&1

EXIT=0
docker compose -f "$COMPOSE" run --rm tester python -u test_api.py before || EXIT=1

docker compose -f "$COMPOSE" restart agent > /dev/null 2>&1
docker compose -f "$COMPOSE" run --rm tester python -u test_api.py after || EXIT=1

echo "==> E2E: start without database"
docker compose -f "$COMPOSE" --profile nodb up agent-nodb > /dev/null 2>&1
CODE=$(docker compose -f "$COMPOSE" --profile nodb ps -a --format '{{.ExitCode}}' agent-nodb)
LOG=$(docker compose -f "$COMPOSE" --profile nodb logs agent-nodb 2>&1)
if [[ "${CODE}" != "0" && "${LOG}" == *"DATABASE_URI is required"* ]]; then
    echo "  PASS  refuses_to_start_without_database"
else
    echo "  FAIL  refuses_to_start_without_database: exit ${CODE}: ${LOG: -400}"
    EXIT=1
fi

if [[ ${EXIT} -ne 0 ]]; then
    echo "==> agent logs:"
    docker compose -f "$COMPOSE" logs agent agent-secret agent-open agent-llm 2>&1 | tail -120
fi
exit ${EXIT}
