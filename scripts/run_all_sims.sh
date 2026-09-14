#!/usr/bin/env bash
# Run the ngspice simulation suite and write results to build/sim/.
set -euo pipefail
cd "$(dirname "$0")/.."
out=${SIM_OUT:-build/sim}
run() { python3 scripts/run_spice.py "$1" --outdir "$out" "${@:2}"; }

run sim/ltc6268-10/ac.cir                        --vec v\(o50\)
run sim/ltc6268-10/noise.cir                     --noise
run sim/lmh34400/ac.cir                          --vec v\(o50\)
run sim/lmh34400/noise.cir                       --noise
run sim/preenfasis/filtro_t_ac.cir               --vec v\(j2\)
run sim/led/bias_t_ac.cir                        --vec v\(rf2\)
run sim/tx_amplifier/ac.cir                      --vec v\(out\)
run sim/tx_amplifier/tran.cir                    --vec v\(out\)
run sim/rx_amp/ac.cir                            --vec v\(out\)
run sim/fca/ac.cir                               --vec v\(out\)
run sim/fca/tran.cir                             --vec v\(out\)

python3 scripts/summarize_sims.py "$out"
