/* ------------------ UTIL ------------------ */
const $ = (sel, root = document) => root.querySelector(sel);
document.documentElement.classList.add('js');

/* Base-path helper: works at / and at /Promptfolio */
const BASE = (() => {
    // first segment, e.g. "/Promptfolio" or null if "/"
    const m = location.pathname.match(/^\/[^/]+/);
    // ignore if we're already at root or in /static
    if (!m || m[0] === '/static') return '';
    return m[0] === '/' ? '' : m[0];
})();
const url = (p) => BASE + p; // joiner

/* ------------------ LIKE + COPY ------------------ */
document.addEventListener("click", async (e) => {
    // Like button (stop bubbling so the card doesn't open the modal)
    const likeBtn = e.target.closest(".like");
    if (likeBtn) {
        e.stopPropagation();

        // Prefer server-generated URL; fallback to base + id
        const explicitUrl = likeBtn.dataset.likeUrl;
        const id = likeBtn.dataset.id;
        const api = explicitUrl || (id ? url(`/like/${id}`) : null);

        if (!api) {
            console.error("Like failed: no URL or id on button", likeBtn);
            return;
        }

        const key = "liked-" + (id || api);
        if (localStorage.getItem(key)) return;

        try {
            const res = await fetch(api, { method: "POST" });
            if (!res.ok) throw new Error(await res.text());
            const data = await res.json();
            likeBtn.querySelector("span").textContent = data.likes;
            localStorage.setItem(key, "1");
            likeBtn.classList.add("liked");
            setTimeout(() => likeBtn.classList.remove("liked"), 250);
        } catch (err) {
            console.error("Like failed", err);
        }
        return;
    }

    // Copy prompt
    if (e.target.classList.contains("copy")) {
        e.stopPropagation();
        const txt = e.target.dataset.text || "";
        navigator.clipboard.writeText(txt);
        e.target.textContent = "Copied ✓";
        setTimeout(() => (e.target.textContent = "Copy prompt"), 1200);
    }
});

/* ------------------ VOICE SEARCH (Chrome/Edge) ------------------ */
const mic = document.getElementById("voice");
if (mic && "webkitSpeechRecognition" in window) {
    const rec = new webkitSpeechRecognition();
    rec.lang = "en-US";
    rec.interimResults = false;
    mic.onclick = () => rec.start();
    rec.onresult = (ev) => {
        const query = ev.results[0][0].transcript;
        const form = mic.closest("form");
        const input = form.querySelector("input[type=search]");
        input.value = query;
        if (form.requestSubmit) form.requestSubmit();
        else form.dispatchEvent(new Event("submit", { bubbles: true }));
    };
}

/* ------------------ REVEAL ON SCROLL (Safari-safe) ------------------ */
let io;
function attachCardObservers() {
    const cards = document.querySelectorAll(".card");
    if ("IntersectionObserver" in window) {
        if (!io) {
            io = new IntersectionObserver(
                (entries) => {
                    entries.forEach((ent) => {
                        if (ent.isIntersecting) {
                            ent.target.classList.add("reveal");
                            io.unobserve(ent.target);
                        }
                    });
                },
                { rootMargin: "0px 0px -10% 0px" }
            );
        }
        cards.forEach((c) => io.observe(c));
    }
    requestAnimationFrame(() => cards.forEach((c) => c.classList.add("reveal")));
}
window.addEventListener("DOMContentLoaded", attachCardObservers);
window.addEventListener("load", attachCardObservers);
document.body.addEventListener("htmx:afterSwap", (e) => {
    if (e.target && e.target.id === "grid") attachCardObservers();
});

/* ------------------ SEARCH SHORTCUT ------------------ */
document.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        const q = document.getElementById("q");
        if (q) { q.focus(); q.select(); }
    }
});

