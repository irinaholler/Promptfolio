import os, json
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Table, Column, Integer, ForeignKey, or_, func
from sqlalchemy.orm import relationship
from slugify import slugify

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "gallery.db")
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

with app.app_context():
    db.create_all()
