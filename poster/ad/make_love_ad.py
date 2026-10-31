"""Builds the 1 minute romantic version of the Prom Night 2026 ad, with an original slow piano and strings score.

Reuses the text layers and helpers from make_ad.py.
Usage: python make_love_ad.py   (needs Pillow and imageio-ffmpeg)
"""
import math
import os
import struct
import subprocess
import wave

from PIL import Image
import imageio_ffmpeg

from make_ad import HERE, W, H, FPS, ZOOM, Sparkles, ease_out, prepare_background, prepare_layer, with_alpha

OUT = os.path.join(HERE, "prom-night-2026-ad-love.mp4")
WAV = os.path.join(HERE, "music-love.wav")

DURATION = 60.0
FADE = 1.0  # crossfade between scenes
BAR = 60 / 72 * 4  # 72 BPM in 4/4

# (start, end, background, darkness, blur, [(layer, appear_at, pop)])
SCENES = [
    (0.0, 6.6, "countdown/pexels-30151915.jpg", .5, 0, [("s0a", 1.0, False), ("s0b", 3.0, False)]),
    (6.6, 13.3, "royal.jpg", .5, 0, [("s2a", .6, False), ("s2b", 1.6, True), ("s2c", 3.2, False)]),
    (13.3, 18.3, "countdown/pexels-17028568.jpg", .5, 0, [("s3a", .8, True)]),
    (18.3, 23.3, "countdown/pexels-4992827.jpg", .5, 0, [("s3b", .8, True)]),
    (23.3, 28.3, "countdown/pexels-12311203.jpg", .55, 0, [("s3c", .8, True)]),
    (28.3, 35.0, "countdown/pexels-29069190.jpg", .45, 0, [("s4a", .8, False), ("s4b", 2.2, True)]),
    (35.0, 40.0, "countdown/pexels-30767993.jpg", .45, 0, [("s8a", .8, False), ("s8b", 2.0, False)]),
    (40.0, 46.6, "countdown/pexels-31091958.jpg", .35, 6, [("s5a", .8, True), ("s5b", 2.0, False)]),
    (46.6, 51.6, "countdown/pexels-31196839.jpg", .5, 0, [("s6a", .8, True), ("s6b", 2.0, False)]),
    (51.6, 60.0, "countdown/pexels-35764836.jpg", .35, 4, [("s7a", .8, True), ("s7b", 2.4, False)]),
]


