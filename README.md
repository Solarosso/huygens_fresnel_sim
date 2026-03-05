# Huygens–Fresnel Principle Simulation

An interactive 2D wave diffraction simulator built with Python and Pygame, demonstrating the Huygens–Fresnel principle across four aperture configurations.

## What it simulates

Every point on a wavefront acts as a secondary spherical source (Huygens wavelet). The total field at any observation point is the superposition of all these secondary waves:

$$E(x, y, t) = \sum_{i} \frac{1}{\sqrt{r_i}} \cos(k r_i - \omega t)$$

where $r_i$ is the distance from the $i$-th secondary source to the observation point, $k = 2\pi/\lambda$ is the wavenumber, and $\omega = k$ (normalized wave speed).

## Modes

| Mode | Description |
|---|---|
| **Single Slit** | Classic single-slit diffraction — observe the central maximum and side lobes |
| **Double Slit** | Young's double-slit interference — interference fringes in the far field |
| **N-Slit Grating** | Diffraction grating with 2–10 slits — sharper maxima as N increases |
| **Custom Draw** | Left-click to place secondary sources anywhere on the aperture line |

## Controls

| Input | Action |
|---|---|
| Mode buttons | Switch simulation mode |
| Wavelength slider | Change λ (15–60 px) |
| Slit Width slider | Aperture opening size |
| Slit Spacing slider | Separation between slits |
| Num Slits slider | Number of slits (grating mode) |
| Speed slider | Animation speed |
| `SPACE` | Pause / Resume |
| `R` | Reset time to 0 |
| `W` | Toggle Huygens wavelet circles |
| Left-click (custom) | Add secondary source |
| Right-click (custom) | Clear all sources |

The **I(y)** panel on the right shows the instantaneous intensity profile at the far field (rightmost column of the simulation grid).

## Installation

```bash
git clone https://github.com/Solarosso/huygens-fresnel-sim.git
cd huygens-fresnel-sim

pip install -r requirements.txt

python main.py
```

Tested on Ubuntu 20.04 with Python 3.8+.

## Project structure

```
huygens-fresnel-sim/
├── main.py          # Pygame application, UI, rendering
├── simulation.py    # Wave physics (numpy-vectorized)
├── requirements.txt
└── README.md
```

## Performance notes

The field is computed on a 550×330 grid using fully vectorized numpy operations (no Python loops over observation points). With ~50 secondary sources this runs at ~25 fps. Enabling wavelet circles reduces FPS slightly. If performance is low, reduce the wavelength (fewer sources) or disable wavelets.

## Theory

- **Near field (Fresnel regime):** $z \ll a^2/\lambda$ — complex curved wavefronts, computed correctly here
- **Far field (Fraunhofer regime):** $z \gg a^2/\lambda$ — intensity pattern matches the Fourier transform of the aperture function

The single-slit far-field pattern converges to the expected $\text{sinc}^2(\beta)$ envelope, and the double-slit pattern produces the classic $\cos^2$ fringes modulated by the sinc² envelope.

## License

MIT
