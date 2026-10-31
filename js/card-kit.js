/* Drawing helpers shared by cards.html and organiser.html */
const CardKit = (() => {
    const HASHTAG = "#PromNightEldoret2026";
    const images = {};

    function loadImage(src) {
        if (!images[src]) {
            images[src] = new Promise(resolve => {
                const img = new Image();
                img.onload = () => resolve(img);
                img.onerror = () => resolve(null);
                img.src = src;
            });
        }
        return images[src];
    }

    function readPhoto(file) {
        return new Promise(resolve => {
            if (!file) return resolve(null);
            const img = new Image();
            img.onload = () => resolve(img);
            img.onerror = () => resolve(null);
            img.src = URL.createObjectURL(file);
        });
    }

    function create(canvas) {
        const ctx = canvas.getContext("2d");
        const W = canvas.width, H = canvas.height;

        function cover(img, x, y, w, h) {
            const s = Math.max(w / img.width, h / img.height);
            const sw = w / s, sh = h / s;
            ctx.drawImage(img, (img.width - sw) / 2, (img.height - sh) / 2, sw, sh, x, y, w, h);
        }

        function circlePhoto(img, cx, cy, r) {
            ctx.save();
            ctx.beginPath(); ctx.arc(cx, cy, r, 0, 7); ctx.clip();
            cover(img, cx - r, cy - r, r * 2, r * 2);
            ctx.restore();
        }

        function gold(y0, y1) {
            const g = ctx.createLinearGradient(0, y0, W, y1);
            g.addColorStop(0, "#fff1c9");
            g.addColorStop(.45, "#e3b75a");
            g.addColorStop(1, "#b8862f");
            return g;
        }

        // Centred text that shrinks until it fits the width
        function text(str, y, size, font, color, { x = W / 2, maxWidth = W - 160, spacing = 0, shadow = true, align = "center" } = {}) {
            let s = size;
            do {
                ctx.font = font.replace("{s}", s);
                ctx.letterSpacing = spacing ? `${spacing * s}px` : "0px";
                s -= 2;
            } while (ctx.measureText(str).width > maxWidth && s > 16);
            ctx.fillStyle = color;
            ctx.textAlign = align;
            ctx.textBaseline = "alphabetic";
            ctx.shadowColor = shadow ? "rgba(0,0,0,.6)" : "transparent";
            ctx.shadowBlur = shadow ? 30 : 0;
            ctx.fillText(str, x + (spacing && align === "center" ? spacing * s / 2 : 0), y);
            ctx.shadowBlur = 0;
            ctx.letterSpacing = "0px";
        }

        function pill(str, y, fill, color) {
            ctx.font = "800 26px Outfit";
            ctx.letterSpacing = "7px";
            const w = ctx.measureText(str).width + 70;
            ctx.fillStyle = fill;
            ctx.beginPath(); ctx.roundRect((W - w) / 2, y - 40, w, 58, 29); ctx.fill();
            ctx.fillStyle = color;
            ctx.textAlign = "center";
            ctx.fillText(str, W / 2 + 3, y - 2);
            ctx.letterSpacing = "0px";
        }

        function sparkles(seed, count = 26) {
            let r = seed;
            const rand = () => (r = (r * 9301 + 49297) % 233280) / 233280;
            for (let i = 0; i < count; i++) {
                const x = rand() * W, y = rand() * H * .7, s = 2 + rand() * 3;
                ctx.fillStyle = "rgba(246,216,146,.18)";
                ctx.beginPath(); ctx.arc(x, y, s * 3, 0, 7); ctx.fill();
                ctx.fillStyle = "rgba(255,240,200,.9)";
                ctx.beginPath(); ctx.arc(x, y, s / 2, 0, 7); ctx.fill();
            }
        }

        // Photo across the top fading into the base colour, plus logo and gold frame
        async function backdrop(img, base, photoHeight = .58) {
            ctx.fillStyle = base;
            ctx.fillRect(0, 0, W, H);
            if (img) cover(img, 0, 0, W, H * photoHeight);
            const fade = ctx.createLinearGradient(0, 0, 0, H);
            fade.addColorStop(0, "rgba(0,0,0,.25)");
            fade.addColorStop(photoHeight * .5, "rgba(0,0,0,.3)");
            fade.addColorStop(photoHeight * .95, base);
            fade.addColorStop(1, base);
            ctx.fillStyle = fade;
            ctx.fillRect(0, 0, W, H);
            sparkles(base.length * 131);
            const logo = await loadImage("images/pr logo.png");
            if (logo) {
                circlePhoto(logo, W / 2, 110, 46);
                ctx.strokeStyle = "#e3b75a"; ctx.lineWidth = 3;
                ctx.beginPath(); ctx.arc(W / 2, 110, 46, 0, 7); ctx.stroke();
            }
            ctx.strokeStyle = "rgba(246,216,146,.45)"; ctx.lineWidth = 2;
            ctx.beginPath(); ctx.roundRect(36, 36, W - 72, H - 72, 30); ctx.stroke();
        }

        // Ticket QR panel with two lines of text and the hashtag underneath
        async function footer(line1, line2) {
            const qr = await loadImage("images/zenlipa-qr.png");
            const y = H - 250;
            ctx.fillStyle = "rgba(0,0,0,.45)";
            ctx.strokeStyle = "rgba(246,216,146,.4)";
            ctx.lineWidth = 2;
            ctx.beginPath(); ctx.roundRect(80, y, W - 160, 170, 28); ctx.fill(); ctx.stroke();
            ctx.fillStyle = "#fff";
            ctx.beginPath(); ctx.roundRect(106, y + 22, 126, 126, 14); ctx.fill();
            if (qr) {
                ctx.imageSmoothingEnabled = false;
                ctx.drawImage(qr, 114, y + 30, 110, 110);
                ctx.imageSmoothingEnabled = true;
            }
            text(line1.toUpperCase(), y + 62, 20, "700 {s}px Outfit", "#f6d892", { x: 262, align: "left", spacing: .25, shadow: false, maxWidth: W - 360 });
            text(line2, y + 110, 40, "700 {s}px 'Playfair Display'", "#fff", { x: 262, align: "left", shadow: false, maxWidth: W - 360 });
            text("prom2026.online  ·  Thu 10 Dec  ·  Boma Inn", y + 146, 22, "400 {s}px Outfit", "#cbbfd8", { x: 262, align: "left", shadow: false, maxWidth: W - 360 });
            hashtag();
        }

        function hashtag() {
            text(HASHTAG, H - 46, 22, "600 {s}px Outfit", "rgba(255,255,255,.6)", { spacing: .12, shadow: false });
        }

        return { ctx, W, H, cover, circlePhoto, gold, text, pill, sparkles, backdrop, footer, hashtag };
    }

    function toBlob(canvas) {
        return new Promise((resolve, reject) => {
            try {
                canvas.toBlob(blob => blob ? resolve(blob) : reject(new Error("Empty image")), "image/png");
            } catch (err) {
                reject(err);
            }
        });
    }

    function notify(message, sticky = false) {
        let box = document.getElementById("cardkitNotice");
        if (!box) {
            box = document.createElement("div");
            box.id = "cardkitNotice";
            box.setAttribute("role", "status");
            box.style.cssText = "position:fixed;left:16px;right:16px;bottom:20px;z-index:100;max-width:520px;margin:0 auto;padding:14px 18px;border-radius:14px;background:#1a1424;border:1px solid rgba(227,183,90,.5);color:#f4eff8;font:500 15px/1.45 Outfit,sans-serif;box-shadow:0 20px 50px rgba(0,0,0,.5)";
            document.body.appendChild(box);
        }
        box.textContent = message;
        box.hidden = false;
        clearTimeout(box._timer);
        if (!sticky) box._timer = setTimeout(() => { box.hidden = true; }, 6000);
    }

    function blockedMessage() {
        return location.protocol === "file:"
            ? "Saving only works on the live site (prom2026.online). Browsers block it when the page is opened as a file from your computer."
            : "Sorry, this card could not be saved. Please try again, or take a screenshot.";
    }

    // Renders the PNG after every redraw so Share can open the share sheet straight away (iPhones require this)
    async function cache(canvas) {
        try {
            canvas._blob = await toBlob(canvas);
        } catch (err) {
            canvas._blob = null;
        }
    }

    async function getBlob(canvas) {
        if (canvas._blob) return canvas._blob;
        try {
            return await toBlob(canvas);
        } catch (err) {
            notify(blockedMessage());
            return null;
        }
    }

    async function download(canvas, name) {
        const blob = await getBlob(canvas);
        if (!blob) return false;
        const url = URL.createObjectURL(blob);
        const a = Object.assign(document.createElement("a"), { href: url, download: name });
        document.body.appendChild(a);
        a.click();
        a.remove();
        setTimeout(() => URL.revokeObjectURL(url), 4000);
        notify("Card saved. Check your downloads or gallery.");
        return true;
    }

    // Native share sheet with the image where supported, otherwise download and open WhatsApp
    async function share(canvas, name, message) {
        const blob = canvas._blob;
        if (blob) {
            const file = new File([blob], name, { type: "image/png" });
            if (navigator.canShare && navigator.canShare({ files: [file] })) {
                try {
                    await navigator.share({ files: [file], text: message });
                    return true;
                } catch (err) {
                    if (err.name === "AbortError") return false;
                }
            }
        }
        if (await download(canvas, name)) {
            window.open("https://wa.me/?text=" + encodeURIComponent(message), "_blank", "noopener");
            return true;
        }
        return false;
    }

    if (location.protocol === "file:") {
        document.addEventListener("DOMContentLoaded", () => notify(blockedMessage(), true));
    }

    function slug(str) {
        return str.trim().toLowerCase().replace(/[^a-z0-9]+/g, "");
    }

    return { HASHTAG, loadImage, readPhoto, create, cache, download, share, notify, slug };
})();
