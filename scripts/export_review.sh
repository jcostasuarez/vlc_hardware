#!/usr/bin/env bash
# Reproducible review + fabrication export for one KiCad project directory.
#
#   scripts/export_fabrication.sh <project-directory>
#
# Generates (under build/fabrication/<project>/):
#   erc.rpt drc.rpt            full reports (errors + warnings)
#   erc-errors.rpt drc-errors.rpt  error-only gate reports
#   schematic.pdf layout.pdf   documentation
#   gerbers/                   Gerbers + Excellon drill
#   positions.csv              pick & place
#   top.png bottom.png        3D layer renders
#   layers/*.svg              per-layer plots
#
# It FAILS (non-zero) if ERC or DRC report an *error* level violation.
# Library/metadata warnings (footprint mismatch, symbol drift) are reported but
# do not block fabrication.  Set STRICT=1 to also block on warnings.
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <project-directory>" >&2
  exit 64
fi

project_dir=${1%/}
cli=${KICAD_CLI:-kicad-cli}

# Auto-detect the single native board and its schematic in the directory
# (project filenames do not always match the folder name).
mapfile -t boards < <(find "$project_dir" -maxdepth 1 -name '*.kicad_pcb')
if [[ ${#boards[@]} -ne 1 ]]; then
  echo "Expected exactly one .kicad_pcb in $project_dir (found ${#boards[@]})" >&2
  exit 66
fi
board="${boards[0]}"
schematic="${board%.kicad_pcb}.kicad_sch"
project_name=$(basename "$board" .kicad_pcb)
out="build/fabrication/$project_name"

[[ -f "$board" && -f "$schematic" ]] || {
  echo "Expected $board and $schematic" >&2
  exit 66
}

mkdir -p "$out/gerbers" "$out/layers"

# Detect copper layers (2 or 4 layer designs).
mapfile -t copper < <(grep -oE '"(F|B|In[0-9]+)\.Cu"' "$board" | tr -d '"' | sort -u)
copper_csv=$(IFS=,; echo "${copper[*]}")
layers="$copper_csv,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"

echo "== $project_name =="
echo "copper: $copper_csv"

# Full reports (never fail on warnings).
"$cli" sch erc --output "$out/erc.rpt" --format report --units mm \
  --severity-warning --severity-error "$schematic"
"$cli" pcb drc --output "$out/drc.rpt" --format report --units mm \
  --severity-warning --severity-error --refill-zones --schematic-parity "$board"

# Error-only gate reports.
gate_flags=(--severity-error --exit-code-violations)
[[ "${STRICT:-0}" == "1" ]] && gate_flags=(--severity-warning --severity-error --exit-code-violations)

if "$cli" sch erc --output "$out/erc-errors.rpt" --format report --units mm \
     "${gate_flags[@]}" "$schematic"; then
  echo "ERC: no error-level violations"
else
  echo "ERC: error-level violations found -- see $out/erc-errors.rpt" >&2
  exit 1
fi

if "$cli" pcb drc --output "$out/drc-errors.rpt" --format report --units mm \
     --refill-zones --schematic-parity "${gate_flags[@]}" "$board"; then
  echo "DRC: no error-level violations"
else
  echo "DRC: error-level violations found -- see $out/drc-errors.rpt" >&2
  exit 1
fi

# Documentation.
"$cli" sch export pdf --output "$out/schematic.pdf" "$schematic"
"$cli" pcb export pdf --output "$out/layout.pdf" --layers "$layers" \
  --black-and-white --mode-multipage --include-border-title "$board"

# Fabrication data.
"$cli" pcb export gerbers --output "$out/gerbers" --layers "$layers" \
  --subtract-soldermask --precision 5 "$board"
"$cli" pcb export drill --output "$out/gerbers" --format excellon \
  --drill-origin absolute --excellon-units in --excellon-zeros-format decimal \
  --gerber-precision 5 "$board"
"$cli" pcb export pos --output "$out/positions.csv" --format csv --units mm \
  --side both --exclude-dnp --use-drill-file-origin "$board"

# Layer plots + 3D renders.
"$cli" pcb export svg --output "$out/layers/board.svg" --layers "$layers" \
  --page-size-mode 2 "$board"
"$cli" pcb render --output "$out/top.png" --width 1600 --height 1000 \
  --side top --quality high "$board"
"$cli" pcb render --output "$out/bottom.png" --width 1600 --height 1000 \
  --side bottom --quality high "$board"

echo "Export complete: $out"
