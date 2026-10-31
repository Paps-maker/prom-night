"""Builds the card maker explainer video (1080x1920, 30 fps) with voiceover and soft music.

Inputs: explain_shots/ (phone screenshots of cards.html at 390px, 2x), explain_layers/ (captions from
explain_layers.html), explain_voice/line1.wav ... line11.wav (one per scene, script in explain_voice/script.txt).
Usage: python make_explainer.py   (needs Pillow and imageio-ffmpeg)
"""
import os
import struct
import subprocess
import wave

from PIL import Image, ImageDraw
import imageio_ffmpeg

import make_love_ad
from make_ad import HERE, W, H, FPS, Sparkles, ease_out, with_alpha

SHOTS = os.path.join(HERE, "explain_shots")
LAYERS = os.path.join(HERE, "explain_layers")
VOICE = os.path.join(HERE, "explain_voice")
POSTERS = os.path.join(HERE, "..")
OUT = os.path.join(HERE, "prom-night-2026-card-maker-explainer.mp4")
MIX = os.path.join(HERE, "explainer-mix.wav")
SR = 32000
GAP = .9      # silence added to each scene around its voice line
LEAD = .35    # voice starts this long after the scene starts
FADE = .35

# Phone screen: 390x844 css shown at 600x1298
SCALE = 600 / 390
PHONE_X, PHONE_Y, BEZEL = 216, 520, 24
SCREEN_X, SCREEN_Y = PHONE_X + BEZEL, PHONE_Y + BEZEL
SW, SH = 600, 1298


def load(path, mode="RGBA"):
    return Image.open(path).convert(mode)


def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius, fill=255)
    return m


def build_phone():
    pw, ph = SW + BEZEL * 2, SH + BEZEL * 2
    phone = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(phone)
    d.rounded_rectangle((0, 0, pw - 1, ph - 1), 74, fill=(22, 18, 28, 255), outline=(227, 183, 90, 160), width=3)
    d.rounded_rectangle((BEZEL, BEZEL, BEZEL + SW, BEZEL + SH), 52, fill=(0, 0, 0, 0))
    return phone


class Assets:
    def __init__(self):
        self.shots = {n[:-4]: load(os.path.join(SHOTS, n), "RGB") for n in os.listdir(SHOTS)}
        self.layers = {n[:-4]: load(os.path.join(LAYERS, n)) for n in os.listdir(LAYERS)}
        self.phone = build_phone()
        self.screen_mask = rounded_mask((SW, SH), 52)
        self.nav = self.shots["index_full"].crop((0, 0, 780, 152))
        card = self.shots["inv_Brian"].crop((32, 584, 32 + 686, 584 + 858))
        self.card = card.resize((640, 800), Image.LANCZOS)
        self.card_mask = rounded_mask(self.card.size, 30)
        stories = os.path.join(POSTERS, "marketing", "stories")
        self.stories = [load(os.path.join(stories, f"story-{n}.png"), "RGB").resize((600, 1067), Image.LANCZOS)
                        for n in ("gown-or-suit", "dress-code-poll", "tag-your-prom-date")]
        self.story_mask = rounded_mask((600, 1067), 36)
        self.posters = [load(os.path.join(POSTERS, p), "RGB").resize((460, 575), Image.LANCZOS) for p in
                        ("countdown/40-days-post-on-oct31.png", "marketing/will-you-go-to-prom-with-me.png", "marketing/dress-code.png")]
        bg = Image.new("RGB", (W, H), (11, 9, 16))
        glow = Image.radial_gradient("L").resize((1400, 1400)).point(lambda v: int((255 - v) * .35))
        bg.paste(Image.new("RGB", (1400, 1400), (90, 50, 110)), (-160, 300), glow)
        self.bg = bg.convert("RGBA")
        self.sparkles = Sparkles(n=40, seed=21)


def screen(assets, shot, scroll, nav=False):
    img = assets.shots[shot]
    top = int(scroll * 2)
    view = Image.new("RGB", (780, 1688), (11, 9, 16))
    view.paste(img.crop((0, top, 780, min(img.height, top + 1688))), (0, 0))
    if nav:
        view.paste(assets.nav, (0, 0))
    return view.resize((SW, SH), Image.BILINEAR)


