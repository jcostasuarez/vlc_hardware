# Simulaciones ngspice

Suite única de simulación para las placas VLC, reproducible y sin GUI. Reemplaza
las simulaciones dispersas en LTspice (`.asc`) y OrCAD PSpice (`-PSpiceFiles`)
por decks **ngspice** derivados de los esquemas KiCad.

## Cómo correr

```bash
scripts/run_all_sims.sh                        # toda la suite -> build/sim/
python3 scripts/run_spice.py sim/ltc6268-10/noise.cir --outdir build/sim --noise
python3 scripts/summarize_sims.py build/sim    # métricas -> docs/sim/RESULTS.md
```

`scripts/run_spice.py` maneja la `libngspice` que viene con KiCad vía `ctypes`
(no hace falta un binario `ngspice`). Antes de cargar cada deck hace
`set ngbehavior=ltpsa` (compatibilidad PSpice/LTspice). Los resultados van a
`build/sim/` (ignorado por git).

## Estructura

```
sim/models/opamp_2pole.sub        opamp de dos polos (datasheet) [fallback]
sim/models/tia_block.sub          bloque TIA sobre opamp_2pole  [fallback]
sim/models/bfr740l3rh.lib         Infineon BFR740L3RH (nativo)
sim/models/lmh34400.lib           TI LMH34400, convertido a ngspice (nativo)
sim/models/opa2675.lib            TI OPA2675, convertido a ngspice (nativo)
sim/models/bga616.lib             BGA616, bloque de ganancia 50 Ω (datasheet)
sim/<placa>/<análisis>.cir        decks de análisis
```

## Modelos

Los modelos de fabricante son específicos de cada herramienta. Estado por placa:

| Deck | Placa | Modelo | Estado |
|---|---|---|---|
| `preenfasis/filtro_t_ac` | `preenfasis` | RLC puros + puerto 50 Ω | exacto (valores del esquema) |
| `led/bias_t_ac` | `LED` | RLC + equivalente de LED (Li 2019) | exacto (valores del esquema) |
| `tx_amplifier/ac`, `tran` | `tx_amplifier` | Infineon **BFR740L3RH** (Gummel-Poon) | **fabricante, nativo** |
| `lmh34400/ac`, `noise` | `LMH34400` | TI **LMH34400** macro-modelo | **fabricante, convertido** |
| `fca/ac`, `tran` | `LumiCom_Transmitter` | TI **OPA2675** macro-modelo | **fabricante, convertido** |
| `rx_amp/ac` | `rx_amp` | **BGA616** bloque de ganancia 50 Ω | datasheet (sin netlist público) |
| `ltc6268-10/ac`, `noise` | `LTC6268-10` | opamp 2 polos + Rf/Cf | datasheet (ADI solo da LTspice) |

### Conversión de modelos PSpice → ngspice

`scripts/convert_vendor_model.py` traduce los modelos TI (sbom…):

- `.MODEL … VSWITCH ROFF/RON/VOFF/VON` → `.MODEL … SW(Roff/Ron/Vt/Vh)`
- `.MODEL … ISWITCH ROFF/RON/IOFF/ION` → `.MODEL … CSW(Roff/Ron/It/Ih)`
- `PWR(x,y)` → `((x)**(y))`
- descarta `noiseless` y `T_ABS`

Genera `sim/models/lmh34400.lib` y `sim/models/opa2675.lib` desde los `.lib`
originales del repo. Con eso los dos corren 100 % en ngspice y aportan su propio
ruido interno. El LMH34400 reproduce la ganancia integrada de 40 kΩ (≈20 kΩ
entregados a 50 Ω) y el OPA2675 la ganancia cerrada de 4,02.

### Modelos no nativos

- **LTC6268-10**: Analog Devices solo publica el modelo de LTspice, que usa
  devices `A` (OTA/SCHMITT/BUF) y `dnlim/uplim` inexistentes en ngspice. Se usa
  el macromodelo de dos polos de `sim/models/opamp_2pole.sub` con los datos del
  datasheet (GBW 4 GHz, en 4 nV/√Hz, in ≈ 1 fA/√Hz, Cin 1.5 pF).
- **BGA616**: Infineon no publica un netlist; el datasheet solo da el circuito
  equivalente de encapsulado y los parámetros 2G.6. `sim/models/bga616.lib`
  reproduce el comportamiento de gain block de 50 Ω y 19 dB (DC–2,7 GHz).

## Supuestos

- Fotodiodo: `Cd = 1 pF` (condición de datasheet del LMH34400) o `5 pF` en el
  LTC6268-10.
- LMH34400: ALC activo; el contenido bajo ≈400 kHz se rechaza, por eso el ruido
  se integra desde 100 kHz.
- LTC6268-10: `Rf = 3 kΩ`, `Cf = 0.2 pF` (valores del esquema).

## Ruido

`.noise` está en `sim/lmh34400/noise.cir` (modelo TI nativo) y
`sim/ltc6268-10/noise.cir` (macromodelo). `docs/sim/RESULTS.md` reporta densidad
espectral a 1 MHz e integrada sobre la banda.
