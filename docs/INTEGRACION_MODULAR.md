# Integración modular VLC

## Arquitectura y selección

La cadena de transmisión es `PRE` -> `AMP` **o** `FCA` -> `LED`.  La cadena de
recepción es `PD` -> **una sola** placa `TIA` (`LMH34400` **o** `LTC6268-10`)
-> `rx_amp` -> instrumento/ADC.

No instalar ambas TIA en la misma cadena.  La selección se realiza antes de
cablear: los componentes, los valores y los jumpers de cada variante se
conservan tal como están en sus esquemas.  En particular, no se ha supuesto una
impedancia de pista ni una pila de fabricación que el fabricante no haya
confirmado.

## Cableado entre módulos

Usar cables coaxiales SMA de 50 ohmios, cortos, exclusivamente para señal RF.
Conectar primero todos los retornos de chasis/GND y las borneras de alimentación,
y después los SMA con la alimentación desconectada.  Nunca aplicar tensión DC a
un SMA.

1. Conectar la salida SMA de PRE a la entrada SMA de AMP o FCA.
2. Conectar la salida SMA del driver elegido a la entrada SMA de la placa LED.
3. En recepción, conectar el SMA de la placa PD al SMA de entrada de la TIA
   elegida; conectar la salida RF de esa TIA a la entrada de `rx_amp`.
4. Conectar la salida SMA de `rx_amp` al osciloscopio de 50 ohmios o al ADC que
   presente la terminación especificada por el diseño.

Cada bornera se reserva para alimentación/bias y GND; comprobar polaridad contra
la serigrafía y el esquema antes de energizar.  `tx_amplifier` etiqueta su rail
como `+3.3V`. Las demás placas etiquetan sus rails como `VCC`, `Vdc` o `Vout`:
la tensión numérica, corriente disponible y polaridad en J1/J3/J5 deben
confirmarse contra la revisión de esquema y la hoja de datos del componente que
alimente la placa. No se ha inferido ninguna de esas tensiones.

## Notas de layout y montaje

- Mantener el plano de GND continuo bajo RF; no dejar stubs ni añadir vías en la
  ruta RF sin recalcular la impedancia para la pila real.
- Añadir vías de cosido GND junto a SMA/CPW sólo tras confirmar el stack-up,
  diámetro de vía y separación del fabricante.
- En PD/TIA, montar el fotodiodo y el TIA contiguos; mantener el nodo de entrada
  de alta impedancia corto, limpio y separado de la salida RF y del LED.
- En LED, el lazo `bornera -> L1 -> LED -> GND` debe ser compacto y de cobre
  acorde a la corriente de LED validada. Los conectores J1/J2 están acoplados
  por C1/C2; la alimentación entra por J3, no por SMA.
- La placa LED contiene las opciones LED1 (SFH 47167B) y LED2
  (XPERED-L1-0000-00501). La documentación disponible no establece cuál debe
  montarse ni si una debe quedar DNP; no poblar ambas sin confirmación de la
  configuración óptica y de corriente.

## Estado de revisión

Los informes de DRC/ERC versionados están en `docs/review/` y el informe completo
en `docs/REVISION_PCB.md`. Se eliminó un arco de cobre colgante en
`Receiver/TIA/LTC6268-10`; su respaldo local está en `build/backups/2026-09-14/`.

La placa LED tenía dos errores ERC de metadatos de símbolo: GND no declaraba la
fuente externa y los cátodos de LEDs se definieron como salidas. Ambos se
corrigieron en `Transmitter/LED/LED.kicad_sch` (cátodo `passive` y `PWR_FLAG`
sobre GND).

Las bibliotecas de huellas y de símbolos quedaron consolidadas: cada proyecto es
autocontenido y las definiciones embebidas se copiaron verbatim a la biblioteca
local de su proyecto. Se limpió además la paridad esquema-placa sincronizando los
campos de la huella con el esquema. Las herramientas son
`scripts/vendor_footprints.py`, `scripts/vendor_symbols.py` y
`scripts/sync_schematic_parity.py`; los respaldos de cada paso se conservan
localmente (no versionados) en `build/backups/2026-09-14-*`.

Las ocho placas dan ERC y DRC con 0 errores y 0 avisos. Pendiente de fabricación:
confirmar la pila RF de 1,2 mm y la decisión de no poblar JP1 en `LMH34400`; ver
`docs/REVISION_PCB.md`.

## Cadena de excitación del LED (recomendación)

La cadena propuesta —Pitaya → preénfasis → FCA → amplificador discreto → LED— se
puede simplificar y conviene ajustarla:

1. **Un solo driver.** Encadenar FCA + `tx_amplifier` suma ruido y distorsión y
   recorta banda. La simulación de sistema lo muestra: con el amplificador
   discreto la corriente de LED pica a ≈52 MHz; con la FCA pica a ≈0,94 MHz,
   porque su red de entrada R7/C6 (49,9 Ω / 0,1 µF) corta en ≈32 kHz.
2. **Preénfasis una sola vez.** Mejor en digital dentro de la FPGA de la Red
   Pitaya (ajustable, sin dispersión de componentes) y dejar una única etapa
   analógica de adaptación. Si se hace en analógico, usar el filtro `PRE` y no
   repetirlo.
3. **El bias-tee va en la placa LED** (`J3 → L1 → nodo del LED`, con `C1`/`C2`
   acoplando `J1`/`J2`). Es la forma correcta de sumar polarización DC y RF, pero
   fija un pasabanda de ≈0,7 MHz a ≈39 MHz; para otra banda hay que redimensionar
   L1 y C1/C2. El último estado del driver debe ser de corriente con polarización DC. Un
   LED común necesita decenas a cientos de mA y tiene impedancia dinámica de
   pocos ohmios (≈1–5 Ω). Un amplificador de tensión adaptado a 50 Ω entrega muy
   poca corriente de modulación (≈1 mA/V según la simulación). Usar el lazo
   `bornera → L1 → LED → GND` de la placa LED como bias-T y un driver con
   capacidad de corriente: la **FCA (OPA2675)** tiene la salida de corriente para
   esto; el **`tx_amplifier` (BFR740L3RH)** es un transistor de RF pequeño, sirve
   como pre-driver, no como driver de potencia.
4. **Límites reales del LED.** El ancho de banda de un LED común lo fijan el
   tiempo de vida de portadores y el RC (unos pocos a decenas de MHz). El
   preénfasis extiende el −3 dB a costa de rango dinámico; para más velocidad
   conviene un LED azul/IR de baja capacidad o un láser.
5. **Validar contra mediciones.** El repositorio ya tiene 74 mediciones `.s2p`
   en `vna/`; conviene superponerlas con las respuestas simuladas (`sim/system`).

Cadena recomendada:

```
Red Pitaya (preénfasis digital en FPGA)
   └─ 50 Ω ─► [PRE analógico opcional] ─► driver DC (FCA/OPA2675)
        └─ bias-T (L1) + acople (C1) ─► LED
Rx: PD ─► TIA (LMH34400) ─► rx_amp ─► ADC/osciloscopio
```