def draw_phone(frame, assets, view, alpha=1.0):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.paste(view, (SCREEN_X, SCREEN_Y), assets.screen_mask)
    layer.alpha_composite(assets.phone, (PHONE_X, PHONE_Y))
    frame.alpha_composite(with_alpha(layer, alpha) if alpha < 1 else layer)


def tap(frame, x, y, scroll, since):
    """Ripple at css point (x, y) of the page, `since` seconds after the tap."""
    if not 0 <= since < .7:
        return
    cx, cy = SCREEN_X + x * SCALE, SCREEN_Y + (y - scroll) * SCALE
    e = ease_out(since / .7)
    r = 26 + 50 * e
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, int(110 * (1 - e))))
    d.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill=(255, 255, 255, int(200 * (1 - e))))
    frame.alpha_composite(layer)


def at(timeline, t):
    """Last value in [(time, value), ...] whose time has passed."""
    value = timeline[0][1]
    for when, v in timeline:
        if t >= when:
            value = v
    return value


def lerp(a, b, k):
    return a + (b - a) * max(0.0, min(1.0, k))


# Each scene draws its visuals for local time t (seconds) and duration d
def s_intro(f, a, t, d):
    draw_phone(f, a, screen(a, "inv0", lerp(0, 120, t / d)))


def s_open(f, a, t, d):
    draw_phone(f, a, screen(a, "index_full", 420, nav=True))
    tap(f, 160, 1138, 420, t - 3.4)


def s_pick(f, a, t, d):
    shot = at([(0, "inv0"), (3.75, "going"), (5.75, "vote")], t)
    draw_phone(f, a, screen(a, shot, 300))
    for when, x in ((2.0, 82), (3.6, 188), (5.6, 293)):
        tap(f, x, 834, 300, t - when)


def s_type(f, a, t, d):
    shot = at([(0, "inv0"), (.9, "inv_B"), (1.25, "inv_Br"), (1.6, "inv_Bri"), (1.95, "inv_Bria"), (2.3, "inv_Brian")], t)
    draw_phone(f, a, screen(a, shot, 300))
    tap(f, 187, 974, 300, t - .4)


