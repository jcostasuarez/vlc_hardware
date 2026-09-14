# Resultados de simulación (ngspice)

Generado por `scripts/summarize_sims.py` (2026-09-14).
Supuestos de los modelos en `sim/README.md`.

## Respuesta en frecuencia (AC)

| Deck | Banda simulada | Pico | Frecuencia del pico | Ancho de banda a -3 dB |
|---|---|---:|---:|---:|
| `fca` | 1e+04..5e+09 Hz | 0.936 | 3.47e+04 Hz | 8.35e+04 Hz |
| `led__bias_t` | 1e+05..1e+10 Hz | 0.459 | 1e+10 Hz | > banda |
| `lmh34400` | 1e+03..1e+09 Hz | 2.16e+04 | 2e+06 Hz | 2.19e+08 Hz |
| `ltc6268-10` | 1e+03..1e+09 Hz | 1.5e+03 | 7.41e+03 Hz | 7.59e+07 Hz |
| `preenfasis__filtro_t` | 1e+05..5e+08 Hz | 0.5 | 5.22e+07 Hz | 8.28e+07 Hz |
| `rx_amp` | 1e+05..1e+10 Hz | 8.9 | 8.91e+09 Hz | > banda |
| `tx_amplifier` | 1e+03..1e+10 Hz | 6.65 | 1.51e+04 Hz | 4.84e+08 Hz |

## Transitorio

| Deck | pico-pico |
|---|---:|
| `fca` | 0.00761 V |
| `tx_amplifier` | 0.00884 V |

## Ruido

| Deck | en salida @1 MHz | in referida @1 MHz | en salida rms (banda) | in referida rms (banda) |
|---|---:|---:|---:|---:|
| `lmh34400` | 5.48e-07 V/√Hz | 2.68e-11 A/√Hz | 0.0242 V | 2.06e-06 A |
| `ltc6268-10` | 6.74e-09 V/√Hz | 4.49e-12 A/√Hz | 0.000335 V | 2.29e-06 A |
