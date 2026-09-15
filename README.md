# VLC Hardware — Comunicación por Luz Visible

Hardware abierto (KiCad) de una cadena de comunicación por luz visible (VLC):
transmisor óptico, receptor óptico de alta sensibilidad y placas de
acondicionamiento RF. Proyecto final de la carrera de Ingeniería Electrónica,
UTN FRBA.

Cada placa es un módulo independiente que se interconecta con cables coaxiales
SMA de 50 Ω. Todos los proyectos son **autocontenidos**: las huellas y los
símbolos están embebidos y copiados en la biblioteca local de cada proyecto, de
modo que se abren y verifican sin depender de bibliotecas externas.

## Arquitectura

```
Transmisor:   PRE ──► AMP ─┐
                         ├──► LED ──► (espacio libre, luz IR)
              PRE ──► FCA ─┘

Receptor:     PD ──► TIA ──► rx_amp ──► osciloscopio / ADC
```

- **TX**: `PRE` (red de preénfasis) excita a `AMP` **o** a `FCA`; el driver
  elegido alimenta la placa `LED`.
- **RX**: `PD` (fotodiodo + bias) entra a **una sola** placa `TIA`
  (`LMH34400` **o** `LTC6268-10`) y su salida pasa por `rx_amp`.
- **No instalar ambas TIA** en la misma cadena.

Detalle de cableado, alimentación y layout en
[docs/INTEGRACION_MODULAR.md](docs/INTEGRACION_MODULAR.md).

## Placas

| Proyecto | Ruta | Función |
|---|---|---|
| `rx_amp` | `Receiver/AMP/` | Amplificador receptor BGA616, SMA de entrada/salida y alimentación |
| `PD` | `Receiver/PD/` | Adaptador de fotodiodos PDB-C154SM / S5971 / SFH203, SMA y bias |
| `LMH34400` | `Receiver/TIA/LMH34400/` | TIA LMH34400 con entradas PD, salida RF y ALC |
| `LTC6268-10` | `Receiver/TIA/LTC6268-10/` | TIA LTC6268-10 con entrada PD y salida RF |
| `tx_amplifier` | `Transmitter/AMP/` | Amplificador de transmisión con SMA y alimentación de 3,3 V |
| `LumiCom_Transmitter` | `Transmitter/FCA/` | Amplificador/filtro de dos canales con OPA2675 (4 capas) |
| `LED` | `Transmitter/LED/` | Driver/emisor óptico IR, bobina y conectividad RF |
| `preenfasis` | `Transmitter/PRE/` | Red RF de preénfasis (variantes microstrip/CPW) |

## Estructura del repositorio

```
Receiver/AMP/            rx_amp.kicad_{pcb,sch} + library/
Receiver/PD/             PD.kicad_{pcb,sch} + Library/
Receiver/TIA/LMH34400/   LMH34400.kicad_{pcb,sch} + Library/
Receiver/TIA/LTC6268-10/ LTC6268-10.kicad_{pcb,sch} + Library/
Transmitter/AMP/         tx_amplifier.kicad_{pcb,sch} + footprints/
Transmitter/FCA/         LumiCom_Transmitter.kicad_{pcb,sch} + Library/
Transmitter/LED/         LED.kicad_{pcb,sch} + library/
Transmitter/PRE/         preenfasis.kicad_{pcb,sch} + library/
vna/                     Mediciones de red (VNA), calibraciones y scripts de análisis
docs/                    Integración, revisión y evidencias (ERC/DRC)
scripts/                 Exportación reproducible y herramientas de mantenimiento
```

Cada proyecto incluye su `fp-lib-table` y `sym-lib-table` que registran su
biblioteca local (`library/` o `Library/`).

## Requisitos

- [KiCad 10.0.6](https://www.kicad.org/) con `kicad-cli` en el `PATH`
  (variable `KICAD_CLI` para apuntar a otra ruta).
- Python 3 (sólo para las herramientas de `scripts/`).

## Generar revisión y fabricación

```bash
scripts/export_review.sh Receiver/TIA/LTC6268-10
```

Genera en `build/fabrication/<proyecto>/`:

- `erc.rpt`, `drc.rpt` y sus variantes de sólo errores;
- `schematic.pdf`, `layout.pdf`;
- `gerbers/` (Gerber + taladro Excellon);
- `positions.csv` (pick & place);
- `top.png`, `bottom.png` (render 3D) y `layers/board.svg`.

El script **falla** si ERC o DRC reportan errores. Con `STRICT=1` también falla
ante avisos.

## Simulaciones (ngspice)

Todas las simulaciones están unificadas en una única suite **ngspice**,
reproducible y sin GUI (`sim/`):

```bash
scripts/run_all_sims.sh                        # corre todo -> build/sim/
python3 scripts/run_spice.py sim/ltc6268-10/noise.cir --outdir build/sim --noise
python3 scripts/summarize_sims.py build/sim    # métricas -> docs/sim/RESULTS.md
```

`scripts/run_spice.py` usa la `libngspice` que viene con KiCad vía `ctypes`; no
requiere un binario `ngspice`. Incluye respuesta en frecuencia, transitorios y
**análisis de ruido** de las TIA (`lmh34400`, `ltc6268-10`). Los modelos TI
(LMH34400, OPA2675) y el BFR740 corren nativos, con los PSpice convertidos por
`scripts/convert_vendor_model.py`. Los supuestos y la fidelidad de cada deck
están en [sim/README.md](sim/README.md), y los resultados en
[docs/sim/RESULTS.md](docs/sim/RESULTS.md).

Además de cada placa, `sim/system/` interconecta la cadena completa
(`tx_chain`, `tx_chain_fca`, `rx_chain`, `link`, `link_channel`) con interfaces de
50 Ω, incluido el **canal óptico LED → fotodiodo con distancia paramétrica**. El
presupuesto de enlace y cómo ganar alcance están en
[docs/VLC_ALCANCE.md](docs/VLC_ALCANCE.md) (`scripts/vlc_link_budget.py`).

## Estado de revisión

Las ocho placas pasan **ERC y DRC con 0 errores y 0 avisos**, incluyendo DRC con
zonas rellenadas, paridad esquema-placa y paridad de bibliotecas de huellas y
símbolos. Los informes versionados están en
[docs/review/](docs/review/) y el informe completo en
[docs/REVISION_PCB.md](docs/REVISION_PCB.md).

Pendientes antes de fabricar:

1. Confirmar con el fabricante la pila real de 1,2 mm y sus dieléctricos para las
   trayectorias RF (placas `PRE`, `AMP`, TIA y `RX`).
2. Confirmar la decisión de no poblar `JP1` (`Test`) en `LMH34400`.

## Herramientas de mantenimiento

| Script | Uso |
|---|---|
| `scripts/summarize_netlists.py` | Resumen por placa de conectores, rieles y redes de alimentación |
| `scripts/vendor_footprints.py` | Copia las huellas embebidas a la biblioteca local y repunta los FPID |
| `scripts/vendor_symbols.py` | Copia los símbolos embebidos a la biblioteca local y repunta los `lib_id` |
| `scripts/sync_schematic_parity.py` | Sincroniza los campos de huella con el esquema (paridad) |

Todos aceptan modo *dry-run* (sin `--write`).

## Créditos

- Cotti, Nicolás Gabriel — `ncotti@frba.utn.edu.ar`
- UTN FRBA — Proyecto Final de Ingeniería Electrónica
