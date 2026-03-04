import pygame
import numpy as np
import sys
from simulation import get_sources, compute_field, field_to_rgb

pygame.init()

WIN_W, WIN_H = 1100, 660
SIDEBAR_W    = 230
PROF_W       = 90
FIELD_W      = WIN_W - SIDEBAR_W - PROF_W
GRID_W       = FIELD_W // 2
GRID_H       = WIN_H  // 2
FPS_TARGET   = 25

BG      = (5,   9,  15)
PANEL   = (10,  16, 28)
BORDER  = (24,  40, 60)
WAVE_C  = (0,  220, 255)
TEXT_C  = (160, 195, 215)
LABEL_C = (70,  115, 145)
WHITE   = (230, 242, 250)
BTN_ACT = (0,   80, 110)
BARRIER = (28,  55, 75)

MODES       = ['single', 'double', 'grating', 'custom']
MODE_LABELS = ['Single Slit', 'Double Slit', 'N-Slit Grating', 'Custom Draw']


class Slider:
    def __init__(self, x, y, w, label, lo, hi, val, fmt='{:.0f}'):
        self.track = pygame.Rect(x, y, w, 3)
        self.label = label
        self.lo, self.hi = lo, hi
        self.val = float(val)
        self.fmt = fmt
        self.dragging = False

    @property
    def handle_x(self):
        t = (self.val - self.lo) / (self.hi - self.lo)
        return int(self.track.x + t * self.track.w)

    def hit(self, pos):
        hx = self.handle_x
        return abs(pos[0] - hx) <= 9 and abs(pos[1] - self.track.centery) <= 9

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.hit(event.pos):
            self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            t = (event.pos[0] - self.track.x) / self.track.w
            self.val = self.lo + max(0.0, min(1.0, t)) * (self.hi - self.lo)

    def draw(self, surf, font):
        pygame.draw.rect(surf, BORDER, self.track, border_radius=2)
        hx = self.handle_x
        fill = pygame.Rect(self.track.x, self.track.y, hx - self.track.x, self.track.h)
        pygame.draw.rect(surf, (0, 100, 140), fill, border_radius=2)
        pygame.draw.circle(surf, WAVE_C, (hx, self.track.centery), 6)
        pygame.draw.circle(surf, PANEL,  (hx, self.track.centery), 3)

        lbl = font.render(self.label, True, LABEL_C)
        val = font.render(self.fmt.format(self.val), True, WHITE)
        surf.blit(lbl, (self.track.x, self.track.y - 16))
        surf.blit(val, (self.track.right - val.get_width(), self.track.y - 16))


