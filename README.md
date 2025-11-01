#📘 Promptfolio

Showcase AI images with their prompts in a tiny Flask + HTMX gallery—searchable, likable, and beautifully glassy.

✨ Features

Beautiful cards with title overlay + subtle shine

Glass modal with a large preview and the full “recipe” (prompt, model, seed, tags, palette)

Copy prompt button + Show more/less (no scrollbars in the prompt area)

Search across title + prompt + tags (live search + Enter to submit)

Voice search (Chrome/Edge) with one click

Shuffle gallery on load, plus Shuffle button & keyboard R

Like button with a local guard (no double-likes on the same device)

Masonry grid (CSS columns) with Safari-friendly fallbacks

Animated wordmark (SVG “draw” effect) + tasteful, cinematic color palette

🧭 Project Structure
Promptfolio/
├─ app.py # Flask app, routes, models
├─ gallery.db # SQLite DB (created automatically)
├─ data/
│ ├─ meta.json # Your image metadata (title, prompt, tags…)
│ └─ ingest.py # Upsert images from static/images + meta.json
├─ static/
│ ├─ images/ # Place your image files here
│ ├─ styles.css # Main styles (glass, animations, responsive)
│ └─ script.js # Likes, modal, search, shuffle, voice, zoom
└─ templates/
├─ base.html # Layout + header + search + modal shell
├─ index.html # Home page
├─ \_cards.html # Grid container (HTMX target)
├─ \_card.html # Single card
└─ \_recipe.html # Modal content (large preview + info)

gallery.db is auto-created on first run. It’s ignored by git.

🛠️ Setup (Beginner-friendly)

Create & activate a virtual environment

python -m venv .venv
source .venv/bin/activate # Windows: .venv\Scripts\activate

Install packages

pip install Flask Flask-SQLAlchemy python-slugify Pillow colorthief

Run the dev server

python -m flask run

Open http://127.0.0.1:5000/

If flask isn’t found, set:
export FLASK_APP=app.py (macOS/Linux) or set FLASK_APP=app.py (Windows)

📸 Add Images (Your Portfolio Flow)

Drop files into static/images/
Use clear names (e.g. Latte_Lure.jpg).

Describe them in data/meta.json (optional but recommended):

"Latte_Lure.jpg": {
"title": "Latte Lure",
"prompt": "Short description or full prompt here…",
"model": "Leonardo Phoenix",
"seed": "123456",
"preset": "Macro",
"tags": ["coffee","macro","bokeh","vertical"]
}

Ingest (update/insert in DB):

python -m data.ingest

Refresh the site (hard refresh: ⌘⇧R)

The ingester:

reads every file in static/images/

extracts width/height + a small color palette

uses meta.json to fill title/prompt/tags/model/seed/preset

updates existing rows (upsert), so you can keep iterating

🔎 Search, Shuffle, Shortcuts

Type in the search → results update (live)

Press Enter → submits (Safari-friendly)

Searches across: title, prompt, tags

Press R → shuffle grid (HTMX refresh)

Click Shuffle button → same as above

Voice: click 🎤 and speak (Chrome/Edge)

❤️ Likes

Click ❤️ to like an image.
It increments once per image per browser (stored via localStorage).

🪟 Modal (Recipe) View

Click a card → modal with large preview + details

Click the big image to zoom slightly

Copy prompt copies the full text

Show more reveals additional lines (no ugly scrollbars)

🧪 Troubleshooting

“ModuleNotFoundError: flask_sqlalchemy”
→ pip install Flask-SQLAlchemy

Ingester: “No module named app”
→ Run from the project root (same folder as app.py):
python -m data.ingest

New image not appearing

Confirm the file is in static/images/ with the exact filename

Update data/meta.json (optional but nice)

Run python -m data.ingest

Open / (no ?tag=/?color= filters) and hard refresh

Sizes are all the same

The size shown comes from the DB (Image.width/height) written by the ingester.

Re-run python -m data.ingest after replacing images.

Safari layout looks gappy

We include Safari-safe break-inside rules and a reveal fallback.

Hard refresh (⌘⇧R). If needed, reduce grid density:

@supports (-webkit-touch-callout: none){ .grid{ columns: 3 280px } }

Search not working

Ensure HTMX is loaded once in base.html:

<script src="https://unpkg.com/htmx.org@1.9.12"></script>

Input has id="q" and the form has hx-get="/" hx-target="#grid".

🚀 Deploy (quick suggestions)

Gunicorn (basic):

pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:8000 app:app

Render/Fly/Heroku: point the start command to the gunicorn line above.

Persist your static/images/ somewhere durable (cloud storage or bind mount) if you plan uploads later.

🧾 Example requirements.txt
Flask
Flask-SQLAlchemy
python-slugify
Pillow
colorthief

Add if you deploy with Gunicorn:

gunicorn

🧱 Roadmap (nice next steps)

Upload form (drop an image, fill metadata, auto-ingest)

Tag cloud + color filters (click a palette swatch to filter by color)

Share buttons (copy link to a specific recipe/modal)

Favorite lists (store locally; export as JSON)

Static build (export HTML grid for GitHub Pages)

Dark/Light theme toggle

📝 License

**Code:** MIT — use, modify, and share freely; attribution appreciated.

**Images / Artwork:** © Irini Holler. You’re welcome to browse and take inspiration.
If you’d like to use any image (in posts, projects, thumbnails, prints, etc.), please ask first:
open an issue or email me at irina@mygrin.de.  
No redistribution, resale, or inclusion in datasets/models without permission.

💌 Credits

Built with ❤️ using Flask, HTMX, and a sprinkle of tasteful CSS.
Design language inspired by cinematic UI, glass surfaces, and your own AI artworks.

Re-ingest (so the DB learns about it)
Localhost

# from your project root

source ~/Promptfolio/venv/bin/activate
python - <<'PY'
from app import app,\_ingest_run
with app.app_context():
a,u=\_ingest_run()
print("INGEST:", a, "added,", u, "updated")
PY

# then run your app if needed:

flask --app app run --debug

python app.py  
git push origin master

# Pushed to GitHub

cd ~/Promptfolio
git pull --rebase origin master

python - <<'PY'
from app import app, \_ingest_run
with app.app_context():
print("INGEST:", \*\_ingest_run())
PY

# On PythonAnywhere

cd ~/Promptfolio
git fetch origin

# overwrite working tree with GitHub's master

git reset --hard origin/master

# sanity: do you see your new images now?

ls -1 static/images | tail -n 20

git pull origin master

source venv/bin/activate
python - <<'PY'
from app import app,\_ingest_run
with app.app_context():
a,u=\_ingest_run()
print("INGEST:", a, "added,", u, "updated")
PY
