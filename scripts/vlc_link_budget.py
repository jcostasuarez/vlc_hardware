#!/usr/bin/env python3
"""VLC link budget with cheap LEDs / photodiodes.

Computes the received photocurrent, electrical SNR and the reachable distance
for a line-of-sight Lambertian link, and shows the effect of a collecting lens,
a narrower electrical bandwidth and an avalanche (or pre-amplified) detector.

Model
-----
  LED optical power (modulated)      p_tx = eta * i_led            [W]
  LOS channel gain (on axis)         H(d) = (m+1) * A_pd / (2*pi*d^2)
  Received optical power             p_rx = p_tx * H(d) * G      [W]
  Photocurrent                       i_pd = R * p_rx              [A]
  Receiver noise                     i_n  = in_A * sqrt(B)        [A rms]
  SNR                               = (i_pd / i_n)^2

  d_max(SNR) = sqrt( R*eta*i_led*G*(m+1)*A_pd / (2*pi*in_A*sqrt(B)*sqrt(SNR)) )

All parameters are documented defaults; override them at the top.
"""
import math

# --- LED -------------------------------------------------------------------
ETA = 1.0          # radiant flux per drive current [W/A]
M = 1.0            # Lambertian order (1 = ideal cosine emitter)
I_LED = 10e-3      # modulation current [A rms]
LAMBDA = 850e-9    # wavelength [m]

# --- photodiode ------------------------------------------------------------
R = 0.60           # responsivity at 850 nm [A/W]  (Si PIN)
A_PD = 1e-6        # active area [m^2]  (1 mm^2)
C_PD = 5e-12       # junction capacitance [F]

# --- optics ----------------------------------------------------------------
G_BARE = 1.0
# 25 mm lens over a 1 mm^2 detector: G ~ (D_lens/d_pd)^2 * eff
def lens_gain(d_lens_m, eff=0.7):
    d_pd = math.sqrt(4 * A_PD / math.pi)
    return eff * (d_lens_m / d_pd) ** 2

G_LENS = lens_gain(25e-3)

# --- receiver --------------------------------------------------------------
IN_A = 2.7e-11     # input-referred current noise [A/sqrt(Hz)]  (from sims)
BW = 50e6          # electrical bandwidth [Hz]
TARGET_SNR_DB = 10.0


def channel(d):
    return (M + 1) * A_PD / (2 * math.pi * d * d)


def electrical(bw, g, snr_db=TARGET_SNR_DB):
    """Return (i_pd, i_noise, snr_db) at 1 m for the given optics/bandwidth."""
    i_pd = R * ETA * I_LED * channel(1.0) * g
    i_n = IN_A * math.sqrt(bw)
    return i_pd, i_n, 20 * math.log10(i_pd / i_n)


def dmax(g, bw, snr_db=TARGET_SNR_DB):
    snr = 10 ** (snr_db / 10)
    num = R * ETA * I_LED * g * channel(1.0)
    den = IN_A * math.sqrt(bw) * math.sqrt(snr)
    return math.sqrt(num / den)


def main():
    print('=== VLC link budget (line-of-sight, cheap LED + PIN photodiode) ===')
    print(f'LED: eta={ETA} W/A, i_led={I_LED*1e3:.0f} mA, m={M}, lambda={LAMBDA*1e9:.0f} nm')
    print(f'PD:  R={R} A/W, area={A_PD*1e6:.1f} mm^2, Cj={C_PD*1e12:.0f} pF')
    print(f'RX:  in={IN_A*1e12:.1f} pA/sqrt(Hz), B={BW/1e6:.0f} MHz')
    print(f'Optics: bare G=1 ; 25 mm lens over the PD G={G_LENS:.0f} '
          f'+{10*math.log10(G_LENS):.1f} dB')
    print()
    i1, in1, snr1 = electrical(BW, G_BARE)
    print(f'At d = 1 m, bare PD: i_pd={i1*1e9:.3g} nA, i_n={in1*1e9:.1f} nA, '
          f'SNR={snr1:.1f} dB')
    print()
    print('Reachable distance for SNR = %.0f dB:' % TARGET_SNR_DB)
    print(f'  {"caso":44} {"d_max":>9}')
    cases = [
        ('PD desnudo, B=50 MHz', G_BARE, 50e6),
        ('lente 25 mm, B=50 MHz', G_LENS, 50e6),
        ('lente 25 mm, B=10 MHz (canal angosto)', G_LENS, 10e6),
        ('lente 25 mm, B=1 MHz', G_LENS, 1e6),
        ('lente 50 mm, B=10 MHz', lens_gain(50e-3), 10e6),
        ('APD (G_av=20) + lente 25 mm, B=10 MHz', 20 * G_LENS, 10e6),
    ]
    for name, g, bw in cases:
        print(f'  {name:44} {dmax(g, bw):8.2f} m')

    print()
    print('SNR vs distancia (canal de 50 MHz):')
    print(f'  {"d [m]":>7} {"SNR desnudo":>13} {"SNR +lente 25mm":>16}')
    for d in [0.05, 0.1, 0.2, 0.5, 1.0, 2.0]:
        h = channel(d)
        for label, g in (('bare', G_BARE), ('lens', G_LENS)):
            i_pd = R * ETA * I_LED * h * g
            snr = 20 * math.log10(i_pd / (IN_A * math.sqrt(50e6))) if i_pd > 0 else -999
            if label == 'bare':
                row = f'{d:>7.2f} {snr:>13.1f}'
            else:
                print(row + f' {snr:>16.1f}')


if __name__ == '__main__':
    main()
