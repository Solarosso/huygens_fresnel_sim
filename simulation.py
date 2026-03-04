import numpy as np


def get_sources(mode, center_y, params):
    sw = max(1, int(params['slit_width']))
    ss = max(sw + 4, int(params['slit_sep']))
    n  = max(2, int(params['n_slits']))
    spacing = max(1, sw // 20)

    if mode == 'single':
        ys = np.arange(center_y - sw // 2, center_y + sw // 2 + 1, spacing, dtype=float)
        return np.column_stack([np.zeros(len(ys)), ys])

    elif mode == 'double':
        parts = []
        for offset in [-ss // 2, ss // 2]:
            ys = np.arange(-sw // 2, sw // 2 + 1, spacing, dtype=float) + center_y + offset
            parts.append(ys)
        ys = np.concatenate(parts)
        return np.column_stack([np.zeros(len(ys)), ys])

    elif mode == 'grating':
        parts = []
        start = center_y - ((n - 1) * ss) // 2
        for i in range(n):
            ys = np.arange(-sw // 2, sw // 2 + 1, spacing, dtype=float) + start + i * ss
            parts.append(ys)
        ys = np.concatenate(parts)
        return np.column_stack([np.zeros(len(ys)), ys])

    elif mode == 'custom':
        custom = params.get('custom_sources', [])
        if not custom:
            return np.array([[0.0, float(center_y)]])
        return np.array([[0.0, float(y)] for y in custom])

    return np.array([[0.0, float(center_y)]])


def compute_field(sources, W, H, wavelength, time):
    k     = 2.0 * np.pi / wavelength
    omega = k

    x  = np.arange(W, dtype=np.float32)
    y  = np.arange(H, dtype=np.float32)
    gx, gy = np.meshgrid(x, y)

    sx = sources[:, 0].astype(np.float32)
    sy = sources[:, 1].astype(np.float32)

    dx = gx[:, :, None] - sx
    dy = gy[:, :, None] - sy
    r  = np.sqrt(dx * dx + dy * dy)
    np.maximum(r, 0.5, out=r)

    amplitude = np.cos(k * r - omega * time) / np.sqrt(r)
    return amplitude.sum(axis=2).astype(np.float32)


def field_to_rgb(field):
    max_val = np.abs(field).max()
    if max_val < 1e-6:
        max_val = 1.0
    norm = (field / max_val).astype(np.float32)

    intensity = norm * norm

    r = np.clip(intensity * 40,       0, 255).astype(np.uint8)
    g = np.clip(norm * 220,           0, 255).astype(np.uint8)
    b = np.where(norm >= 0,
                 norm * 255,
                -norm * 200).clip(0, 255).astype(np.uint8)

    return np.stack([r, g, b], axis=2)
