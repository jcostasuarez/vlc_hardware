# Revisión de PCB — 2026-09-14

## Alcance y método

Se revisaron las ocho placas nativas del repositorio con KiCad 10.0.6. El DRC
se ejecutó con zonas rellenadas y paridad esquema-placa; los informes versionados
están en `docs/review/drc` (ERC en `docs/review/erc`). Los avisos de biblioteca
se contabilizan por separado de los defectos físicos.

| Placa | Función | ERC | DRC | Estado |
|---|---|---:|---:|---|
| `Receiver/AMP/rx_amp` | Amplificador receptor BGA616, SMA de entrada/salida y alimentación | 0 | 0 | Limpia |
| `Receiver/PD/PD` | Adaptador de fotodiodos PDB-C154SM / S5971 / SFH203, SMA y bias | 0 | 0 | Limpia |
| `Receiver/TIA/LMH34400` | TIA LMH34400 con entradas PD, salida RF y ALC | 0 | 0 | Limpia |
| `Receiver/TIA/LTC6268-10` | TIA LTC6268-10 con entrada PD y salida RF | 0 | 0 | Limpia |
| `Transmitter/AMP/tx_amplifier` | Amplificador de transmisión con SMA y alimentación de 3,3 V | 0 | 0 | Limpia |
| `Transmitter/FCA/LumiCom_Transmitter` | Amplificador/filtro de dos canales con OPA2675; 4 capas | 0 | 0 | Limpia |
| `Transmitter/LED/LED` | Driver/emisor óptico IR, bobina y conectividad RF | 0 | 0 | Limpia |
| `Transmitter/PRE/preenfasis` | Red RF de preénfasis, variantes microstrip/CPW | 0 | 0 | Limpia |

Las ocho placas pasan ERC y DRC con **0 errores y 0 avisos**, incluyendo DRC con
zonas rellenadas, paridad esquema-placa, paridad de bibliotecas de huellas y de
símbolos, y ERC completo.

## Mejoras aplicadas

1. En `Receiver/TIA/LTC6268-10/LTC6268-10.kicad_pcb` se eliminó, mediante la API
   de KiCad, un arco aislado de F.Cu de 0,1341 mm en `Net-(J1-In)`. Era el único
   aviso de cobre funcional (`track_dangling`). La copia previa está en el
   respaldo local `build/backups/2026-09-14/LTC6268-10.kicad_pcb.before-dangling-arc-removal`.
2. En la misma placa se movió el texto de serigrafía `OUT` (F.SilkS) de
   (129,92; 64,50) a (134,42; 65,00) mm para despejar el designador de R3. Sólo
   cambió la posición del texto: ni cobre ni red ni huella.
3. En `Transmitter/LED/LED.kicad_sch` se corrigieron los dos errores ERC de
   metadatos: el cátodo del LED dejó de declararse `output` (ahora `passive`) y
   se añadió un `power:PWR_FLAG` sobre GND, coherente con el resto de esquemas.
4. **Consolidación de bibliotecas de huellas.** Cada una de las ocho placas se
   hizo autocontenida: se extrajo la huella embebida exacta de cada componente y
   se copió a la biblioteca local del proyecto, repuntando el FPID de la placa y
   el campo Footprint del símbolo. Se vendieron 56 tipos de huella; 20 instancias
   estaban ausentes de las bibliotecas instaladas (dos tipos: la SMA
   `SMA_Samtec_SMA-J-P-X-ST-EM1_EdgeMount` y la bornera
   `TerminalBlock_bornier-2_P5.08mm`). Los avisos `lib_footprint_mismatch`
   (110) y `lib_footprint_issues` (20) quedaron en 0. La huella, pads, redes,
   zonas y modelos 3D se copiaron verbatim: los conteos de `footprint`, `pad`,
   `segment`, `via`, `zone`, `gr_line`, `gr_poly`, `gr_text` y `dimension` son
   idénticos a los respaldos, y la estructura de los esquemas no cambió.
5. **Consolidación de bibliotecas de símbolos.** Se aplicó el mismo criterio a
   los esquemas: la definición de símbolo embebida en `lib_symbols` se copió a la
   biblioteca local del proyecto y se repuntó el `lib_id` y el nombre del símbolo
   embebido. Se vendieron 77 referencias de símbolo (23 tipos, entre ellos
   `Connector:Conn_Coaxial`, `Device:C_Small` y varios `power`, más
   `Device:Q_NPN_BCE`, ausente de la biblioteca instalada de KiCad 10). Los
   avisos `lib_symbol_mismatch` (65) y `lib_symbol_issues` (1) quedaron en 0: las
   ocho placas dan **ERC con 0 errores y 0 avisos**. Sólo cambiaron `lib_id` y
   los nombres en `lib_symbols`; los conteos de `symbol`, `wire`, `junction`,
   `label`, `pin`, `polyline` y `text` son idénticos a los respaldos.
6. **Limpieza de paridad esquema-placa.** Se sincronizaron los campos de la
   huella con el esquema (fuente de verdad): 52 campos en 6 placas, en su mayoría
   espacios sobrantes en `Description`/`Datasheet`, más el `Value` de L1/L3/D1.
   Se completó además el `Manufacturer`/`Manufacturer Part Number`/`Mouser Part
   Number` de JP1 en `LTC6268-10`. Los 49 avisos `footprint_symbol_mismatch` y
   `footprint_symbol_field_mismatch` quedaron en 0. Sólo cambiaron valores de
   campos; los conteos físicos y de propiedades son idénticos a los respaldos.
   Para el único aviso restante de atributo, JP1 (jumper de prueba) en
   `LMH34400`, se marcó `dnp yes` en el esquema para que coincida con la huella
   DNP de la placa y se conserve el comportamiento de no poblar.

Herramientas: `scripts/vendor_footprints.py`, `scripts/vendor_symbols.py` y
`scripts/sync_schematic_parity.py`. Los respaldos de cada paso se conservan
localmente (no versionados) en `build/backups/2026-09-14-*`.

Los cambios están verificados con KiCad 10.0.6: las ocho placas dan ERC y DRC con
0 errores y 0 avisos.

## Pendientes antes de fabricar

1. Para las trayectorias RF, confirmar con el fabricante la pila real de 1,2 mm
   y sus dieléctricos. Las placas PRE, AMP, TIA y RX usan SMA y/o trazas RF; la
   impedancia no debe inferirse solamente de la anotación de FR-4.
2. Confirmar la decisión de no poblar JP1 (`Test`) en `LMH34400`; quedó DNP en
   placa y esquema para conservar el estado actual.
