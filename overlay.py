#!/usr/bin/env python3
import ctypes
import os
import random
import time
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog

BG = "#0a0a0a"
DEFAULT_FLOAT = 5.8
BOX_W = 286
BOX_H = 112
BOX_RADIUS = 8
BOX_SHADOW = 6
BOX_TEXT_W = 232
BOX_GAP = 316
LYRIC_OFFSET = 0.0
APPEAR_LEAD = 0.65
AUDIO_LATENCY = 0.0

LRC = [
    (0, "Her love is in your head"),
    (4.5, "You lost your earrings in her bed"),
    (9, "You couldn't tell her that you lost 'em"),
    (13.5, "Cause you're scared and not talking"),
    (18, "So you think of what to say"),
    (22, "Save it for another day"),
    (26, "You just never had the heart"),
    (30, "Now they drift further apart"),
    (34, "From you, oh"),
    (38, "From you, oh"),
    (42, "From you, oh"),
    (46, "From you, oh"),
    (50, "Her love is in your head"),
    (54.5, "You lost your earrings in her bed"),
    (59, "You couldn't tell her that you lost 'em"),
    (63.5, "Cause you're scared and not talking"),
    (68, "So you think of what to say"),
    (72, "Save it for another day"),
    (76, "You just never had the heart"),
    (80, "Now they drift further apart"),
    (84, "Extra, extra, read all about it"),
    (88, "Malcolm's in his feelings"),
    (92, "And he can't get out of it"),
    (96, "Extra, extra, read all about it"),
    (100, "Malcolm's in his feelings"),
    (104, "And he can't get out of it"),
    (108, "From you, oh"),
    (112, "From you, oh"),
    (116, "Extra, extra, read all about it"),
    (120, "Malcolm's in his feelings"),
    (124, "And he can't get out of it"),
    (128, "Can't get out of it"),
    (132, "Can't get out of it"),
    (137, "I hope you like my mix tape"),
]