/* ------------------ MODAL ------------------ */
const modal = document.getElementById("modal");
function openModal() {
    modal.classList.remove("hidden");
    document.documentElement.style.overflow = "hidden";
}
function closeModal() {
    modal.classList.add("hidden");
    document.documentElement.style.overflow = "";
}
document.addEventListener("click", (e) => {
    if (e.target.closest(".pill, .pills, .meta-row a, .like")) return;
    const card = e.target.closest("[data-open-modal]");
    if (card) openModal();
    if (e.target.matches("[data-close-modal]")) closeModal();
});
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !modal.classList.contains("hidden")) closeModal();
});
document.body.addEventListener("htmx:afterSwap", (ev) => {
    if (ev.target.id === "modal-body") {
        const p = document.querySelector("#prompt-block");
        if (p) p.classList.add("collapsed");
        const card = document.querySelector(".modal-card");
        if (card) card.focus({ preventScroll: true });
    }
});
document.addEventListener("click", (e) => {
    const t = e.target.closest(".toggle");
    if (!t) return;
    const sel = t.getAttribute("data-toggle");
    const el = document.querySelector(sel);
    if (!el) return;
    const collapsed = el.classList.toggle("collapsed");
    t.textContent = collapsed
        ? t.getAttribute("data-collapsed-text") || "Show more"
        : t.getAttribute("data-expanded-text") || "Show less";
});

/* ------------------ IMAGE ZOOM IN MODAL ------------------ */
document.addEventListener("click", (e) => {
    const img = e.target.closest(".hero-img");
    if (!img) return;
    img.classList.toggle("zoomed");
});

/* ------------------ SHUFFLE (R key) ------------------ */
document.addEventListener("keydown", (e) => {
    if (e.key.toLowerCase() === "r" && document.activeElement.tagName !== "INPUT") {
        const target = "#grid";
        const q = `/?shuffle=1&_=${Date.now()}`;
        if (window.htmx) htmx.ajax("GET", url(q), target);
        else location.href = url(q);
    }
});

/* ------------------ ABOUT PILL ------------------ */
const aboutBtn = document.getElementById("aboutBtn");
const aboutModal = document.getElementById("aboutModal");
if (aboutBtn && aboutModal) {
    aboutBtn.addEventListener("click", () => {
        aboutModal.classList.remove("hidden");
        document.documentElement.style.overflow = "hidden";
    });
    aboutModal.addEventListener("click", (e) => {
        if (e.target.matches("[data-close-modal], .overlay")) {
            aboutModal.classList.add("hidden");
            document.documentElement.style.overflow = "";
        }
    });
}

/* ------------------ SEARCH: CLEAR (×) RESETS GRID ------------------ */
const searchBox = document.querySelector('input[type="search"]');
if (searchBox) {
    searchBox.addEventListener("search", () => {
        if (searchBox.value === "") {
            const target = "#grid";
            const q = `/?shuffle=1&_=${Date.now()}`;
            if (window.htmx) htmx.ajax("GET", url(q), target);
            else window.location.assign(url("/?shuffle=1"));
        }
    });
}

/* ------------------ BACK TO TOP ------------------ */
(function () {
    const btn = document.getElementById('toTop');
    if (!btn) return;
    btn.classList.add('show');

    function scrollAllToTop() {
        const roots = [document.scrollingElement || document.documentElement, document.body];
        const panels = Array.from(document.querySelectorAll('*')).filter(el => {
            if (el === btn) return false;
            const cs = getComputedStyle(el);
            const canScroll = /(auto|scroll|overlay)/.test(cs.overflowY);
            return canScroll && el.scrollHeight > el.clientHeight;
        });
        const targets = [...new Set([...roots, ...panels])];
        targets.forEach(el => {
            try { el.scrollTo({ top: 0, behavior: 'smooth' }); }
            catch { el.scrollTop = 0; }
        });
        if ('scrollTo' in window) window.scrollTo({ top: 0, behavior: 'smooth' });
        else window.scrollTo(0, 0);
    }

    btn.addEventListener('click', e => { e.preventDefault(); e.stopPropagation(); scrollAllToTop(); });
    document.addEventListener('click', e => {
        const t = e.target.closest('[data-scroll-top]'); if (!t) return;
        e.preventDefault(); scrollAllToTop();
    });

    const soften = () => { btn.style.opacity = (window.scrollY < 40) ? '0.9' : '1'; };
    soften();
    window.addEventListener('scroll', soften, { passive: true });
    window.addEventListener('resize', soften);
})();
