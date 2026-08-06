#!/usr/bin/env bash
set -Eeuo pipefail
export LC_ALL=C

readonly SCHEMA="wsl-status/v1"
FORMAT="human"
TOP_N=10

usage() {
  cat <<'USAGE'
Usage: wsl-status.sh [--format human|jsonl] [--top N]

Options:
  --format FORMAT   Output format: human (default) or jsonl
  --top N           Number of memory-heavy processes to show (default: 10)
  -h, --help        Show this help
USAGE
}

fail() {
  printf 'wsl-status: %s\n' "$*" >&2
  exit 2
}

while (($#)); do
  case "$1" in
    --format)
      (($# >= 2)) || fail '--format requires a value'
      FORMAT=$2
      shift 2
      ;;
    --format=*)
      FORMAT=${1#*=}
      shift
      ;;
    --top)
      (($# >= 2)) || fail '--top requires a value'
      TOP_N=$2
      shift 2
      ;;
    --top=*)
      TOP_N=${1#*=}
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "unknown option: $1"
      ;;
  esac
done

[[ $FORMAT == human || $FORMAT == jsonl ]] || fail '--format must be human or jsonl'
[[ $TOP_N =~ ^[1-9][0-9]*$ ]] || fail '--top must be a positive integer'

json_number_or_null() {
  [[ $1 =~ ^-?[0-9]+([.][0-9]+)?$ ]] && printf '%s' "$1" || printf 'null'
}

json_escape() {
  local value=$1
  value=${value//\\/\\\\}
  value=${value//\"/\\\"}
  value=${value//$'\n'/\\n}
  value=${value//$'\r'/\\r}
  value=${value//$'\t'/\\t}
  printf '%s' "$value"
}

mib() {
  awk -v kb="$1" 'BEGIN { printf "%.1f", kb / 1024 }'
}

percent() {
  awk -v used="$1" -v total="$2" \
    'BEGIN { printf "%.1f", (total > 0 ? used * 100 / total : 0) }'
}

cpu_sample() {
  awk '/^cpu / {
    idle = $5 + $6
    total = 0
    for (i = 2; i <= 9; i++) total += $i
    printf "%.0f %.0f\n", idle, total
    exit
  }' /proc/stat
}

read -r cpu_idle_before cpu_total_before < <(cpu_sample)
sleep 0.2
read -r cpu_idle_after cpu_total_after < <(cpu_sample)

cpu_idle_delta=$((cpu_idle_after - cpu_idle_before))
cpu_total_delta=$((cpu_total_after - cpu_total_before))
cpu_used_delta=$((cpu_total_delta - cpu_idle_delta))
cpu_usage_pct=$(percent "$cpu_used_delta" "$cpu_total_delta")

read -r mem_total_kb mem_available_kb < <(
  awk '
    /^MemTotal:/     { total = $2 }
    /^MemAvailable:/ { available = $2 }
    END { print total, available }
  ' /proc/meminfo
)
[[ -n ${mem_total_kb:-} && -n ${mem_available_kb:-} ]] || fail 'cannot read memory statistics'
mem_used_kb=$((mem_total_kb - mem_available_kb))
mem_usage_pct=$(percent "$mem_used_kb" "$mem_total_kb")
mem_used_mib=$(mib "$mem_used_kb")
mem_available_mib=$(mib "$mem_available_mib")
mem_total_mib=$(mib "$mem_total_kb")

read -r disk_total_kb disk_used_kb disk_available_kb disk_usage_pct < <(
  df -Pk -- / | awk 'NR == 2 { gsub(/%/, "", $5); print $2, $3, $4, $5 }'
)
[[ -n ${disk_total_kb:-} ]] || fail 'cannot read root disk statistics'
disk_used_mib=$(mib "$disk_used_kb")
disk_available_mib=$(mib "$disk_available_kb")
disk_total_mib=$(mib "$disk_total_kb")

host=$(hostname)
kernel=$(uname -r)
cpu_cores=$(nproc)
uptime_seconds=$(awk '{ printf "%.0f", $1 }' /proc/uptime)
load_1m=$(awk '{ print $1 }' /proc/loadavg)
timestamp_utc=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
is_wsl=false
[[ ${kernel,,} == *microsoft* || ${kernel,,} == *wsl* ]] && is_wsl=true

# TSV contract: pid, command, cpu_pct, memory_pct, rss_mib
declare -a processes=()
mapfile -t processes < <(
  ps -eo pid=,%cpu=,%mem=,rss=,comm= --sort=-rss |
    awk -v limit="$TOP_N" 'NR <= limit {
      pid = $1
      cpu = $2
      memory = $3
      rss = $4 / 1024
      $1 = $2 = $3 = $4 = ""
      sub(/^ +/, "")
      gsub(/\t/, " ")
      printf "%s\t%s\t%s\t%s\t%.1f\n", pid, $0, cpu, memory, rss
    }'
)

# TSV contract: index, name, utilization_pct, memory_used_mib,
#               memory_total_mib, temperature_c
declare -a gpus=()
if command -v nvidia-smi >/dev/null 2>&1; then
  mapfile -t gpus < <(
    nvidia-smi \
      --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu \
      --format=csv,noheader,nounits 2>/dev/null |
      awk -F',' '
        function trim(value) {
          gsub(/^[[:space:]]+|[[:space:]]+$/, "", value)
          return value
        }
        {
          printf "%s\t%s\t%s\t%s\t%s\t%s\n",
            trim($1), trim($2), trim($3), trim($4), trim($5), trim($6)
        }'
  )
fi
gpu_count=${#gpus[@]}

print_human() {
  printf 'WSL STATUS  %s\n' "$timestamp_utc"
  printf '\nSYSTEM\n'
  printf '  %-18s %s\n' 'Host' "$host"
  printf '  %-18s %s\n' 'Kernel' "$kernel"
  printf '  %-18s %s\n' 'WSL detected' "$is_wsl"
  printf '  %-18s %s\n' 'CPU cores' "$cpu_cores"
  printf '  %-18s %s seconds\n' 'Uptime' "$uptime_seconds"
  printf '  %-18s %s\n' 'Load (1m)' "$load_1m"

  printf '\nRESOURCES\n'
  printf '  %-18s %6s%%\n' 'CPU' "$cpu_usage_pct"
  printf '  %-18s %6s%%  %s / %s MiB\n' \
    'Memory' "$mem_usage_pct" "$mem_used_mib" "$mem_total_mib"
  printf '  %-18s %6s%%  %s / %s MiB\n' \
    'Root disk' "$disk_usage_pct" "$disk_used_mib" "$disk_total_mib"

  printf '\nTOP PROCESSES BY RSS (%s)\n' "$TOP_N"
  printf '  %-7s %-24s %8s %8s %10s\n' 'PID' 'COMMAND' 'CPU%' 'MEM%' 'RSS MiB'
  local row pid command cpu memory rss
  for row in "${processes[@]}"; do
    IFS=$'\t' read -r pid command cpu memory rss <<< "$row"
    printf '  %-7s %-24.24s %8s %8s %10s\n' "$pid" "$command" "$cpu" "$memory" "$rss"
  done

  printf '\nGPU\n'
  if ((${#gpus[@]} == 0)); then
    printf '  unavailable\n'
    return
  fi

  printf '  %-5s %-28s %8s %12s %12s %8s\n' \
    'INDEX' 'NAME' 'UTIL%' 'USED MiB' 'TOTAL MiB' 'TEMP C'
  local index name utilization memory_used memory_total temperature
  for row in "${gpus[@]}"; do
    IFS=$'\t' read -r index name utilization memory_used memory_total temperature <<< "$row"
    printf '  %-5s %-28.28s %8s %12s %12s %8s\n' \
      "$index" "$name" "$utilization" "$memory_used" "$memory_total" "$temperature"
  done
}

print_jsonl() {
  printf '{"schema":"%s","type":"system","timestamp_utc":"%s","host":"%s","kernel":"%s","is_wsl":%s,"gpu_count":%s,"cpu_cores":%s,"uptime_seconds":%s,"load_1m":%s}\n' \
    "$SCHEMA" "$timestamp_utc" "$(json_escape "$host")" "$(json_escape "$kernel")" \
    "$is_wsl" "$gpu_count" "$cpu_cores" "$uptime_seconds" "$load_1m"

  printf '{"schema":"%s","type":"resource","cpu_usage_pct":%s,"memory_used_mib":%s,"memory_available_mib":%s,"memory_total_mib":%s,"memory_usage_pct":%s,"root_disk_used_mib":%s,"root_disk_available_mib":%s,"root_disk_total_mib":%s,"root_disk_usage_pct":%s}\n' \
    "$SCHEMA" "$cpu_usage_pct" "$mem_used_mib" "$mem_available_mib" \
    "$mem_total_mib" "$mem_usage_pct" "$disk_used_mib" \
    "$disk_available_mib" "$disk_total_mib" "$disk_usage_pct"

  local row pid command cpu memory rss
  for row in "${processes[@]}"; do
    IFS=$'\t' read -r pid command cpu memory rss <<< "$row"
    printf '{"schema":"%s","type":"process","pid":%s,"command":"%s","cpu_usage_pct":%s,"memory_usage_pct":%s,"rss_mib":%s}\n' \
      "$SCHEMA" "$pid" "$(json_escape "$command")" "$cpu" "$memory" "$rss"
  done

  local index name utilization memory_used memory_total temperature
  for row in "${gpus[@]}"; do
    IFS=$'\t' read -r index name utilization memory_used memory_total temperature <<< "$row"
    printf '{"schema":"%s","type":"gpu","index":%s,"name":"%s","utilization_pct":%s,"memory_used_mib":%s,"memory_total_mib":%s,"temperature_c":%s}\n' \
      "$SCHEMA" "$index" "$(json_escape "$name")" "$(json_number_or_null "$utilization")" \
      "$(json_number_or_null "$memory_used")" "$(json_number_or_null "$memory_total")" \
      "$(json_number_or_null "$temperature")"
  done
}

case $FORMAT in
  human) print_human ;;
  jsonl) print_jsonl ;;
esac
