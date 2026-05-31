# ?? Floating Lyric Visualizer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A minimalist, multi-platform synchronized lyric visualizer designed to create a "floating" aesthetic for your music. This project provides three different ways to experience synchronized lyrics: a web-based player, a transparent Python desktop overlay, and an Electron-powered "always-on-top" app.

---

## ? Features

*   **Floating Aesthetics:** Lyrics drift upwards with dynamic opacity and random positioning.
*   **YouTube & MP3 Support:** Sync with YouTube videos or load your own local MP3 files.
*   **Multi-Platform Experience:**
    *   **Web (`brat-lyrics.html`):** Browser-based player with full-screen support.
    *   **Python (`overlay.py`):** A transparent, click-through desktop overlay for Windows.
    *   **Electron (`lyric-vsc/`):** A dedicated desktop window wrapper.
*   **Dynamic Styling:** Randomized box sizes, fonts, and "float jitter" for a unique feel every time.

---

## ?? How It Works

The system uses a **Time-to-Lyric Map**. Each lyric is assigned a timestamp (in seconds). As the audio plays, the application:

1.  **Tracking:** Monitors the current playback time of the audio source (YouTube API or HTML5 Audio/MCI).
2.  **Calculation:** Calculates the "age" of each lyric line relative to the current time.
3.  **Animation:** Maps the age to a vertical Y-position and opacity curve. 
4.  **Rendering:** Spawns floating boxes that drift from the bottom to the top of the screen, fading in at the start and out as they reach the top.

---

## ?? Getting Started

### 1. Web Visualizer (`brat-lyrics.html`)
*The quickest way to get started.*
*   **Setup:** Just open `brat-lyrics.html` in any browser.
*   **Controls:**
    *   `Space`: Play/Pause.
    *   `F`: Toggle Fullscreen.
    *   `MP3 Button`: Upload a local file to replace the default track.

### 2. Python Desktop Overlay (`overlay.py`)
*A transparent overlay that sits on top of all windows (Windows Only).*
*   **Setup:** 
    ```bash
    python overlay.py
    ```
*   **Controls:**
    *   `Space`: Select audio file / Play / Pause.
    *   `Esc`: Exit overlay.

### 3. Electron App (`lyric-vsc/`)
*A dedicated desktop window for an always-on-top experience.*
*   **Setup:**
    ```bash
    cd lyric-vsc
    npm install
    npm start
    ```

---

## ?? Customization

To change the lyrics or the song, edit the `LRC` array in the source files:

**JavaScript:**
```javascript
var LRC = [
  [0, "Her love is in your head"],
  [4.5, "You lost your earrings in her bed"]
];
```

**Python:**
```python
LRC = [
    (0, "Her love is in your head"),
    (4.5, "You lost your earrings in her bed"),
]
```

---

## ?? License

Distributed under the MIT License. See `LICENSE` for more information.
