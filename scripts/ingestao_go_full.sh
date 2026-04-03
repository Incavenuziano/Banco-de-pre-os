#!/bin/bash
# Ingestão completa GO: Jan/2025 → Abr/2026, mês a mês
# Uso: bash scripts/ingestao_go_full.sh

set -euo pipefail

BACKEND_DIR="$(dirname "$0")/../backend"
LOG_DIR="$(dirname "$0")/../tmp/outputs"
mkdir -p "$LOG_DIR"

MASTER_LOG="$LOG_DIR/ingestao-GO-full-$(date +%Y%m%d-%H%M%S).log"

# Períodos: início→fim (inclusive)
PERIODOS=(
  "2025-01-01 2025-01-31"
  "2025-02-01 2025-02-28"
  "2025-03-01 2025-03-31"
  "2025-04-01 2025-04-30"
  "2025-05-01 2025-05-31"
  "2025-06-01 2025-06-30"
  "2025-07-01 2025-07-31"
  "2025-08-01 2025-08-31"
  "2025-09-01 2025-09-30"
  "2025-10-01 2025-10-31"
  "2025-11-01 2025-11-30"
  "2025-12-01 2025-12-31"
  "2026-01-01 2026-01-31"
  "2026-02-01 2026-02-28"
  "2026-03-01 2026-03-31"
  "2026-04-01 2026-04-02"
)

echo "=== Ingestão GO — $(date) ===" | tee "$MASTER_LOG"
echo "Total de períodos: ${#PERIODOS[@]}" | tee -a "$MASTER_LOG"
echo "" | tee -a "$MASTER_LOG"

TOTAL_ERROS=0

for periodo in "${PERIODOS[@]}"; do
  DI=$(echo "$periodo" | awk '{print $1}')
  DF=$(echo "$periodo" | awk '{print $2}')
  echo "----------------------------------------" | tee -a "$MASTER_LOG"
  echo "▶ Período: $DI → $DF  ($(date +%H:%M:%S))" | tee -a "$MASTER_LOG"
  echo "----------------------------------------" | tee -a "$MASTER_LOG"

  if (cd "$BACKEND_DIR" && python3 -m app.services.coletor_municipal \
      --uf GO \
      --data-inicio "$DI" \
      --data-fim "$DF") \
      2>&1 | tee -a "$MASTER_LOG"; then
    echo "✅ Período $DI→$DF concluído" | tee -a "$MASTER_LOG"
  else
    echo "❌ ERRO no período $DI→$DF" | tee -a "$MASTER_LOG"
    TOTAL_ERROS=$((TOTAL_ERROS + 1))
  fi

  echo "" | tee -a "$MASTER_LOG"
  sleep 3  # pausa entre meses para não sobrecarregar a API
done

echo "========================================" | tee -a "$MASTER_LOG"
echo "=== Ingestão GO CONCLUÍDA — $(date) ===" | tee -a "$MASTER_LOG"
echo "=== Erros: $TOTAL_ERROS / ${#PERIODOS[@]} períodos ===" | tee -a "$MASTER_LOG"
echo "========================================" | tee -a "$MASTER_LOG"
echo "Log completo: $MASTER_LOG"
