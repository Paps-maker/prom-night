"""Builds the Prom Night 2026 video ad (1080x1920, 30 fps) with an original synthesized backing track.

Text layers come from layers.html, rendered as transparent PNGs into ad/layers/.
Usage: python make_ad.py   (needs Pillow and imageio-ffmpeg)
"""
import math
import os
import random
import struct
import subprocess
import wave

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
import imageio_ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__))
IMAGES = os.path.join(HERE, "..", "..", "images")
LAYERS = os.path.join(HERE, "layers")
OUT = os.path.join(HERE, "prom-night-2026-ad.mp4")
WAV = os.path.join(HERE, "music.wav")

W, H, FPS = 1080, 1920, 30
DURATION = 21.0
BEAT = 0.5  # 120 BPM, scene cuts land on beats

# (start, end, background, darkness, blur, [(layer, appear_at, pop)])
SCENES = [
    (0.0, 3.0, "countdown/pexels-35764838.jpg", .55, 0, [("s1a", .3, False), ("s1b", 1.0, False)]),
    (3.0, 6.0, "royal.jpg", .5, 0, [("s2a", 0, False), ("s2b", .35, True), ("s2c", 1.0, False)]),
    (6.0, 7.0, "countdown/pexels-17028568.jpg", .5, 0, [("s3a", 0, True)]),
    (7.0, 8.0, "countdown/pexels-4992827.jpg", .5, 0, [("s3b", 0, True)]),
    (8.0, 9.0, "countdown/pexels-1481313.jpg", .5, 0, [("s3c", 0, True)]),
    (9.0, 12.0, "countdown/pexels-29069190.jpg", .45, 0, [("s4a", .1, False), ("s4b", .8, True)]),
    (12.0, 15.0, "countdown/pexels-31091958.jpg", .35, 6, [("s5a", 0, True), ("s5b", .6, False)]),
    (15.0, 17.5, "countdown/pexels-31196839.jpg", .5, 0, [("s6a", 0, True), ("s6b", .5, False)]),
    (17.5, 21.0, "countdown/pexels-35764836.jpg", .35, 4, [("s7a", 0, True), ("s7b", .6, False)]),
]
ZOOM = 1.12


def ease_out(p):
    p = max(0.0, min(1.0, p))
    return 1 - (1 - p) ** 3


def prepare_background(name, darkness, blur):
    im = Image.open(os.path.join(IMAGES, name)).convert("RGB")
    bw, bh = int(W * ZOOM), int(H * ZOOM)
    scale = max(bw / im.width, bh / im.height)
    im = im.resize((math.ceil(im.width * scale), math.ceil(im.height * scale)), Image.LANCZOS)
    left, top = (im.width - bw) // 2, (im.height - bh) // 2
    im = im.crop((left, top, left + bw, top + bh))
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    im = ImageEnhance.Brightness(im).enhance(darkness)
    # Darker towards the bottom so text and QR stay readable
    shade = Image.linear_gradient("L").resize((bw, bh)).point(lambda v: int(v * .55))
    return Image.composite(Image.new("RGB", (bw, bh), (8, 5, 12)), im, shade)


def prepare_layer(name):
    im = Image.open(os.path.join(LAYERS, name + ".png")).convert("RGBA")
    box = im.getbbox()
    return im.crop(box), box


def with_alpha(im, a):
    if a >= .999:
        return im
    r, g, b, alpha = im.split()
    return Image.merge("RGBA", (r, g, b, alpha.point(lambda v: int(v * a))))


class Sparkles:
    def __init__(self, n=55, seed=7):
        rnd = random.Random(seed)
        self.p = [(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(30, 110), rnd.uniform(2, 6), rnd.uniform(0, 6.3))
                  for _ in range(n)]

    def draw(self, frame, t):
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        for x, y, speed, size, phase in self.p:
            yy = (y - speed * t) % H
            xx = x + 14 * math.sin(t * .8 + phase)
            tw = .5 + .5 * math.sin(t * 3 + phase)
            glow = size * 3
            d.ellipse((xx - glow, yy - glow, xx + glow, yy + glow), fill=(246, 216, 146, int(40 * tw)))
            d.ellipse((xx - size / 2, yy - size / 2, xx + size / 2, yy + size / 2), fill=(255, 240, 200, int(230 * tw)))
        frame.alpha_composite(layer)


