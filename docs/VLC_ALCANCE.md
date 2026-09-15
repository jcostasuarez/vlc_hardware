# Alcance del enlace VLC (LED + fotodiodo comerciales)

Con un LED y un fotodiodo baratos, la comunicación sólo funciona con el LED y el
PD casi pegados. El balance de enlace lo explica: con PD desnudo, 10 mA de
modulación y 50 MHz de ancho de banda, un SNR de 10 dB se logra a **≈6 cm**. No
es un problema de "adaptación de impedancia" solamente: es un problema de
**presupuesto óptico y de ruido del receptor**.

`scripts/vlc_link_budget.py` calcula esto (parámetros al inicio del script):

```
LED:  eta=1 W/A, i_led=10 mA, m=1, 850 nm
PD:   R=0.6 A/W, area=1 mm^2, Cj=5 pF
RX:   ruido de entrada 27 pA/√Hz, B=50 MHz
```

| Caso | Distancia para SNR=10 dB |
|---|---:|
| PD desnudo, B=50 MHz | **0,06 m** |
| Lente 25 mm sobre el PD, B=50 MHz | 1,04 m |
| Lente 25 mm, B=10 MHz (canal angosto) | 1,56 m |
| Lente 25 mm, B=1 MHz | 2,77 m |
| Lente 50 mm, B=10 MHz | 3,12 m |
| APD (G≈20) + lente 25 mm, B=10 MHz | 6,97 m |

Regla clave: `i_pd ∝ 1/d²` y por lo tanto **`SNR ∝ 1/d⁴`**. Duplicar la distancia
cuesta 12 dB. Todo lo que sume dB en el presupuesto óptico rinde mucho.

## Prioridades para ganar distancia

1. **Óptica en el receptor (lo de mayor impacto).** Una lente delgada sobre el
   PD concentra la luz; la ganancia ≈ `(D_lente/d_PD)²·η`. Una lente de 25 mm
   sobre un PD de 1 mm² da **+25 dB**; 50 mm, +31 dB. Hay que **alinear** y que
   el ángulo de emisión del LED entre en el campo de visión del PD. Un
   concentrador tipo CPC o un reflector parabólico son alternativas.
2. **Filtrado y receptor angosto.** Un filtro óptico pasa-banda IR (o rojo)
   delante del PD rechaza luz ambiente. Del lado eléctrico, un **filtro
   pasa-banda en la portadora** reduce el ruido fuera de banda: el ruido cae con
   `√B`, así que pasar de 50 MHz a 1 MHz mejora ~17 dB. Para un canal de 50 MHz
   centrado en una portadora, usar un receptor resonante.
3. **Más luz del LED, más directiva.** Subir la corriente de modulación (límite
   térmico), usar un LED **IR 850/940 nm** (mejor acople con un PD de Si que un
   LED blanco de fósforo) y un LED de **haz angosto** (mayor orden lambertiano
   `m`: la intensidad en eje crece con `m+1`).
4. **Menos ruido en el receptor.** El ruido de entrada del TIA es el que fija el
   mínimo detectable. Conviene un **TIA CMOS de baja corriente de ruido** (el
   `LTC6268-10` es CMOS; el `LMH34400` es bipolar, más ruidoso en corriente) y
   **maximizar la transimpedancia** (subir `Rf`, o usar la ganancia integrada de
   40 kΩ del LMH34400) hasta donde el ancho de banda lo permita.
5. **Minimizar la capacidad del PD.** PD más chico (o con polarización inversa)
   y **PD y TIA pegados** (pistas cortas, sin cable SMA entre medio). La
   capacidad del PD es la que fija el ancho de banda y el ruido del TIA:
   `B ∝ 1/(Rf·C)` y `ruido ∝ √C`. Hay un compromiso **sensibilidad ↔ ancho de
   banda**.

## ¿Falta adaptar alguna impedancia?

Sí, pero **no con el paradigma de 50 Ω**:

- **TX (LED):** el LED es de baja impedancia y no lineal (≈1–5 Ω). Adaptar el
  driver a 50 Ω **desperdicia potencia**. Lo correcto es un **driver de corriente**
  o una red de adaptación (LC o transformador) que transforme los 50 Ω del driver
  a los pocos ohmios del LED, para que más corriente de modulación llegue al LED.
  La placa LED ya tiene el bias-tee (`L1` + `C1`/`C2`); ajustá `L1`/`C1` para la
  banda.
- **RX (PD → TIA):** el PD es una fuente de corriente capacitiva y la entrada del
  TIA es tierra virtual; no se "matchea a 50 Ω". Lo que ayuda es:
  - **resonar la capacidad del PD** con un inductor en paralelo (o red LC) en la
    portadora → sube la impedancia de entrada justo en la frecuencia útil
    (canal angosto);
  - **inductive peaking / T-coil** para extender el ancho de banda;
  - **cortar el cable SMA** entre PD y TIA (cada cm de cable suma capacidad y
    reflexiones).

En `sim/system/link_channel.cir` y `optical_channel.cir` la ganancia óptica está
parametrizada: `.param G=<lente>` (por defecto 1). Con `G=344` (lente de 25 mm)
el enlace mejora 25 dB y el alcance escala con `√G`.

## Qué tocaría en estas placas

1. Agregar **lente/concentrador** y filtro óptico IR en la placa PD.
2. **Pegar el PD al TIA** (misma placa o conexión cortísima) y bajar `Cd`
   (polarizar el PD).
3. En recepción, para un canal angosto de 50 MHz, agregar **red resonante** en la
   entrada del TIA y un **pasa-banda** a la salida (antes del `rx_amp`).
4. En transmisión, usar la **FCA/OPA2675 como driver de corriente** con red de
   adaptación al LED (no 50 Ω directo) y preénfasis digital en la Red Pitaya.
5. Si hace falta más alcance, **APD** (ganancia interna) o un PD pre-amplificado.
