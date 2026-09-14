# Resultados de simulación (ngspice)

Generado por `scripts/summarize_sims.py` (2026-09-14).
Los supuestos de cada modelo están en `sim/README.md`.

## Respuesta en frecuencia (AC)

| Deck | Banda simulada | Pico | Frecuencia del pico | Ancho de banda a -3 dB |
|---|---|---:|---:|---:|
| `fca` | 1e+04..5e+09 Hz | 0.937 | 3.47e+04 Hz | 8.35e+04 Hz |
| `led__bias_t` | 1e+05..1e+10 Hz | 0.459 | 1e+10 Hz | > banda |
| `lmh34400` | 1e+03..1e+09 Hz | 1.89e+04 | 1.86e+08 Hz | 2.19e+08 Hz |
| `ltc6268-10` | 1e+03..1e+09 Hz | 1.5e+03 | 7.41e+03 Hz | 7.59e+07 Hz |
| `preenfasis__filtro_t` | 1e+05..5e+08 Hz | 0.5 | 5.22e+07 Hz | 8.28e+07 Hz |
| `rx_amp` | 1e+05..1e+10 Hz | 2.5 | 6.61e+09 Hz | > banda |
| `tx_amplifier` | 1e+03..1e+10 Hz | 6.65 | 1.51e+04 Hz | 4.84e+08 Hz |

## Transitorio

| Deck | pico-pico |
|---|---:|
| `fca` | 0.00763 V |
| `tx_amplifier` | 0.00884 V |

## Ruido

| Deck | en salida @1 kHz | en salida @1 MHz | in referida @1 kHz | en salida rms (1k-500M) | in referida rms |
|---|---:|---:|---:|---:|---:|
| `lmh34400` | 5.43e-08 V/√Hz | 5.45e-08 V/√Hz | 5.43e-12 A/√Hz | 0.0129 V | 2.41e-06 A |
| `ltc6268-10` | 6.7e-09 V/√Hz | 6.74e-09 V/√Hz | 4.47e-12 A/√Hz | 0.000334 V | 2.45e-06 A |
