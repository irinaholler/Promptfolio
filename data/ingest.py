# data/ingest.py
import os, sys, json
from PIL import Image as PILImage
from colorthief import ColorThief
from slugify import slugify

# Make sure Python can import app.py from the project root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import app, db, Image, Tag

DATA_DIR   = "data"
IMAGES_DIR = "static/images"
META_PATH  = os.path.join(DATA_DIR, "meta.json")

with app.app_context():
    # Load optional metadata JSON (title/prompt/tags/etc.)
    meta = {}
    if os.path.exists(META_PATH):
        with open(META_PATH, "r", encoding="utf-8") as f:
            meta = json.load(f)

    # Walk images directory
    for fname in os.listdir(IMAGES_DIR):
        if not fname.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            continue

        full = os.path.join(IMAGES_DIR, fname)
        # Basic image size
        try:
            w, h = PILImage.open(full).size
        except Exception:
            # Skip unreadable images
            print(f"⚠️  Skipping unreadable image: {fname}")
            continue

        # Extract a small color palette
        try:
            ct = ColorThief(full)
            palette = ["#%02x%02x%02x" % tuple(c) for c in ct.get_palette(color_count=5)]
        except Exception:
            palette = []

        # Read metadata for this file (if any)
        m = meta.get(fname, {})
        title    = m.get("title")  or os.path.splitext(fname)[0].replace("_"," ").title()
        prompt   = m.get("prompt", "")
        model    = m.get("model", "")
        seed     = str(m.get("seed", ""))
        preset   = m.get("preset", "")
        tag_list = m.get("tags", [])  # e.g. ["food","vertical","chiaroscuro"]

        # Upsert by filename
        rec = Image.query.filter_by(filename=fname).first()
        if rec:
            # UPDATE
            rec.title   = title
            rec.slug    = slugify(title)[:180]
            rec.prompt  = prompt
            rec.model   = model
            rec.seed    = seed
            rec.preset  = preset
            rec.width   = w
            rec.height  = h
            rec.palette = json.dumps(palette)

            # Update tags
            rec.tags.clear()
            for t in tag_list:
                tslug = slugify(t)
                tag = Tag.query.filter_by(slug=tslug).first()
                if not tag:
                    tag = Tag(name=t, slug=tslug)
                rec.tags.append(tag)

            print(f"🔁 Updated: {fname}")
        else:
            # INSERT
            rec = Image(
                slug=slugify(title)[:180],
                title=title,
                filename=fname,
                prompt=prompt,
                model=model,
                seed=seed,
                preset=preset,
                width=w, height=h,
                palette=json.dumps(palette),
                likes=0
            )
            for t in tag_list:
                tslug = slugify(t)
                tag = Tag.query.filter_by(slug=tslug).first()
                if not tag:
                    tag = Tag(name=t, slug=tslug)
                rec.tags.append(tag)

            db.session.add(rec)
            print(f"➕ Inserted: {fname}")

    db.session.commit()
    print("✅ Done.")