def render_video():
    scenes = []
    for start, end, bg, dark, blur, layers in SCENES:
        scenes.append((start, end, prepare_background(bg, dark, blur), [(prepare_layer(n), at, pop) for n, at, pop in layers]))
    sparkles = Sparkles(n=45, seed=11)

    def scene_frame(idx, t):
        start, end, bg, layers = scenes[idx]
        local, span = t - start, end - start + FADE
        k = max(0.0, min(1.0, local / span))
        z = 1 + (ZOOM - 1) * (k if idx % 2 else 1 - k)
        cw, ch = W * ZOOM / z, H * ZOOM / z
        cx, cy = bg.width / 2, bg.height / 2
        frame = bg.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))).resize((W, H), Image.BILINEAR).convert("RGBA")
        for (img, box), at, pop in layers:
            p = (local - at) / 1.1
            if p <= 0:
                continue
            e = ease_out(p)
            piece = img
            if pop:
                s = 1 + .08 * (1 - e)
                piece = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.BILINEAR)
            piece = with_alpha(piece, e)
            mx, my = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2 + 40 * (1 - e)
            frame.alpha_composite(piece, (int(mx - piece.width / 2), int(my - piece.height / 2)))
        return frame

    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", WAV, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    total = int(DURATION * FPS)
    for f in range(total):
        t = f / FPS
        idx = next(i for i, s in enumerate(scenes) if s[0] <= t < s[1] or i == len(scenes) - 1)
        frame = scene_frame(idx, t)
        local = t - scenes[idx][0]
        if idx and local < FADE:
            # Previous scene keeps moving underneath while this one fades in
            frame = Image.blend(scene_frame(idx - 1, t), frame, ease_out(local / FADE))
        sparkles.draw(frame, t * .6)
        fade = min(1.0, t / 1.5, (DURATION - t) / 2.0)
        if fade < 1:
            frame = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), frame, max(0.0, fade))
        proc.stdin.write(frame.convert("RGB").tobytes())
        if f % 150 == 0:
            print(f"frame {f}/{total}", flush=True)
    proc.stdin.close()
    proc.wait()


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def render_music():
    sr = 32000
    n = int(DURATION * sr)
    buf = [0.0] * n
    two_pi = 2 * math.pi

    def add(t0, length, fn):
        i0 = int(t0 * sr)
        for i in range(max(0, min(int(length * sr), n - i0))):
            buf[i0 + i] += fn(i / sr)

    def piano(f, vel, length=2.2):
        def note(t):
            a = min(1, t / .006)
            return vel * a * (math.sin(two_pi * f * t) * math.exp(-t * 2.2)
                              + .45 * math.sin(two_pi * 2 * f * t) * math.exp(-t * 3.5)
                              + .18 * math.sin(two_pi * 3 * f * t) * math.exp(-t * 5)
                              + .07 * math.sin(two_pi * 4 * f * t) * math.exp(-t * 7))
        return note, length

    # I V vi IV, the classic love ballad progression in C
    chords = [(48, [60, 64, 67]), (43, [59, 62, 67]), (45, [60, 64, 69]), (41, [60, 65, 69])]
    melody = [
        [(76, 1), (74, 1), (72, 2)], [(74, 1), (71, 1), (67, 2)],
        [(72, 1), (76, 1), (79, 2)], [(77, 1.5), (76, .5), (72, 2)],
        [(79, 2), (76, 1), (77, 1)], [(74, 2), (71, 1), (74, 1)],
        [(76, 1.5), (79, .5), (81, 2)], [(77, 1), (76, 1), (74, 1), (72, 1)],
    ]
    beat = BAR / 4
    bars = int(DURATION / BAR)

    for b in range(bars + 1):
        t0 = b * BAR
        last = t0 + BAR > DURATION - 4
        bass, triad = chords[b % 4]
        if last:
            bass, triad = chords[0]

        # Strings pad swelling through each bar
        def pad(t, notes=[bass + 12] + triad, swell=min(1.0, .4 + b * .08)):
            env = min(1, t / 1.2) * (1 if t < BAR else max(0, 1 - (t - BAR) / 1.2))
            vib = .004 * math.sin(two_pi * 5 * t)
            return .028 * swell * env * sum(math.sin(two_pi * midi(m) * (1 + vib) * t) + .4 * math.sin(two_pi * midi(m) * 1.003 * t)
                                             for m in notes)
        add(t0, BAR + 1.3, pad)

        # Low piano bass note and a broken chord in eighths
        fn, ln = piano(midi(bass), .32, 3.2)
        add(t0, ln, fn)
        pattern = [triad[0], triad[1], triad[2], triad[1] + 12, triad[2], triad[1], triad[0] + 12, triad[1]]
        for i, m in enumerate(pattern if not last else pattern[:3]):
            fn, ln = piano(midi(m), .11 + .02 * (i % 2 == 0))
            add(t0 + i * beat / 2, ln, fn)

        # Melody enters after the intro and repeats an octave higher feel at the end
        if 2 <= b and not last:
            pos = t0
            for m, d in melody[(b - 2) % len(melody)]:
                fn, ln = piano(midi(m), .2, 2.6)
                add(pos, ln, fn)
                pos += d * beat

        # Soft heartbeat pulse in the middle section
        if 6 <= b < bars - 1:
            for k in (0, 2):
                def thump(t):
                    return .25 * math.sin(two_pi * (55 * t + 40 * (1 - math.exp(-t * 25)) / 25)) * math.exp(-t * 12)
                add(t0 + k * beat, .3, thump)

    # Final held chord
    for m in (48, 60, 64, 67, 72, 76):
        fn, ln = piano(midi(m), .16, 4.0)
        add(DURATION - 4.2, ln, fn)

    # Simple room reverb
    out = buf[:]
    for delay, gain in ((int(.0297 * sr), .32), (int(.0371 * sr), .28), (int(.0411 * sr), .25), (int(.0437 * sr), .22)):
        line = [0.0] * n
        for i in range(delay, n):
            line[i] = buf[i - delay] + gain * line[i - delay]
        for i in range(n):
            out[i] += .18 * line[i]

    peak = max(abs(v) for v in out) or 1
    with wave.open(WAV, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        fade_from = int((DURATION - 2.5) * sr)
        frames = bytearray()
        for i, v in enumerate(out):
            v = math.tanh(1.2 * v / peak) * .88
            if i > fade_from:
                v *= 1 - (i - fade_from) / (n - fade_from)
            frames += struct.pack("<h", int(v * 32767))
        w.writeframes(bytes(frames))


if __name__ == "__main__":
    render_music()
    print("music done", flush=True)
    render_video()
    os.remove(WAV)
    print("saved", OUT)
