#!/usr/bin/env bash
set -u

USER_NAME="$USER"
UTC_OFFSET_HOURS="0"
UTC_OFFSET_DISPLAY="+0"

for arg in "$@"; do
  if [[ "$arg" =~ ^[+-][0-9]+$ ]]; then
    UTC_OFFSET_HOURS="$arg"
    UTC_OFFSET_DISPLAY="$arg"
  elif [[ "$arg" =~ ^[0-9]+$ ]]; then
    if [[ "$arg" == "0" ]]; then
      UTC_OFFSET_HOURS="0"
      UTC_OFFSET_DISPLAY="+0"
    else
      UTC_OFFSET_HOURS="-$arg"
      UTC_OFFSET_DISPLAY="-$arg"
    fi
  else
    USER_NAME="$arg"
  fi
done

SCHEDULED_START_TZ_HEADER="SCHED_STRT (UTC${UTC_OFFSET_DISPLAY})"

# Original order
# header_fmt="%-10s %-10s %-19s %-3s %-6s %-30s %-10s %-6s %-19s\n"
# row_fmt="%-10s %-10s %-19s %-3s %-6s %-30s %-10s %-6s %-19s\n"

# printf "$header_fmt" \
#   "JOB_ID" "USER" "SUBMISSION_DATE" "ST" "QUEUE" "REQUESTED_HOST" "WALLTIME" "GPUS" "SCHEDULED_START"

# New order
header_fmt="%-8s %-2s %-21s %-9s %-29s %-7s %-19s %-4s %-9s %-6s %-20s\n"
row_fmt="%-8s %-2s %-21s %-9s %-29s %-7s %-19s %-4s %-9s %-6s %-20s\n"

GREEN="$(tput setaf 2 2>/dev/null || true)"
YELLOW="$(tput setaf 3 2>/dev/null || true)"
RESET="$(tput sgr0 2>/dev/null || true)"

printf "$header_fmt" \
  "JOB_ID" "ST" "$SCHEDULED_START_TZ_HEADER" "TIME" "REQUESTED_HOST" "USER" "SUBMISSION_DATE" "QUE" "WALLTIME" "GPUS" "SCHED_STRT (UTC)"

oarstat -u | awk -v user="$USER_NAME" '
/^[0-9]/ {
  job_id = $1
  queue = $NF
  state = $(NF-1)
  submission_date = $(NF-3) " " $(NF-2)
  owner = $(NF-4)

  if (owner == user) {
    print job_id "|" owner "|" submission_date "|" state "|" queue
  }
}
' | while IFS="|" read -r job_id owner submission_date state queue; do

  details="$(oarstat -fj "$job_id")"

  requested_host="$(printf '%s\n' "$details" | awk -F"'" '
    /network_address[[:space:]]*=/ { print $2; exit }
  ')"
  requested_host="${requested_host:-ANY}"

  walltime="$(printf '%s\n' "$details" | awk -F'= ' '
    /^[[:space:]]*walltime[[:space:]]*=/ { print $2; exit }
  ')"
  walltime="${walltime:-UNKNOWN}"

  gpus="$(
    printf '%s\n' "$details" | awk '
      /^[[:space:]]*properties[[:space:]]*=/ {
        if (match($0, /gpu_count[[:space:]]*[<>=]+[[:space:]]*'\''?([0-9]+)'\''?/, m)) {
          print m[1]
          exit
        }
      }
      /^[[:space:]]*wanted_resources[[:space:]]*=/ {
        if (match($0, /\/gpu=([0-9]+)/, m)) {
          print m[1]
          exit
        }
      }
    '
  )"
  gpus="${gpus:-0}"

  scheduled_start="$(printf '%s\n' "$details" | awk -F'= ' '
    /^[[:space:]]*scheduled_start[[:space:]]*=/ { print $2; exit }
  ')"
  scheduled_start="${scheduled_start:-no prediction}"

  scheduled_start_tz="$scheduled_start"
  if [[ "$scheduled_start" != "no prediction" ]]; then
    scheduled_start_epoch="$(date -u -d "$scheduled_start" +%s 2>/dev/null || true)"
    if [[ -n "${scheduled_start_epoch:-}" ]]; then
      scheduled_start_tz="$(
        date -u -d "@$((scheduled_start_epoch + UTC_OFFSET_HOURS * 3600))" '+%F %T' 2>/dev/null || true
      )"
    fi
    scheduled_start_tz="${scheduled_start_tz:-invalid date}"
  fi

printf "%s|%s|%s|%s|%s|%s|%s|%s|%s|%s\n" \
    "$job_id" "$state" "$scheduled_start_tz" "$requested_host" "$owner" "$submission_date" "$queue" "$walltime" "$gpus" "$scheduled_start"

done | sort -t'|' -k10,10 | while IFS="|" read -r job_id state scheduled_start_tz requested_host owner submission_date queue walltime gpus scheduled_start; do

  color=""
  case "$state" in
    R) color="$GREEN" ;;
    W) color="$YELLOW" ;;
  esac

  time_until="started/unknown"
  if [[ "$scheduled_start" != "no prediction" ]]; then
    now_epoch="$(date +%s)"
    start_epoch="$(date -u -d "$scheduled_start" +%s 2>/dev/null || true)"

    if [[ -n "${start_epoch:-}" ]]; then
      diff=$((start_epoch - now_epoch))
      if (( diff <= 0 )); then
        time_until="started"
      else
        days=$((diff / 86400))
        hours=$(((diff % 86400) / 3600))
        mins=$(((diff % 3600) / 60))

        if (( days > 0 )); then
          time_until="${days}d ${hours}h"
        elif (( hours > 0 )); then
          time_until="${hours}h ${mins}m"
        else
          time_until="${mins}m"
        fi
      fi
    fi
  fi

# Original order
  # printf "%s$row_fmt%s" "$color" \
  #   "$job_id" "$owner" "$submission_date" "$state" "$queue" "$requested_host" "$walltime" "$gpus" "$scheduled_start"
  
# New order

  printf "%s$row_fmt%s" "$color" \
    "$job_id" "$state" "$scheduled_start_tz" "$time_until" "$requested_host" "$owner" "$submission_date" "$queue" "$walltime" "$gpus" "$scheduled_start" \
    "$RESET"
done
