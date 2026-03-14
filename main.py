import socket
import threading
import webbrowser
import re
from dataclasses import dataclass, field
from io import BytesIO

import customtkinter as ctk
import feedparser
import requests
from PIL import Image

socket.setdefaulttimeout(10)

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

RSS_FEEDS = [
    ("BBC News", "https://feeds.bbci.co.uk/news/rss.xml"),
    ("Reuters", "https://feeds.reuters.com/reuters/topNews"),
    ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index"),
]

IMAGE_SIZE = (140, 90)
DESCRIPTION_MAX_CHARS = 220


# ---------------------------------------------------------------------------
# Data layer
# ---------------------------------------------------------------------------

@dataclass
class FeedItem:
    title: str
    description: str
    url: str
    thumbnail_url: str
    source_name: str


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > DESCRIPTION_MAX_CHARS:
        text = text[:DESCRIPTION_MAX_CHARS].rsplit(" ", 1)[0] + "…"
    return text


def extract_thumbnail(entry) -> str:
    # 1. media:content
    media = getattr(entry, "media_content", None)
    if media:
        for m in media:
            if m.get("url"):
                return m["url"]
    # 2. media:thumbnail
    thumb = getattr(entry, "media_thumbnail", None)
    if thumb:
        for t in thumb:
            if t.get("url"):
                return t["url"]
    # 3. enclosures
    for enc in getattr(entry, "enclosures", []):
        if enc.get("type", "").startswith("image/") and enc.get("url"):
            return enc["url"]
    # 4. first <img> in summary
    summary = getattr(entry, "summary", "") or ""
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', summary)
    if m:
        return m.group(1)
    return ""


class FeedManager:
    def fetch_all(self, feeds: list[tuple[str, str]]) -> list[FeedItem]:
        items: list[FeedItem] = []
        for name, url in feeds:
            try:
                parsed = feedparser.parse(url)
                for entry in parsed.entries:
                    title = getattr(entry, "title", "").strip()
                    summary = strip_html(getattr(entry, "summary", "") or "")
                    link = getattr(entry, "link", "")
                    thumbnail = extract_thumbnail(entry)
                    if title:
                        items.append(FeedItem(title, summary, link, thumbnail, name))
            except Exception as exc:
                print(f"[FeedManager] Failed to fetch {url!r}: {exc}")
        return items


# ---------------------------------------------------------------------------
# Image loader with in-memory cache
# ---------------------------------------------------------------------------

class ImageLoader:
    def __init__(self, root: ctk.CTk):
        self._root = root
        self._cache: dict[str, ctk.CTkImage] = {}
        self._placeholder = self._make_placeholder()

    def _make_placeholder(self) -> ctk.CTkImage:
        img = Image.new("RGB", IMAGE_SIZE, color=(80, 80, 80))
        return ctk.CTkImage(light_image=img, dark_image=img, size=IMAGE_SIZE)

    @property
    def placeholder(self) -> ctk.CTkImage:
        return self._placeholder

    def get(self, url: str, callback) -> None:
        if not url:
            return
        if url in self._cache:
            callback(self._cache[url])
            return

        def worker():
            try:
                resp = requests.get(url, timeout=8, stream=True)
                resp.raise_for_status()
                img = Image.open(BytesIO(resp.content)).convert("RGB")
                img.thumbnail(IMAGE_SIZE, Image.LANCZOS)
                # pad to exact size
                padded = Image.new("RGB", IMAGE_SIZE, (80, 80, 80))
                x = (IMAGE_SIZE[0] - img.width) // 2
                y = (IMAGE_SIZE[1] - img.height) // 2
                padded.paste(img, (x, y))
                ctk_img = ctk.CTkImage(light_image=padded, dark_image=padded, size=IMAGE_SIZE)
                self._cache[url] = ctk_img
                self._root.after(0, lambda: callback(ctk_img))
            except Exception:
                pass  # keep placeholder

        t = threading.Thread(target=worker, daemon=True)
        t.start()


# ---------------------------------------------------------------------------
# News card widget
# ---------------------------------------------------------------------------

