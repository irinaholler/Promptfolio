import os, json
from flask import Flask, render_template, request, jsonify
from flask import abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Table, Column, Integer, ForeignKey, or_, func
from sqlalchemy.orm import relationship
from slugify import slugify

HOME = os.environ.get("HOME", "/home")           # Azure writable root
DATA_DIR = os.path.join(HOME, "data")            # e.g., /home/data
os.makedirs(DATA_DIR, exist_ok=True)             # ensure it exists

basedir = os.path.abspath(os.path.dirname(__file__))

DB_FILE = os.environ.get("DB_FILE") or os.path.join(basedir, "gallery.db")   # /home/data/gallery.db

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_FILE}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

@app.after_request
def no_cache(resp):
    resp.headers["Cache-Control"] = "no-store"
    return resp

# --- Models ---
image_tags = Table(
    "image_tags", db.metadata,
    Column("image_id", Integer, ForeignKey("image.id")),
    Column("tag_id", Integer, ForeignKey("tag.id"))
)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(180), unique=True, index=True)
    title = db.Column(db.String(180))
    filename = db.Column(db.String(255), unique=True)
    prompt = db.Column(db.Text)
    model = db.Column(db.String(120))
    seed = db.Column(db.String(64))
    preset = db.Column(db.String(120))
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    palette = db.Column(db.Text)           # JSON list of hex colors
    likes = db.Column(db.Integer, default=0)
    tags = relationship("Tag", secondary=image_tags, backref="images")

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, index=True)
    slug = db.Column(db.String(60), unique=True, index=True)

@app.template_filter("loadjson")
def loadjson(s):
    try:
        return json.loads(s) if s else []
    except Exception:
        return []

# --- Routes ---
@app.route("/")
def home():
    q = request.args.get("q", "").strip()
    tag = request.args.get("tag")
    color = request.args.get("color")
    shuffle = request.args.get("shuffle", "1") == "1"   # default: shuffle

    images = Image.query

    # SEARCH: title + prompt + tags
    if q:
        like = f"%{q}%"
        images = (images
                  .outerjoin(Image.tags)
                  .filter(or_(
                      Image.title.ilike(like),
                      Image.prompt.ilike(like),
                      Tag.name.ilike(like)
                  ))
                  .distinct())

    # TAG filter
    if tag:
        images = images.join(Image.tags).filter(Tag.slug == tag)

    # COLOR filter (hex contained in stored palette JSON)
    if color:
        images = images.filter(Image.palette.contains(color.lower()))

    # ORDER
    images = images.order_by(func.random() if shuffle else Image.id.desc()).limit(60).all()

    if request.headers.get("HX-Request"):
        return render_template("_cards.html", images=images)
    return render_template("index.html", images=images)

@app.route("/recipe/<slug>")
def recipe(slug):
    img = Image.query.filter_by(slug=slug).first_or_404()
    return render_template("_recipe.html", img=img)

@app.route("/like/<int:image_id>", methods=["POST"])
def like(image_id):
    img = Image.query.get_or_404(image_id)
    img.likes = (img.likes or 0) + 1
    db.session.commit()
    return jsonify({"likes": img.likes})

# --- One-time ingest route to build DB on the server ---
def _open_image_size(path):
    try:
        from PIL import Image as PILImage
        with PILImage.open(path) as im:
            return im.size
    except Exception:
        return (0, 0)

def _extract_palette(path):
    try:
        from colorthief import ColorThief
        ct = ColorThief(path)
        return ["#%02x%02x%02x" % tuple(c) for c in ct.get_palette(color_count=5)]
    except Exception:
        return []

def _ingest_run():
    images_dir = os.path.join(basedir, "static", "images")
    meta_path  = os.path.join(basedir, "data", "meta.json")
    meta = {}
    if os.path.exists(meta_path):
        meta = json.load(open(meta_path, "r", encoding="utf-8"))

    added = updated = 0
    for fname in os.listdir(images_dir):
        if not fname.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            continue
        full = os.path.join(images_dir, fname)

        # size + palette (best-effort)
        try:
            w, h = _open_image_size(full)
        except Exception:
            continue
        try:
            ct = ColorThief(full)
            palette = _extract_palette(full)
        except Exception:
            palette = []

        m = meta.get(fname, {})
        title   = m.get("title") or os.path.splitext(fname)[0].replace("_"," ").title()
        prompt  = m.get("prompt","")
        model   = m.get("model","")
        seed    = str(m.get("seed",""))
        preset  = m.get("preset","")
        tag_list = m.get("tags", [])

        rec = Image.query.filter_by(filename=fname).first()
        if rec:
            updated += 1
            rec.title = title
            rec.slug = slugify(title)[:180]
            rec.prompt = prompt
            rec.model = model
            rec.seed = seed
            rec.preset = preset
            rec.width = w; rec.height = h
            rec.palette = json.dumps(palette)
            rec.tags.clear()
        else:
            added += 1
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
            db.session.add(rec)

        for t in tag_list:
            tslug = slugify(t)
            tag = Tag.query.filter_by(slug=tslug).first()
            if not tag:
                tag = Tag(name=t, slug=tslug)
            rec.tags.append(tag)

    db.session.commit()
    return added, updated

@app.route("/admin/ingest")
def admin_ingest():
    token = request.args.get("t")
    expected = os.environ.get("ADMIN_TOKEN")
    if not expected or token != expected:
        return abort(403)
    a, u = _ingest_run()
    return f"OK — added {a}, updated {u}"


with app.app_context():
    db.create_all()
