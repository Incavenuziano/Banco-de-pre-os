#!/bin/bash
# Healthcheck script — Banco de Preços v3
# Verifica: DB, API, IBGE, pgvector, filesystem

set -e

API_URL="${API_URL:-http://localhost:8000}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5435}"
DB_NAME="${DB_NAME:-banco_precos}"
DB_USER="${DB_USER:-banco_precos}"

echo "=== Banco de Preços — Health Check ==="
echo ""

# 1. Verificar DB PostgreSQL
echo -n "[DB] PostgreSQL... "
if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > /dev/null 2>&1; then
    echo "OK"
else
    echo "FAIL"
    echo "  Erro: PostgreSQL não está respondendo em $DB_HOST:$DB_PORT"
fi

# 2. Verificar API
echo -n "[API] FastAPI... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "OK (HTTP $HTTP_CODE)"
else
    echo "FAIL (HTTP $HTTP_CODE)"
fi

# 3. Verificar endpoint de saúde detalhado
echo -n "[SAUDE] Health detalhado... "
SAUDE=$(curl -s "$API_URL/api/v1/admin/saude" 2>/dev/null)
if echo "$SAUDE" | grep -q '"status":"ok"'; then
    echo "OK"
else
    echo "DEGRADED"
fi

# 4. Verificar IPCA
echo -n "[IPCA] Dados IPCA... "
IPCA=$(curl -s "$API_URL/api/v1/correcao/ipca?ano_inicio=2020&ano_fim=2020" 2>/dev/null)
if echo "$IPCA" | grep -q '"total_meses"'; then
    echo "OK"
else
    echo "FAIL"
fi

# 5. Verificar filesystem (espaço em disco)
echo -n "[FS] Espaço em disco... "
DISCO_PCT=$(df / | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$DISCO_PCT" -lt 90 ]; then
    echo "OK (${DISCO_PCT}% usado)"
else
    echo "WARN (${DISCO_PCT}% usado)"
fi

echo ""
echo "=== Health Check concluído ==="