class NewsCardFrame(ctk.CTkFrame):
    def __init__(self, parent, item: FeedItem, image_loader: ImageLoader, **kwargs):
        super().__init__(parent, corner_radius=8, **kwargs)
        self._url = item.url
        self._default_color = self.cget("fg_color")

        self.grid_columnconfigure(1, weight=1)

        # Thumbnail
        self._img_label = ctk.CTkLabel(self, text="", image=image_loader.placeholder,
                                       width=IMAGE_SIZE[0], height=IMAGE_SIZE[1])
        self._img_label.grid(row=0, column=0, rowspan=3, padx=(10, 8), pady=10, sticky="n")

        # Source
        source_label = ctk.CTkLabel(self, text=item.source_name,
                                    font=ctk.CTkFont(size=11),
                                    text_color="gray60", anchor="w")
        source_label.grid(row=0, column=1, padx=(0, 10), pady=(10, 0), sticky="ew")

        # Title
        title_label = ctk.CTkLabel(self, text=item.title,
                                   font=ctk.CTkFont(size=14, weight="bold"),
                                   wraplength=520, anchor="w", justify="left")
        title_label.grid(row=1, column=1, padx=(0, 10), pady=(2, 4), sticky="ew")

        # Description
        if item.description:
            desc_label = ctk.CTkLabel(self, text=item.description,
                                      font=ctk.CTkFont(size=12),
                                      wraplength=520, anchor="w", justify="left",
                                      text_color="gray70")
            desc_label.grid(row=2, column=1, padx=(0, 10), pady=(0, 10), sticky="ew")

        # Hover + click bindings on all children
        for widget in [self, self._img_label, source_label, title_label]:
            widget.bind("<Button-1>", self._open_link)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
        if item.description:
            desc_label.bind("<Button-1>", self._open_link)
            desc_label.bind("<Enter>", self._on_enter)
            desc_label.bind("<Leave>", self._on_leave)

        # Load real image
        image_loader.get(item.thumbnail_url, self._set_image)

    def _set_image(self, img: ctk.CTkImage) -> None:
        self._img_label.configure(image=img)

    def _open_link(self, _event=None) -> None:
        if self._url:
            webbrowser.open(self._url)

    def _on_enter(self, _event=None) -> None:
        self.configure(fg_color=("gray85", "gray25"))

    def _on_leave(self, _event=None) -> None:
        self.configure(fg_color=self._default_color)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

class SidebarFrame(ctk.CTkFrame):
    def __init__(self, parent, feeds: list[tuple[str, str]], on_refresh, **kwargs):
        super().__init__(parent, width=200, corner_radius=0, **kwargs)
        self._on_refresh = on_refresh
        self._checkboxes: dict[str, ctk.BooleanVar] = {}

        ctk.CTkLabel(self, text="News Feed",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(padx=16, pady=(20, 4))

        ctk.CTkLabel(self, text="Sources",
                     font=ctk.CTkFont(size=12), text_color="gray60").pack(padx=16, pady=(12, 4), anchor="w")

        for name, _url in feeds:
            var = ctk.BooleanVar(value=True)
            self._checkboxes[name] = var
            ctk.CTkCheckBox(self, text=name, variable=var,
                            font=ctk.CTkFont(size=13)).pack(padx=16, pady=3, anchor="w")

        self._refresh_btn = ctk.CTkButton(self, text="Refresh", command=self._on_refresh)
        self._refresh_btn.pack(padx=16, pady=(20, 8), fill="x")

        # Dark / light toggle
        self._appearance_var = ctk.StringVar(value="System")
        ctk.CTkOptionMenu(self, values=["System", "Light", "Dark"],
                          variable=self._appearance_var,
                          command=ctk.set_appearance_mode).pack(padx=16, pady=(0, 8), fill="x")

        self._status_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=11),
                                          text_color="gray60")
        self._status_label.pack(padx=16, pady=(4, 0))

    def set_status(self, text: str) -> None:
        self._status_label.configure(text=text)

    def set_loading(self, loading: bool) -> None:
        state = "disabled" if loading else "normal"
        self._refresh_btn.configure(state=state)

    def checked_feeds(self, all_feeds: list[tuple[str, str]]) -> list[tuple[str, str]]:
        return [(name, url) for name, url in all_feeds if self._checkboxes.get(name, ctk.BooleanVar(value=True)).get()]


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

class NewsApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("News Feed")
        self.geometry("900x700")
        self.minsize(700, 500)

        self._feed_manager = FeedManager()
        self._image_loader = ImageLoader(self)
        self._fetch_generation = 0

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._sidebar = SidebarFrame(self, RSS_FEEDS, on_refresh=self._start_refresh)
        self._sidebar.grid(row=0, column=0, sticky="nsew")

        self._scroll_frame = ctk.CTkScrollableFrame(self, corner_radius=0)
        self._scroll_frame.grid(row=0, column=1, sticky="nsew")
        self._scroll_frame.grid_columnconfigure(0, weight=1)

        self.after(100, self._start_refresh)

    def _start_refresh(self) -> None:
        self._fetch_generation += 1
        generation = self._fetch_generation

        self._sidebar.set_loading(True)
        self._sidebar.set_status("Loading…")
        self._clear_cards()

        feeds = self._sidebar.checked_feeds(RSS_FEEDS)

        def worker():
            items = self._feed_manager.fetch_all(feeds)
            self.after(0, lambda: self._render_cards(items, generation))

        threading.Thread(target=worker, daemon=True).start()

    def _clear_cards(self) -> None:
        for widget in self._scroll_frame.winfo_children():
            widget.destroy()

    def _render_cards(self, items: list[FeedItem], generation: int) -> None:
        if generation != self._fetch_generation:
            return  # stale result, discard

        self._sidebar.set_loading(False)
        self._sidebar.set_status(f"{len(items)} articles")

        for item in items:
            card = NewsCardFrame(self._scroll_frame, item, self._image_loader)
            card.grid(sticky="ew", padx=10, pady=5)
            self._scroll_frame.grid_columnconfigure(0, weight=1)


if __name__ == "__main__":
    app = NewsApp()
    app.mainloop()
