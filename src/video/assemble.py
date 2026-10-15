"""Assemble the demo video: slide pictures + website clip + voice clips + English subtitles.

    python src/video/assemble.py --work DIR [--pdf slides.pdf] [--audio AUDIO_DIR] [--preview]

- Segments and subtitles come from docs/04_video_script.md (12 rows, # 01 to 12).
- Pictures: segment 04 is the website clip (record_demo.py output in DIR); the others are
  slide pages. With --pdf, pages come from the exported deck (exact fonts and layout).
  Without it, slides are rendered from the deck's HTML files in DIR/deck/project/slides.
- Audio: AUDIO_DIR/01.* ... 12.* (any format ffmpeg reads). Leading and trailing silence
  is trimmed and 0.3 s of padding added, then each picture lasts exactly as long as its clip.
- --preview: no audio needed; each segment gets silence sized from its Chinese character
  count at 4.5 characters per second, to check pictures and subtitle timing before recording.
- Output: DIR/haze_window_demo.mp4 (1920x1080, H.264, AAC). Reports the total length and
  fails loudly if it is over 3:00.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "docs" / "04_video_script.md"
SLIDE_OF = {"01": 1, "02": 2, "03": 3, "05": 4, "06": 5, "07": 6, "08": 7, "09": 8, "10": 9, "11": 10, "12": 11}
SLIDE_IDS = ["cover", "problem", "decision", "method", "results", "model", "shadow", "limits", "pilot", "sustain", "links"]
PAD = 0.3
LIMIT = 180.0


def sh(cmd):
    subprocess.run(cmd, check=True)


def dur(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
                         check=True, capture_output=True, text=True).stdout
    return float(json.loads(out)["format"]["duration"])


def segments():
    rows = []
    for line in SCRIPT.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\| (\d\d) \|(.*)\|(.*)\|(.*)\|\s*$", line)
        if m:
            rows.append({"id": m.group(1), "zh": m.group(3).strip(), "en": m.group(4).strip()})
    assert [r["id"] for r in rows] == [f"{i:02d}" for i in range(1, 13)], "script must have rows 01-12"
    return rows


def slide_images(work, pdf):
    out = work / "slides"
    out.mkdir(exist_ok=True)
    if pdf:
        sh(["pdftoppm", "-png", "-scale-to-x", "1920", "-scale-to-y", "1080", str(pdf), str(out / "p")])
        pages = sorted(out.glob("p-*.png"))
        assert len(pages) == 11, f"expected 11 slide pages, got {len(pages)}"
        return {i + 1: p for i, p in enumerate(pages)}
    from playwright.sync_api import sync_playwright  # fallback: render the deck's own HTML
    deck = work / "deck" / "project" / "slides"
    imgs = {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1920, "height": 1080})
        pg.route("https://fonts.googleapis.com/**", lambda r: r.abort())
        for i, sid in enumerate(SLIDE_IDS, 1):
            html = (deck / f"{sid}.html").read_text(encoding="utf-8")
            html = re.sub(r"<aside>.*?</aside>", "", html, flags=re.S)  # speaker notes are not shown
            css = ("body{margin:0}section{position:relative;width:1920px;height:1080px;box-sizing:border-box;overflow:hidden}"
                   "h1,h2,h3,p,table{margin:0}th,td{padding:0.35em 0.6em;border-bottom:1px solid #c5d0cf;text-align:left}"
                   "table{border-collapse:collapse}")
            pg.set_content(f"<html><head><style>{css}</style></head><body>{html}</body></html>", wait_until="load")
            imgs[i] = out / f"s{i:02d}.png"
            pg.screenshot(path=str(imgs[i]))
        b.close()
    return imgs


def prepare_audio(work, rows, audio_dir, preview):
    out = work / "audio"
    out.mkdir(exist_ok=True)
    files = {}
    for r in rows:
        dst = out / f"{r['id']}.wav"
        if preview:
            n = len(re.sub(r"[\s，。、：；%]", "", r["zh"]))
            sh(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono",
                "-t", f"{n / 4.5 + 2 * PAD:.2f}", dst])
        else:
            src = next(audio_dir.glob(f"{r['id']}.*"))
            # trim silence at both ends, then add a short pad so words are not clipped
            trim = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
                    "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,"
                    f"adelay={int(PAD * 1000)},apad=pad_dur={PAD},loudnorm=I=-16:TP=-1.5")
            sh(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", trim, "-ar", "48000", "-ac", "1", dst])
        files[r["id"]] = dst
    return files


def ass_time(t):
    h, m = divmod(t, 3600)
    m, s = divmod(m, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def chunks(text, limit=80):
    """Split a subtitle into pieces of at most ~limit characters at sentence or clause ends."""
    parts = re.split(r"(?<=[.;:!?])\s+", text)
    out, cur = [], ""
    for p in parts:
        if len(cur) + len(p) + 1 <= limit or not cur:
            cur = f"{cur} {p}".strip()
        else:
            out.append(cur)
            cur = p
    out.append(cur)
    return out


def write_ass(work, rows, lengths):
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Public Sans,34,&H00F2F6F5,&H00F2F6F5,&H0018272B,&H0018272B,0,0,0,0,100,100,0,0,1,0,0,2,120,120,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines, t = [], 0.0
    for r in rows:
        L = lengths[r["id"]]
        pieces = chunks(r["en"])
        total = sum(len(p) for p in pieces)
        start = t + PAD
        span = L - 2 * PAD
        for p in pieces:
            d = span * len(p) / total
            lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(start + d)},Sub,,0,0,0,,{p}")
            start += d
        t += L
    path = work / "subs.ass"
    path.write_text(head + "\n".join(lines) + "\n", encoding="utf-8")
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True, type=Path)
    ap.add_argument("--pdf", type=Path)
    ap.add_argument("--audio", type=Path)
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()
    if not a.preview and not a.audio:
        raise SystemExit("give --audio DIR, or --preview")
    rows = segments()
    imgs = slide_images(a.work, a.pdf)
    audio = prepare_audio(a.work, rows, a.audio, a.preview)
    lengths = {k: dur(v) for k, v in audio.items()}
    total = sum(lengths.values())
    web = a.work / "04_website_raw.webm"
    web_start = float((a.work / "04_website_start.txt").read_text())
    parts = []
    for r in rows:
        L, seg = lengths[r["id"]], a.work / f"seg_{r['id']}.mp4"
        # picture at 90% on a dark frame; the 96 px band at the bottom holds the subtitles,
        # so they never cover slide text such as source lines
        vf = "scale=1728:972,pad=1920:1080:96:12:color=0x18272b,fps=30,format=yuv420p"
        if r["id"] == "04":
            v_in = ["-ss", f"{web_start:.2f}", "-i", str(web)]
            vf = f"tpad=stop_mode=clone:stop_duration={L},{vf}"   # hold the last frame if the voice runs longer
        else:
            v_in = ["-loop", "1", "-i", str(imgs[SLIDE_OF[r['id']]])]
        sh(["ffmpeg", "-v", "error", "-y", *v_in, "-i", str(audio[r["id"]]), "-t", f"{L:.3f}",
            "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-map", "0:v", "-map", "1:a", str(seg)])
        parts.append(seg)
    lst = a.work / "concat.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts))
    joined = a.work / "joined.mp4"
    sh(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined)])
    subs = write_ass(a.work, rows, lengths)
    name = "haze_window_demo_preview.mp4" if a.preview else "haze_window_demo.mp4"
    final = a.work / name
    sh(["ffmpeg", "-v", "error", "-y", "-i", str(joined), "-vf", f"ass={subs}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-c:a", "copy", "-movflags", "+faststart", str(final)])
    for r in rows:
        print(f"{r['id']}  {lengths[r['id']]:5.1f} s")
    print(f"total {total:.1f} s; file {final} ({final.stat().st_size / 1e6:.1f} MB)")
    if total > LIMIT:
        raise SystemExit(f"OVER THE 3:00 LIMIT by {total - LIMIT:.1f} s")


if __name__ == "__main__":
    main()
