#!/bin/zsh
# Wait for a phase-1 run to exit, then launch its phase-2 run.
cd /Users/alex/Documents/CR_projects/phil_sycophancy
MODEL=$1; EFF=$2
while pgrep -f -- "--models $MODEL --n 20 --effort $EFF --concurrency 12" > /dev/null; do sleep 30; done
echo "$(date) phase-1 for $MODEL/$EFF finished; launching phase 2"
uv run python -u -m philsyc run --models $MODEL --n 20 --effort $EFF --sets G H I J K L M N P S --concurrency 12
