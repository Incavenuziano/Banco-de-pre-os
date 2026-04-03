#!/bin/bash
# Ingestão GO: Fev/2025 → Abr/2026 (continuação após Jan/2025)
# Aguarda o PID passado como $1 terminar, depois roda mês a mês

set -euo pipefail

WAIT_PID="${1:-}"
BACKEND_DIR="$(cd "$(dirname "$0")/../backend" && pwd)"
LOG_DIR="$(cd "$(dirname "$0")/../tmp/outputs" && pwd)"
mkdir -p "$LOG_DIR"
MASTER_LOG="$LOG_DIR/ingestao-GO-restante-$(date +%Y%m%d-%H%M%S).log"

if [[ -n "$WAIT_PID" ]]; then
  echo "Aguardando PID $WAIT_PID (Jan/2025) terminar..." | tee "$MASTER_LOG"
  while kill -0 "$WAIT_PID" 2>/dev/null; do sleep 15; done
  echo "PID $WAIT_PID concluído. Iniciando continuação — $(date)" | tee -a "$MASTER_LOG"
fi

PERIODOS=(
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

echo "=== Ingestão GO restante — $(date) ===" | tee -a "$MASTER_LOG"
echo "Total de períodos: ${#PERIODOS[@]}" | tee -a "$MASTER_LOG"

TOTAL_ERROS=0

for periodo in "${PERIODOS[@]}"; do
  DI=$(echo "$periodo" | awk '{print $1}')
  DF=$(echo "$periodo" | awk '{print $2}')
  echo "---" | tee -a "$MASTER_LOG"
  echo "▶ $DI → $DF  ($(date +%H:%M:%S))" | tee -a "$MASTER_LOG"

  set +e
  (cd "$BACKEND_DIR" && python3 -m app.services.coletor_municipal \
      --uf GO \
      --data-inicio "$DI" \
      --data-fim "$DF") 2>&1 | tee -a "$MASTER_LOG"
  RC=${PIPESTATUS[0]}
  set -e

  if [[ $RC -eq 0 ]]; then
    echo "✅ $DI→$DF OK" | tee -a "$MASTER_LOG"
  else
    echo "❌ ERRO $DI→$DF (exit $RC)" | tee -a "$MASTER_LOG"
    TOTAL_ERROS=$((TOTAL_ERROS + 1))
  fi

  sleep 5
done

echo "===========================" | tee -a "$MASTER_LOG"
echo "CONCLUÍDO — $(date)" | tee -a "$MASTER_LOG"
echo "Erros: $TOTAL_ERROS / ${#PERIODOS[@]}" | tee -a "$MASTER_LOG"
echo "Log: $MASTER_LOG"
