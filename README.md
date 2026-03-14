# News Feed

A desktop RSS news reader with auto-scrolling, thumbnails, and a configurable set of sources. Built with Python and CustomTkinter.

## Features

- Fetches articles from multiple RSS feeds simultaneously
- Displays each article as a card with thumbnail, source, title, and description
- Auto-scrolls card by card on a timer — pauses when you hover
- Thumbnails loaded lazily in the background; falls back to `og:image` from the article page if the feed doesn't provide one
- Sidebar to toggle individual sources on/off and manually refresh
- All key settings controlled via `config.ini` — no code changes needed

## Requirements

- Python 3.10 or newer
- Internet connection

## Running the app

### Mac / Linux

```bash
./run.sh
```

### Windows

Double-click `run.bat` or run it in a terminal:

```bat
run.bat
```

Both scripts will automatically create a virtual environment and install dependencies on the first run. Subsequent runs start immediately.

## Project files

```
news-feed/
├── main.py           # Application code
├── config.ini        # All user-configurable settings
├── requirements.txt  # Python dependencies
├── run.sh            # Launcher for Mac / Linux
└── run.bat           # Launcher for Windows
```

## Configuration

All settings live in `config.ini`. Restart the app after making changes.

### [display]

| Key | Default | Description |
|-----|---------|-------------|
| `visible_cards` | `6` | Number of cards visible at once — window height is auto-sized to fit |
| `window_width` | `900` | Window width in pixels |
| `appearance` | `Dark` | Theme mode: `System`, `Light`, or `Dark` |
| `color_theme` | `blue` | Accent colour: `blue`, `green`, or `dark-blue` |
| `background_color` | *(empty)* | Custom background hex color (e.g. `#0055A4`). Leave empty to use the default theme color |

### [scrolling]

| Key | Default | Description |
|-----|---------|-------------|
| `card_interval_ms` | `3000` | Milliseconds to display each card before advancing |
| `pause_top_ms` | `2000` | Milliseconds to pause at the top before restarting |
| `speed_step_ms` | `500` | How much each `+`/`-` keypress changes the interval |
| `speed_min_ms` | `500` | Minimum allowed interval |
| `speed_max_ms` | `10000` | Maximum allowed interval |
| `speed_faster_key` | `plus` | Key to speed up scrolling |
| `speed_slower_key` | `minus` | Key to slow down scrolling |

### [feeds]

| Key | Description |
|-----|-------------|
| `default_source` | Name of the feed that starts checked on launch (must match a feed name exactly) |
| *(any name)* `= URL` | Add or remove feeds — each line is a source shown in the sidebar |

Example — add a new feed:

```ini
[feeds]
default_source = BBC News
BBC News     = https://feeds.bbci.co.uk/news/rss.xml
My Blog      = https://example.com/feed.xml
```

### [articles]

| Key | Default | Description |
|-----|---------|-------------|
| `description_max_chars` | `400` | Maximum characters shown in the article snippet |
| `thumbnail_width` | `140` | Thumbnail width in pixels |
| `thumbnail_height` | `90` | Thumbnail height in pixels |

## Default sources

| Source | Type |
|--------|------|
| BBC News | General news |
| AP News | General / wire news |
| NPR News | General news |
| Ars Technica | Technology |
| The Verge | Technology |
| Wired | Technology |
| Hacker News | Technology / links |
| TechCrunch | Technology / startups |

## Dependencies

| Package | Purpose |
|---------|---------|
| `customtkinter` | Modern themed UI widgets |
| `feedparser` | RSS/Atom feed parsing |
| `requests` | HTTP image and feed fetching |
| `Pillow` | Image resizing and processing |
