#!/bin/bash
set -euo pipefail
REPORT_TIME_LOG="${REPORT_TIME_LOG:-time_report.txt}"
shift  # get rid of the  \'-c\' supplied by make.
tsi=$(date -u '+%Y%m%d%H%M%S%N') # Initial timestamp
exec 3>&1 4>&2
time=$(LANG="C"; TIMEFORMAT="r=%lR u=%lU s=%lS"; { time sh -c "$*" 1>&3 2>&4; } 2>&1)
ret=$? # Command execution result
tsf=$(date -u '+%Y%m%d%H%M%S%N') # Final timestamp
cmd=$(echo "$*" | sed -e 's/^[\t ]*//g' -e 's/[\t ]*\\$//g' | tr '\r\n' ' ')
mkdir -p "$(dirname "$REPORT_TIME_LOG")"
echo "${tsi}-${tsf} ${time} ${cmd}" >> ${REPORT_TIME_LOG}