class AudioPlayer:
    def __init__(self):
        self.alias = "song_overlay"
        self.loaded_path = None
        self._state = "stopped"
        self._started_at = None
        self._paused_pos = 0.0
        self._winmm = ctypes.windll.winmm
        self._buf = ctypes.create_unicode_buffer(512)
        self._err = ctypes.create_unicode_buffer(512)

    def _send(self, command: str):
        result = self._winmm.mciSendStringW(command, self._buf, len(self._buf), 0)
        if result != 0:
            self._winmm.mciGetErrorStringW(result, self._err, len(self._err))
            raise RuntimeError(self._err.value or f"MCI error {result}")
        return self._buf.value

    def close(self):
        try:
            self._send(f"close {self.alias}")
        except Exception:
            pass
        self.loaded_path = None
        self._state = "stopped"
        self._started_at = None
        self._paused_pos = 0.0

    def load(self, path: str):
        self.close()
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(abs_path)
        quoted = abs_path.replace('"', '\\"')
        self._send(f'open "{quoted}" alias {self.alias}')
        self._send(f"set {self.alias} time format milliseconds")
        self.loaded_path = abs_path
        self._state = "loaded"
        self._started_at = None
        self._paused_pos = 0.0

    def play(self):
        if not self.loaded_path:
            raise RuntimeError("No audio file loaded")
        self._send(f"play {self.alias}")
        self._started_at = time.monotonic()
        self._paused_pos = 0.0
        self._state = "playing"

    def pause(self):
        if self.loaded_path:
            try:
                self._send(f"pause {self.alias}")
                self._paused_pos = self.position_seconds()
                self._state = "paused"
            except Exception:
                pass

    def resume(self):
        if self.loaded_path:
            try:
                self._send(f"resume {self.alias}")
                self._started_at = time.monotonic() - self._paused_pos
                self._state = "playing"
            except Exception:
                self.play()

    def position_seconds(self) -> float:
        if not self.loaded_path:
            return 0.0
        if self._state == "paused":
            return max(0.0, self._paused_pos)
        if self._started_at is not None:
            return max(0.0, time.monotonic() - self._started_at)
        pos_ms = self._send(f"status {self.alias} position")
        try:
            return max(0.0, float(pos_ms) / 1000.0)
        except ValueError:
            return 0.0


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Earrings")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        try:
            self.root.attributes("-transparentcolor", BG)
        except tk.TclError:
            pass

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{sw}x{sh}+0+0")
        self.root.configure(bg=BG)

        self.canvas = tk.Canvas(self.root, bg=BG, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.boxes = {}
        self.styles = {}
        self.font = tkfont.Font(family="Arial", size=22)
        self.player = AudioPlayer()
        self.playing = False
        self.paused = False
        self.file = None

        self.lbl = self.canvas.create_text(
            sw // 2,
            sh // 2,
            text="Press SPACE to select an audio file",
            fill="#444",
            font=("Arial", 16),
            anchor="center",
        )

        self.root.bind("<space>", lambda e: self.handle_space())
        self.root.bind("<Escape>", lambda e: self.shutdown())
        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)

        self.tick()
        self.root.mainloop()

    def shutdown(self):
        try:
            self.player.close()
        finally:
            self.root.destroy()

    def handle_space(self):
        if self.file:
            self.toggle_playback()
        else:
            self.pick()

    def pick(self):
        f = filedialog.askopenfilename(
            title="Select audio (Earrings - Malcolm Todd)",
            filetypes=[("Audio", "*.mp3 *.wav *.ogg *.m4a"), ("All files", "*.*")],
        )
        if not f:
            return
        self.file = f
        self.canvas.itemconfig(self.lbl, text="Press SPACE to play / pause")

    def toggle_playback(self):
        if not self.file:
            self.pick()
            return

        if not os.path.exists(self.file):
            self.playing = False
            self.paused = False
            self.canvas.itemconfig(self.lbl, text="File not found. Press SPACE to select another.")
            return

        try:
            if self.player.loaded_path != os.path.abspath(self.file):
                self.player.load(self.file)
                self.player.play()
                self.playing = True
                self.paused = False
                self.canvas.itemconfig(self.lbl, text="")
                return

            if self.playing and not self.paused:
                self.player.pause()
                self.playing = False
                self.paused = True
            elif self.paused:
                self.player.resume()
                self.playing = True
                self.paused = False
        except Exception as e:
            self.playing = False
            self.paused = False
            self.canvas.itemconfig(self.lbl, text=f"Audio error: {str(e)[:70]}")

    def y(self, p, h):
        return (1 - p) * (h + 180) - 120

    def rx(self, ex, w, note_w, m=30):
        usable = max(1, w - note_w - m * 2)
        for _ in range(50):
            x = m + random.random() * usable
            if all(abs(x - e) >= max(BOX_GAP, note_w + 26) for e in ex):
                return x
        return m + random.random() * usable

    def float_duration(self, idx, t):
        if idx == 0:
            return 9.2
        if idx == 1:
            return 8.0
        if idx < 8:
            return 6.7
        if idx < 20:
            return 5.8
        return DEFAULT_FLOAT

    def style_for(self, idx, txt):
        if idx not in self.styles:
            seed = (idx + 1) * 9973 + len(txt) * 97
            rng = random.Random(seed)
            width = rng.randint(268, 322)
            height = rng.randint(100, 132)
            font_size = rng.randint(20, 24)
            radius = rng.randint(7, 12)
            shadow = rng.randint(4, 8)
            text_pad = rng.randint(44, 58)
            float_jitter = rng.uniform(-0.35, 0.55)
            lead_jitter = rng.uniform(-0.18, 0.22)
            self.styles[idx] = {
                "w": width,
                "h": height,
                "font": tkfont.Font(family="Arial", size=font_size),
                "radius": radius,
                "shadow": shadow,
                "text_w": max(120, width - text_pad),
                "float_jitter": float_jitter,
                "lead_jitter": lead_jitter,
                "x_bias": rng.randint(-18, 18),
            }
        return self.styles[idx]

    def fc(self, c, o):
        o = max(0, min(1, o))
        return "#{:02x}{:02x}{:02x}".format(
            int(10 + (int(c[1:3], 16) - 10) * o),
            int(10 + (int(c[3:5], 16) - 10) * o),
            int(10 + (int(c[5:7], 16) - 10) * o),
        )

    def rounded_rect_points(self, x1, y1, x2, y2, r):
        return [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1,
        ]

    def create_note(self, x, y, text, opacity, style):
        shadow_fill = self.fc("#000000", opacity * 0.40)
        note_fill = self.fc("#ffffff", opacity)
        text_fill = self.fc("#111111", opacity)
        w = style["w"]
        h = style["h"]
        r = style["radius"]
        s = style["shadow"]

        shadow = self.canvas.create_polygon(
            self.rounded_rect_points(
                x + s,
                y + s,
                x + w + s,
                y + h + s,
                r,
            ),
            smooth=True,
            splinesteps=16,
            fill=shadow_fill,
            outline="",
        )
        rect = self.canvas.create_polygon(
            self.rounded_rect_points(
                x,
                y,
                x + w,
                y + h,
                r,
            ),
            smooth=True,
            splinesteps=16,
            fill=note_fill,
            outline="",
        )
        tx = self.canvas.create_text(
            x + w / 2,
            y + h / 2,
            text=text,
            fill=text_fill,
            font=style["font"],
            anchor="center",
            width=style["text_w"],
            justify="center",
        )
        return {
            "shadow": shadow,
            "rect": rect,
            "text": tx,
            "x": x,
            "y": y,
            "shown": False,
            "w": w,
            "h": h,
            "radius": r,
            "shadow_pad": s,
            "font": style["font"],
            "text_w": style["text_w"],
            "lead_jitter": style["lead_jitter"],
            "float_jitter": style["float_jitter"],
        }

    def box_age(self, idx, t, ct):
        style = self.style_for(idx, LRC[idx][1])
        return ct - (t - APPEAR_LEAD + style["lead_jitter"])

    def tick(self):
        if self.playing:
            try:
                ct = max(0.0, self.player.position_seconds() + LYRIC_OFFSET - AUDIO_LATENCY)
            except Exception:
                ct = 0.0

            w = self.root.winfo_width() or self.root.winfo_screenwidth()
            h = self.root.winfo_height() or self.root.winfo_screenheight()

            active = set()
            for i, (t, _) in enumerate(LRC):
                duration = self.float_duration(i, t) + self.style_for(i, LRC[i][1])["float_jitter"]
                age = self.box_age(i, t, ct)
                if 0 <= age < duration:
                    active.add(i)

            for bid in list(self.boxes.keys()):
                if bid not in active:
                    box = self.boxes.pop(bid)
                    self.canvas.delete(box["shadow"])
                    self.canvas.delete(box["rect"])
                    self.canvas.delete(box["text"])

            existing_x = [box["x"] for box in self.boxes.values()]

            for i, (t, txt) in enumerate(LRC):
                style = self.style_for(i, txt)
                duration = self.float_duration(i, t) + style["float_jitter"]
                age = self.box_age(i, t, ct)
                if 0 <= age < duration:
                    p = age / duration
                    y = self.y(p, h)
                    opacity = 1.0
                    if p < 0.05:
                        opacity = p / 0.05
                    elif p > 0.80:
                        opacity = max(0, (1 - p) / 0.20)

                    if i in self.boxes:
                        box = self.boxes[i]
                        x = box["x"]
                        self.canvas.coords(
                            box["shadow"],
                            *self.rounded_rect_points(
                                x + box["shadow_pad"],
                                y + box["shadow_pad"],
                                x + box["w"] + box["shadow_pad"],
                                y + box["h"] + box["shadow_pad"],
                                box["radius"],
                            ),
                        )
                        self.canvas.coords(
                            box["rect"],
                            *self.rounded_rect_points(
                                x,
                                y,
                                x + box["w"],
                                y + box["h"],
                                box["radius"],
                            ),
                        )
                        self.canvas.coords(box["text"], x + box["w"] / 2, y + box["h"] / 2)
                        self.canvas.itemconfig(box["shadow"], fill=self.fc("#000000", opacity * 0.40))
                        self.canvas.itemconfig(box["rect"], fill=self.fc("#ffffff", opacity))
                        if not box["shown"] and ct >= t:
                            box["shown"] = True
                            self.canvas.itemconfig(box["text"], text=txt)
                        self.canvas.itemconfig(
                            box["text"],
                            fill=self.fc("#111111", opacity if box["shown"] else 0),
                        )
                    else:
                        x = self.rx(existing_x, w, style["w"]) + style["x_bias"]
                        x = max(20, min(x, max(20, w - style["w"] - 20)))
                        existing_x.append(x)
                        box = self.create_note(x, y, "", opacity, style)
                        if ct >= t:
                            box["shown"] = True
                            self.canvas.itemconfig(box["text"], text=txt)
                            self.canvas.itemconfig(box["text"], fill=self.fc("#111111", opacity))
                        else:
                            self.canvas.itemconfig(box["text"], fill=self.fc("#111111", 0))
                        self.boxes[i] = box

        self.root.after(16, self.tick)


if __name__ == "__main__":
    App()
