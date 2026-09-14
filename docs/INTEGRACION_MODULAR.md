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

Los informes de DRC/ERC se generan en `build/review/`. Se eliminó un arco de
cobre colgante en `Receiver/TIA/LTC6268-10`; su respaldo está en
`build/backups/2026-09-14/`.

La placa LED tenía dos errores ERC de metadatos de símbolo: GND no declaraba la
fuente externa y los cátodos de LEDs se definieron como salidas. Ambos se
corrigieron en `Transmitter/LED/LED.kicad_sch` (cátodo `passive` y `PWR_FLAG`
sobre GND).

Las bibliotecas de huellas y de símbolos quedaron consolidadas: cada proyecto es
autocontenido y las definiciones embebidas se copiaron verbatim a la biblioteca
local de su proyecto. Se limpió además la paridad esquema-placa sincronizando los
campos de la huella con el esquema. Las herramientas son
`build/audit/vendor_footprints.py`, `build/audit/vendor_symbols.py` y
`build/audit/sync_schematic_parity.py`; los respaldos están en
`build/backups/2026-09-14-library-consolidation/`,
`build/backups/2026-09-14-symbol-consolidation/` y
`build/backups/2026-09-14-parity-cleanup/`.

Las ocho placas dan ERC y DRC con 0 errores y 0 avisos. Pendiente de fabricación:
confirmar la pila RF de 1,2 mm y la decisión de no poblar JP1 en `LMH34400`; ver
`build/review/REPORTE_REVISION.md`.
