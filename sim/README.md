# Simulaciones ngspice

Suite única de simulación para todas las placas VLC, reproducible y sin GUI.
Reemplaza las simulaciones dispersas en LTspice (`.asc`) y OrCAD PSpice
(`-PSpiceFiles`) por decks **ngspice** derivados de los esquemas KiCad.

## Cómo correr

```bash
# toda la suite -> build/sim/
scripts/run_all_sims.sh

# un deck puntual
python3 scripts/run_spice.py sim/ltc6268-10/noise.cir --outdir build/sim --noise

# resumen de métricas -> docs/sim/RESULTS.md
python3 scripts/summarize_sims.py build/sim
```

`scripts/run_spice.py` usa la `libngspice` que viene con KiCad, vía `ctypes`
(no hace falta un binario `ngspice`). Los resultados van a `build/sim/`
(ignorado por git).

## Estructura

```
sim/models/opamp_2pole.sub   macromodelo de opamp de dos polos
sim/models/tia_block.sub     bloque TIA (opamp + Rf/Cf interno)
sim/models/bfr740l3rh.lib    modelo Infineon BFR740L3RH (Gummel-Poon)
sim/<placa>/<análisis>.cir   decks de análisis
```

## Fidelidad de los modelos

Las simulaciones originales no eran reproducibles: los proyectos PSpice
dependían de rutas Windows (`E:\Onedrive\...`) y de netlists (`AC.net`,
`Noise.net`, `Trans.net`) que no están en el repo; los modelos de fabricante de
los opamps son específicos de su herramienta y **ngspice no los puede correr**
(LTC6268-10 usa devices `A` de LTspice; LMH34400/OPA2675 usan `dnlim`/`uplim` y
devices `S` de PSpice).

| Deck | Placa | Análisis | Modelo | Fidelidad |
|---|---|---|---|---|
| `preenfasis/filtro_t_ac` | `preenfasis` | AC | RLC puros + puerto 50 Ω | **Exacto** (valores del esquema) |
| `led/bias_t_ac` | `LED` | AC | RLC + equivalente de LED (Li 2019) | **Exacto** (valores del esquema) |
| `tx_amplifier/ac`, `tran` | `tx_amplifier` | AC, transitorio | BFR740L3RH + red del esquema | **Fiel** (modelo de fabricante ngspice) |
| `ltc6268-10/ac`, `noise` | `LTC6268-10` | AC, ruido | opamp 2 polos + Rf=3k/Cf=0.2p | Aproximado (macromodelo) |
| `lmh34400/ac`, `noise` | `LMH34400` | AC, ruido | bloque TIA (Zt interno) | Aproximado (macromodelo) |
| `fca/ac`, `tran` | `LumiCom_Transmitter` | AC, transitorio | opamp 2 polos (OPA2675) | Aproximado (macromodelo) |
| `rx_amp/ac` | `rx_amp` | AC | bloque de ganancia 50 Ω / 20 dB | **Placeholder** (sin modelo BGA616 ngspice) |

### Supuestos de los macromodelos

- `opamp_2pole.sub`: parámetros por datasheet. El ruido de entrada se modela con
  resistencias térmicas equivalentes (`en² = 4kT·R`, `in² = 4kT/R`) de modo que
  `.noise` lo contabilice; la rama de ruido de corriente va bufferizada para no
  cargar la entrada de tierra virtual.
- `tia_block.sub` (LMH34400): TIA completa con Rf interna. Se asume
  `Zt = 20 kΩ` y `BW = 240 MHz` (datasheet); `en = 2.35 nV/√Hz` e
  `in = 2.5 pA/√Hz` extraídos del macro-modelo TI.
- LTC6268-10: `GBW = 4 GHz`, `en = 4 nV/√Hz`, `in ≈ 1 fA/√Hz` (entrada CMOS).
- Fotodiodo: `Cd = 5 pF`, `Rsh = 1 GΩ` (representativo de PDB-C154SM/S5971/SFH203).
- `rx_amp`: el modelo BGA616 disponible es una hoja de datos, no un netlist;
  se usa un bloque de ganancia de 50 Ω como marcador de posición.
- `LMH34400` no tiene deck transitorio: el macromodelo no es numéricamente
  estable en `.tran`. El ruido y la respuesta AC sí se simulan.

## Ruido

`sim/ltc6268-10/noise.cir` y `sim/lmh34400/noise.cir` corren `.noise` y generan
`onoise_spectrum`/`inoise_spectrum` y los totales integrados. Los valores
resumidos están en `docs/sim/RESULTS.md`.

Para un modelo de mayor fidelidad de los opamps hay que obtener una versión
ngspice de los modelos de fabricante (TI/ADI) o pasar a un modelo a nivel
transistor, y reemplazar `sim/models/opamp_2pole.sub` y `sim/models/tia_block.sub`.