def s_share(f, a, t, d):
    k = ease_out((t - 1.9) / .6)
    if k < 1:
        draw_phone(f, a, screen(a, "inv_Brian", 560), 1 - k)
        tap(f, 187, 1144, 560, t - 1.0)
    if k > 0:
        s = .85 + .15 * k
        card = a.card.resize((int(640 * s), int(800 * s)), Image.BILINEAR)
        mask = a.card_mask.resize(card.size)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        layer.paste(card, ((W - card.width) // 2, 540 + (800 - card.height) // 2), mask)
        f.alpha_composite(with_alpha(layer, k))
        sheet = a.layers["share"]
        f.alpha_composite(with_alpha(sheet, ease_out((t - 2.4) / .5)), (0, int(80 * (1 - ease_out((t - 2.4) / .5)))))


def s_going(f, a, t, d):
    draw_phone(f, a, screen(a, "going", lerp(260, 0, t / 2.5)))


def s_vote(f, a, t, d):
    draw_phone(f, a, screen(a, "vote", lerp(260, 0, t / 2.5)))


def s_stories(f, a, t, d):
    part = d / 3
    i = min(2, int(t / part))
    local = t - i * part
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.paste(a.stories[i], (240, 560), a.story_mask)
    f.alpha_composite(with_alpha(layer, ease_out(local / .4)))
    sticker = a.layers[f"poll{i + 1}"]
    e = ease_out((local - .6) / .4)
    if e > 0:
        f.alpha_composite(with_alpha(sticker, e), (0, int(40 * (1 - e))))


def s_hashtag(f, a, t, d):
    z = 1 + .04 * t / d
    for i, (img, angle, x) in enumerate(zip(a.posters, (-8, 0, 8), (40, 310, 580))):
        p = img.resize((int(460 * z), int(575 * z)), Image.BILINEAR).convert("RGBA").rotate(angle, expand=True, resample=Image.BICUBIC)
        e = ease_out((t - i * .25) / .5)
        f.alpha_composite(with_alpha(p, e), (x - (p.width - 460) // 2, 700 + (60 if i != 1 else 0) - (p.height - 575) // 2 + int(40 * (1 - e))))


def s_calendar(f, a, t, d):
    draw_phone(f, a, screen(a, "calendar", 0, nav=True))
    tap(f, 194, 538, 0, t - 2.9)
    tap(f, 195, 603, 0, t - 5.3)
    e = ease_out((t - 5.9) / .5)
    if e > 0:
        f.alpha_composite(with_alpha(a.layers["calok"], e), (0, int(60 * (1 - e))))


def s_cta(f, a, t, d):
    s = 1 + .03 * t / d
    card = a.card.resize((int(560 * s), int(700 * s)), Image.BILINEAR)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.paste(card, ((W - card.width) // 2, 600 + (700 - card.height) // 2), a.card_mask.resize(card.size))
    f.alpha_composite(layer)
    f.alpha_composite(with_alpha(a.layers["cta"], ease_out((t - .5) / .5)))


SCENES = [("c1", 1, s_intro), ("c2", 2, s_open), ("c3", 3, s_pick), ("c4", 4, s_type), ("c5", 5, s_share),
          ("c6", 6, s_going), ("c7", 7, s_vote), ("c9", 9, s_stories), ("c10", 10, s_hashtag), ("c11", 11, s_calendar), ("c8", 8, s_cta)]


def read_wav(path):
    with wave.open(path) as w:
        assert w.getframerate() == SR and w.getsampwidth() == 2 and w.getnchannels() == 1
        raw = w.readframes(w.getnframes())
    return [v / 32768 for v in struct.unpack(f"<{len(raw) // 2}h", raw)]


def build_audio():
    voices = [read_wav(os.path.join(VOICE, f"line{n}.wav")) for _, n, _ in SCENES]
    durations = [len(v) / SR + GAP for v in voices]
    total = sum(durations)

    make_love_ad.DURATION = total
    make_love_ad.WAV = MIX
    make_love_ad.render_music()
    music = read_wav(MIX)
    out = [m * .16 for m in music]
    start = 0.0
    for v, d in zip(voices, durations):
        i0 = int((start + LEAD) * SR)
        for i, s in enumerate(v):
            if i0 + i < len(out):
                out[i0 + i] += s * .95
        start += d
    peak = max(abs(v) for v in out) or 1
    with wave.open(MIX, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v / peak * .95)) * 32767)) for v in out))
    return durations


def render(durations):
    a = Assets()
    starts = [sum(durations[:i]) for i in range(len(durations))]
    total = sum(durations)

    def scene_frame(i, t):
        cap, _, fn = SCENES[i]
        local, d = t - starts[i], durations[i]
        frame = a.bg.copy()
        a.sparkles.draw(frame, t * .5)
        fn(frame, a, local, d)
        e = ease_out(local / .5)
        frame.alpha_composite(with_alpha(a.layers[cap], e), (0, int(30 * (1 - e))))
        return frame

    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", MIX, "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    frames = int(total * FPS)
    for n in range(frames):
        t = n / FPS
        i = max(k for k in range(len(starts)) if starts[k] <= t)
        frame = scene_frame(i, t)
        if i and t - starts[i] < FADE:
            frame = Image.blend(scene_frame(i - 1, t), frame, ease_out((t - starts[i]) / FADE))
        fade = min(1.0, t / .6, (total - t) / 1.2)
        if fade < 1:
            frame = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), frame, max(0.0, fade))
        proc.stdin.write(frame.convert("RGB").tobytes())
        if n % 150 == 0:
            print(f"frame {n}/{frames}", flush=True)
    proc.stdin.close()
    proc.wait()


if __name__ == "__main__":
    durations = build_audio()
    print("audio done, total", round(sum(durations), 1), "s", flush=True)
    render(durations)
    os.remove(MIX)
    print("saved", OUT)