def render_video():
    scenes = []
    for start, end, bg, dark, blur, layers in SCENES:
        scenes.append((start, end, prepare_background(bg, dark, blur), [(prepare_layer(n), at, pop) for n, at, pop in layers]))
    sparkles = Sparkles()

    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", WAV, "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    for f in range(int(DURATION * FPS)):
        t = f / FPS
        idx = next(i for i, s in enumerate(scenes) if s[0] <= t < s[1] or i == len(scenes) - 1)
        start, end, bg, layers = scenes[idx]
        local, span = t - start, end - start

        # Slow zoom, alternating in and out per scene
        k = local / span
        z = 1 + (ZOOM - 1) * (k if idx % 2 else 1 - k)
        cw, ch = W * ZOOM / z, H * ZOOM / z
        cx, cy = bg.width / 2, bg.height / 2
        frame = bg.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))).resize((W, H), Image.BILINEAR)
        frame = frame.convert("RGBA")

        sparkles.draw(frame, t)

        for (img, box), at, pop in layers:
            p = (local - at) / .45
            if p <= 0:
                continue
            e = ease_out(p)
            piece = img
            if pop:
                s = 1 + .18 * (1 - e)
                piece = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.BILINEAR)
            piece = with_alpha(piece, e)
            mx, my = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2 + 60 * (1 - e)
            frame.alpha_composite(piece, (int(mx - piece.width / 2), int(my - piece.height / 2)))

        # Quick flash on every cut, fade in at the start and out at the end
        if idx and local < .18:
            frame = Image.blend(frame, Image.new("RGBA", (W, H), (255, 245, 225, 255)), .45 * (1 - local / .18))
        fade = min(1.0, t / .4, (DURATION - t) / .5)
        if fade < 1:
            frame = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), frame, max(0.0, fade))

        proc.stdin.write(frame.convert("RGB").tobytes())
        if f % 60 == 0:
            print(f"frame {f}/{int(DURATION * FPS)}")
    proc.stdin.close()
    proc.wait()


def render_music():
    sr = 44100
    n = int(DURATION * sr)
    buf = [0.0] * n
    rnd = random.Random(3)
    two_pi = 2 * math.pi

    def add(t0, length, fn):
        i0 = int(t0 * sr)
        for i in range(min(int(length * sr), n - i0)):
            buf[i0 + i] += fn(i / sr)

    chords = [(220.0, 261.63, 329.63), (174.61, 220.0, 261.63), (261.63, 329.63, 392.0), (196.0, 246.94, 293.66)]
    roots = [110.0, 87.31, 130.81, 98.0]

    # Warm pad, one chord every 2 seconds
    for c in range(int(DURATION / 2) + 1):
        notes = chords[c % 4]

        def pad(t, notes=notes):
            env = min(1, t / .3) * (1 if t < 2 else max(0, 1 - (t - 2) / .4))
            v = sum(math.sin(two_pi * f * t) + .5 * math.sin(two_pi * f * 1.004 * t) + .2 * math.sin(two_pi * 2 * f * t) for f in notes)
            return .05 * env * v
        add(c * 2, 2.4, pad)

    # Riser into the drop at 3 s
    lp = [0.0]

    def riser(t):
        lp[0] += (rnd.uniform(-1, 1) - lp[0]) * (.02 + .3 * t / 3)
        return (t / 3) ** 2 * (.35 * lp[0] + .08 * math.sin(two_pi * (200 + 500 * t) * t))
    add(0, 3, riser)

    def crash(t):
        return .3 * rnd.uniform(-1, 1) * math.exp(-t * 2.5)
    for at in (3.0, 9.0, 17.5):
        add(at, 1.6, crash)

    def kick(t):
        return .9 * math.sin(two_pi * (45 * t + 110 * (1 - math.exp(-t * 30)) / 30)) * math.exp(-t * 9)

    def hat(t):
        return .12 * rnd.uniform(-1, 1) * math.exp(-t * 60)

    def clap(t):
        return .28 * rnd.uniform(-1, 1) * math.exp(-t * 22)

    b = 3.0
    while b < 20.5:
        add(b, .35, kick)
        add(b + BEAT / 2, .08, hat)
        beat_no = round((b - 3) / BEAT)
        if b >= 6 and beat_no % 2 == 1:
            add(b, .2, clap)
        # Bass on eighth notes following the chord roots
        root = roots[int(b / 2) % 4]
        for half in (0, BEAT / 2):
            def bass(t, f=root):
                return .22 * math.exp(-t * 8) * (math.sin(two_pi * f * t) + .35 * math.sin(two_pi * 2 * f * t))
            add(b + half, .24, bass)
        b += BEAT

    # Bright arpeggio from the crown scene onwards
    step = BEAT / 2
    s = 9.0
    i = 0
    while s < 20.5:
        f = chords[int(s / 2) % 4][i % 3] * 2

        def pluck(t, f=f):
            return .07 * math.exp(-t * 10) * (math.sin(two_pi * f * t) + .3 * math.sin(two_pi * 2 * f * t))
        add(s, .3, pluck)
        s += step
        i += 1

    # Final hit and fade
    add(20.5, .5, kick)
    peak = max(abs(v) for v in buf) or 1
    with wave.open(WAV, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        fade_from = int((DURATION - .5) * sr)
        frames = bytearray()
        for i, v in enumerate(buf):
            v = math.tanh(1.4 * v / peak) * .9
            if i > fade_from:
                v *= 1 - (i - fade_from) / (n - fade_from)
            frames += struct.pack("<h", int(v * 32767))
        w.writeframes(bytes(frames))


if __name__ == "__main__":
    render_music()
    render_video()
    os.remove(WAV)
    print("saved", OUT)