class App:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption('Huygens–Fresnel Principle Simulation')
        self.clock = pygame.time.Clock()

        self.font_s = pygame.font.SysFont('monospace', 11)
        self.font_m = pygame.font.SysFont('monospace', 13)
        self.font_b = pygame.font.SysFont('monospace', 14, bold=True)

        self.mode          = 'single'
        self.t             = 0.0
        self.paused        = False
        self.show_wavelets = True
        self.sources       = np.array([[0.0, float(GRID_H // 2)]])
        self.field         = None
        self.field_surf    = None
        self.custom_ys     = []
        self.wavelet_surf  = pygame.Surface((FIELD_W, WIN_H), pygame.SRCALPHA)

        P  = SIDEBAR_W - 28
        sx = 14
        self.sliders = [
            ('wavelength', Slider(sx, 182, P, 'Wavelength',    15,  60,  28)),
            ('slit_width', Slider(sx, 242, P, 'Slit Width',     8, 100,  35)),
            ('slit_sep',   Slider(sx, 302, P, 'Slit Spacing',  20, 180,  80)),
            ('n_slits',    Slider(sx, 362, P, 'Num Slits',      2,  10,   5)),
            ('speed',      Slider(sx, 422, P, 'Speed',         0.1,  3, 1.0, '{:.1f}')),
        ]

        self.mode_rects = []
        bw = (P - 4) // 2
        for i in range(4):
            col, row = i % 2, i // 2
            self.mode_rects.append(pygame.Rect(sx + col * (bw + 4), 90 + row * 36, bw, 29))

        self.pause_rect   = pygame.Rect(sx,          WIN_H - 52, bw, 26)
        self.reset_rect   = pygame.Rect(sx + bw + 4, WIN_H - 52, bw, 26)
        self.wavelet_rect = pygame.Rect(sx,          WIN_H - 98, P,  16)

    def sv(self, key):
        for k, sl in self.sliders:
            if k == key:
                return sl.val
        return 0.0

    def get_params(self):
        return {
            'slit_width':    max(1, int(self.sv('slit_width'))),
            'slit_sep':      max(5, int(self.sv('slit_sep'))),
            'n_slits':       max(2, int(self.sv('n_slits'))),
            'custom_sources': list(self.custom_ys),
        }

    def compute(self):
        lam          = self.sv('wavelength')
        self.sources = get_sources(self.mode, GRID_H // 2, self.get_params())
        self.field   = compute_field(self.sources, GRID_W, GRID_H, lam, self.t)

    def render_field(self):
        rgb      = field_to_rgb(self.field)
        arr      = np.transpose(rgb, (1, 0, 2)).copy()
        surf     = pygame.surfarray.make_surface(arr)
        self.field_surf = pygame.transform.scale(surf, (FIELD_W, WIN_H))

    def draw_barrier(self):
        sw  = int(self.sv('slit_width'))
        ss  = int(self.sv('slit_sep'))
        n   = max(2, int(self.sv('n_slits')))
        ys  = WIN_H / GRID_H
        bx  = SIDEBAR_W
        bw  = 6

        def block(y1, y2):
            if y2 > y1:
                pygame.draw.rect(self.screen, BARRIER, (bx - bw, int(y1), bw + 2, int(y2 - y1 + 1)))

        cy_g = GRID_H // 2

        if self.mode == 'single':
            g1 = (cy_g - sw // 2) * ys
            g2 = (cy_g + sw // 2) * ys
            block(0, g1); block(g2, WIN_H)

        elif self.mode == 'double':
            d   = ss // 2
            pts = sorted([
                0,
                (cy_g - d - sw // 2) * ys,
                (cy_g - d + sw // 2) * ys,
                (cy_g + d - sw // 2) * ys,
                (cy_g + d + sw // 2) * ys,
                WIN_H
            ])
            for i in range(0, len(pts) - 1, 2):
                block(pts[i], pts[i + 1])

        elif self.mode == 'grating':
            prev  = 0.0
            start = cy_g - ((n - 1) * ss) // 2
            for i in range(n):
                g1 = (start + i * ss - sw // 2) * ys
                g2 = (start + i * ss + sw // 2) * ys
                block(prev, g1)
                prev = g2
            block(prev, WIN_H)

        elif self.mode == 'custom':
            pygame.draw.rect(self.screen, BARRIER, (bx - bw, 0, bw + 2, WIN_H))
            for gy in self.custom_ys:
                y1 = int((gy - 4) * ys)
                y2 = int((gy + 5) * ys)
                pygame.draw.rect(self.screen, BG, (bx - bw, y1, bw + 2, y2 - y1))

    def draw_wavelets(self):
        lam     = self.sv('wavelength')
        scale_x = FIELD_W / GRID_W
        scale_y = WIN_H   / GRID_H
        scale   = (scale_x + scale_y) / 2.0

        self.wavelet_surf.fill((0, 0, 0, 0))

        step_sources = self.sources[::max(1, len(self.sources) // 12)]
        t_mod        = self.t % (lam * 8)

        for sx_g, sy_g in step_sources:
            cx = int(sx_g * scale_x)
            cy = int(sy_g * scale_y)
            r  = t_mod
            rings = 0
            while r > lam and rings < 7:
                r -= lam
                rings += 1
            r = t_mod
            while r > 2:
                r_px  = int(r * scale)
                alpha = max(0, 55 - int(r * 0.4))
                if alpha > 3:
                    pygame.draw.circle(self.wavelet_surf, (0, 220, 255, alpha), (cx, cy), r_px, 1)
                r -= lam

        self.screen.blit(self.wavelet_surf, (SIDEBAR_W, 0))

    def draw_intensity_profile(self):
        if self.field is None:
            return
        px = SIDEBAR_W + FIELD_W
        pw = PROF_W
        pygame.draw.rect(self.screen, (5, 9, 16), (px, 0, pw, WIN_H))
        pygame.draw.line(self.screen, BORDER, (px, 0), (px, WIN_H))

        col   = self.field[:, -1] ** 2
        max_i = col.max()
        if max_i < 1e-6:
            return
        col  /= max_i
        sy    = WIN_H / GRID_H
        mw    = pw - 16

        for j in range(GRID_H):
            val  = float(col[j])
            bw   = int(val * mw)
            by   = int(j * sy)
            bh   = max(1, int(sy) + 1)
            c    = int(val * 255)
            pygame.draw.rect(self.screen, (c, int(c * 0.55), 0), (px + 6, by, bw, bh))

        lbl = self.font_s.render('I(y)', True, LABEL_C)
        self.screen.blit(lbl, (px + pw // 2 - lbl.get_width() // 2, 6))

    def draw_sidebar(self):
        pygame.draw.rect(self.screen, PANEL, (0, 0, SIDEBAR_W, WIN_H))
        pygame.draw.line(self.screen, BORDER, (SIDEBAR_W, 0), (SIDEBAR_W, WIN_H))

        self.screen.blit(self.font_b.render('HUYGENS–FRESNEL', True, WHITE), (14, 14))
        self.screen.blit(self.font_s.render('Diffraction Simulator', True, LABEL_C), (14, 32))
        pygame.draw.line(self.screen, BORDER, (14, 54), (SIDEBAR_W - 14, 54))

        ml = self.font_s.render('— MODE —', True, LABEL_C)
        self.screen.blit(ml, (SIDEBAR_W // 2 - ml.get_width() // 2, 64))

        for i, (rect, label) in enumerate(zip(self.mode_rects, MODE_LABELS)):
            active = MODES[i] == self.mode
            pygame.draw.rect(self.screen, BTN_ACT if active else PANEL, rect, border_radius=3)
            pygame.draw.rect(self.screen, WAVE_C if active else BORDER, rect, 1, border_radius=3)
            txt = self.font_s.render(label, True, WAVE_C if active else TEXT_C)
            self.screen.blit(txt, (rect.centerx - txt.get_width() // 2,
                                   rect.centery - txt.get_height() // 2))

        pygame.draw.line(self.screen, BORDER, (14, 168), (SIDEBAR_W - 14, 168))

        hidden = {
            'single':  ['slit_sep', 'n_slits'],
            'double':  ['n_slits'],
            'grating': [],
            'custom':  ['slit_width', 'slit_sep', 'n_slits'],
        }.get(self.mode, [])

        for key, sl in self.sliders:
            if key not in hidden:
                sl.draw(self.screen, self.font_s)

        if self.mode == 'custom':
            for i, txt in enumerate(['Left-click: add source', 'Right-click: clear all']):
                self.screen.blit(self.font_s.render(txt, True, LABEL_C), (14, 400 + i * 16))

        pygame.draw.line(self.screen, BORDER, (14, WIN_H - 108), (SIDEBAR_W - 14, WIN_H - 108))

        wc    = WAVE_C if self.show_wavelets else LABEL_C
        wtxt  = self.font_s.render(f'[{"X" if self.show_wavelets else " "}] Show Wavelets  [W]', True, wc)
        self.screen.blit(wtxt, (14, WIN_H - 98))

        for rect, label in [(self.pause_rect, 'RESUME' if self.paused else 'PAUSE'),
                             (self.reset_rect, 'RESET')]:
            pygame.draw.rect(self.screen, PANEL, rect, border_radius=3)
            pygame.draw.rect(self.screen, BORDER, rect, 1, border_radius=3)
            txt = self.font_s.render(label, True, TEXT_C)
            self.screen.blit(txt, (rect.centerx - txt.get_width() // 2,
                                   rect.centery - txt.get_height() // 2))

        info = [
            f'λ={self.sv("wavelength"):.0f}px  fps={int(self.clock.get_fps())}',
            f't={self.t:.1f}  src={len(self.sources)}',
            'SPACE: pause   R: reset',
        ]
        for i, line in enumerate(info):
            self.screen.blit(self.font_s.render(line, True, LABEL_C), (14, WIN_H - 30 + i * 12 - 8))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE: self.paused = not self.paused
                elif event.key == pygame.K_r:   self.t = 0.0
                elif event.key == pygame.K_w:   self.show_wavelets = not self.show_wavelets

            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos

                for i, rect in enumerate(self.mode_rects):
                    if rect.collidepoint(x, y):
                        self.mode = MODES[i]

                if self.pause_rect.collidepoint(x, y):   self.paused = not self.paused
                if self.reset_rect.collidepoint(x, y):   self.t = 0.0; self.custom_ys = []
                if self.wavelet_rect.collidepoint(x, y): self.show_wavelets = not self.show_wavelets

                if self.mode == 'custom' and SIDEBAR_W <= x < SIDEBAR_W + FIELD_W:
                    gy = int(y * GRID_H / WIN_H)
                    if event.button == 1:   self.custom_ys.append(gy)
                    elif event.button == 3: self.custom_ys = []

            for _, sl in self.sliders:
                sl.handle_event(event)

    def run(self):
        while True:
            self.handle_events()

            if not self.paused:
                self.t += self.sv('speed') * 0.5

            self.compute()
            self.render_field()

            self.screen.fill(BG)
            self.screen.blit(self.field_surf, (SIDEBAR_W, 0))
            self.draw_barrier()
            if self.show_wavelets:
                self.draw_wavelets()
            self.draw_intensity_profile()
            self.draw_sidebar()

            pygame.display.flip()
            self.clock.tick(FPS_TARGET)


if __name__ == '__main__':
    App().run()
