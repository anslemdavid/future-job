"""The Future Job: live job search powered by the Arbeitnow Job Board API."""
import html
import os
import re
import threading
import time
from datetime import datetime, timezone
from urllib.parse import urlencode

import requests
from flask import Flask, render_template_string, request

app = Flask(__name__)

API = "https://www.arbeitnow.com/api/job-board-api"
PAGE_SIZE = 20
CACHE_SECONDS = 60 * 60
_cache_lock = threading.Lock()
_job_cache = []
_cache_updated_at = 0.0
_cache_fetched_at = 0.0

TYPES = {
    "": "All opportunities",
    "apprenticeship": "Apprenticeship",
    "internship": "Internship",
    "permanent": "Permanent role",
    "contract": "Contract",
    "freelance": "Freelance",
}
HOURS = {
    "": "Any schedule",
    "full-time": "Full-time",
    "part-time": "Part-time",
    "mini-job": "Mini-job",
    "remote": "Remote",
}
PAGE = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#f7f8f5">
<title>The Future Job — Find your next job in Germany</title>
<style>
:root{color-scheme:light;--ink:#17231f;--mute:#64736c;--line:#e4e9e3;--bg:#f7f8f5;--card:#fff;--soft:#eff3ed;--accent:#167a59;--accent-dark:#105c43;--lime:#d8f278;--shadow:0 18px 55px #203b2810}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;font:16px/1.55 "Segoe UI",system-ui,sans-serif;color:var(--ink);background:var(--bg)}
a{color:inherit}
.wrap{width:min(1120px,calc(100% - 40px));margin:auto}
nav{height:76px;display:flex;align-items:center;justify-content:space-between}
.brand{display:flex;align-items:center;white-space:nowrap;font-weight:800;letter-spacing:-.04em;font-size:1.2rem;text-decoration:none}
.brand-mark{display:inline-grid;flex:0 0 34px;place-items:center;width:34px;height:34px;margin-right:8px;border-radius:11px;background:var(--lime);color:var(--accent-dark)}
.nav-note{font-size:.88rem;color:var(--mute)}
.hero{position:relative;overflow:hidden;padding:62px 0 75px;background:radial-gradient(ellipse at 82% 45%,#e7f0dd 0,transparent 34%),linear-gradient(130deg,#f7f8f5,#f1f5ec)}
.hero-inner{position:relative;z-index:1;max-width:720px}
.eyebrow{display:inline-flex;align-items:center;gap:9px;color:var(--accent-dark);font-size:.82rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase}
.live-dot{width:8px;height:8px;border-radius:50%;background:#32a46f;box-shadow:0 0 0 4px #32a46f22}
h1{max-width:690px;margin:17px 0 13px;font-size:clamp(2.5rem,6vw,4.4rem);line-height:1.04;letter-spacing:-.065em}
.hero p{max-width:560px;margin:0;color:var(--mute);font-size:1.06rem}
.orb-scene{position:absolute;right:5%;top:50%;width:210px;height:210px;perspective:700px;transform:translateY(-50%)}
.orb{position:absolute;inset:12px;border-radius:50%;background:radial-gradient(circle at 30% 25%,#f6ffd4 0,#c9e977 21%,#75b979 54%,#31856d 78%,#246958 100%);box-shadow:inset -18px -20px 35px #174c3944,0 30px 60px #37795b30;transform-style:preserve-3d;animation:float 7s ease-in-out infinite}
.orb:before,.orb:after{position:absolute;content:"";border:1px solid #fff9;border-radius:50%;transform:rotateX(68deg) rotateZ(-24deg)}
.orb:before{inset:22px -18px}.orb:after{inset:44px -12px;transform:rotateX(68deg) rotateZ(38deg)}
@keyframes float{0%,100%{transform:translateY(0) rotateY(-12deg) rotateX(8deg)}50%{transform:translateY(-13px) rotateY(12deg) rotateX(-5deg)}}
.search-panel{position:relative;z-index:2;margin-top:-30px;padding:22px;background:var(--card);border:1px solid var(--line);border-radius:18px;box-shadow:var(--shadow)}
.search-grid{display:grid;grid-template-columns:1.5fr 1fr 1fr auto;gap:10px;align-items:end}
.field label{display:block;margin:0 0 6px 2px;font-size:.76rem;font-weight:700;color:var(--mute)}
input,select,button{width:100%;min-width:0;min-height:48px;padding:11px 12px;border:1px solid var(--line);border-radius:10px;background:#fff;color:var(--ink);font:inherit}
input::placeholder{color:#9aa69e}
button{cursor:pointer;font-weight:700}
.search-button{background:var(--accent);border-color:var(--accent);color:#fff;padding-inline:20px}
.search-button:hover{background:var(--accent-dark)}
:focus-visible{outline:3px solid #80ba66;outline-offset:3px}
.quick{display:flex;align-items:center;flex-wrap:wrap;gap:9px;margin:17px 2px 0;color:var(--mute);font-size:.82rem}
.quick a{padding:5px 11px;border:1px solid var(--line);border-radius:99px;background:#fff;text-decoration:none;color:var(--ink)}
.quick a:hover{border-color:var(--accent);color:var(--accent)}
main{padding:50px 0 72px}
.section-head{display:flex;justify-content:space-between;align-items:end;gap:18px;margin-bottom:16px}
.section-head h2{margin:0;font-size:1.65rem;letter-spacing:-.04em}
.section-head p{margin:5px 0 0;color:var(--mute);font-size:.9rem}
.feed-label{color:var(--accent);font-size:.83rem;font-weight:700}
.source-panel{margin:18px 0 0;padding:16px 18px;border:1px solid var(--line);border-radius:14px;background:#fff}
.source-heading{margin:0 0 10px;color:var(--mute);font-size:.82rem;font-weight:650}
.source-links{display:flex;flex-wrap:wrap;gap:9px}
.source-link{display:inline-flex;align-items:center;gap:7px;padding:8px 12px;border:1px solid var(--line);border-radius:9px;background:#fff;text-decoration:none;font-size:.86rem;font-weight:700}
.source-link:hover{border-color:var(--accent);color:var(--accent)}
.source-note{margin:10px 0 0;color:var(--mute);font-size:.76rem}
.results{overflow:hidden;border:1px solid var(--line);border-radius:16px;background:var(--card);box-shadow:var(--shadow)}
.job{display:grid;grid-template-columns:54px minmax(0,1fr) auto;align-items:center;gap:17px;padding:20px 22px;border-bottom:1px solid var(--line);transition:background .18s ease,transform .18s ease}
.job:last-child{border-bottom:0}
.job:hover{background:#fbfcfa}
.company-mark{display:grid;place-items:center;width:50px;height:50px;border-radius:15px;background:var(--soft);color:var(--accent-dark);font-size:1.05rem;font-weight:800}
.job h3{margin:0 0 4px;font-size:1.08rem;line-height:1.35;letter-spacing:-.02em}
.job-title{text-decoration:none}
.job-title:hover{color:var(--accent)}
.meta{display:flex;flex-wrap:wrap;gap:5px 13px;color:var(--mute);font-size:.88rem}
.job-tags{display:flex;flex-wrap:wrap;gap:6px;margin-top:9px}
.tag{padding:3px 9px;border-radius:99px;background:var(--soft);color:#43564a;font-size:.76rem}
.posted{color:var(--mute);font-size:.78rem;white-space:nowrap}
.save-job{width:auto;min-height:38px;padding:7px 11px;border-color:var(--line);background:#fff;font-size:.81rem}
.save-job[aria-pressed=true]{border-color:#b9dcae;background:#f1f8ed;color:var(--accent-dark)}
.empty,.err{padding:24px;color:var(--mute)}
.err{border:1px solid #f0dfc0;border-radius:13px;background:#fffaf0;color:#6b5429}
.pager{display:flex;justify-content:space-between;gap:12px;margin-top:20px}
.pager a{padding:10px 15px;border:1px solid var(--line);border-radius:10px;background:var(--card);text-decoration:none;font-weight:650}
.pager a:hover{border-color:var(--accent);color:var(--accent)}
footer{padding:22px 0;border-top:1px solid var(--line);color:var(--mute);font-size:.82rem}
@media(max-width:900px){.search-grid{grid-template-columns:repeat(3,minmax(0,1fr))}.search-button{grid-column:span 3}.orb-scene{right:1%;opacity:.65}}
@media(max-width:600px){.wrap{width:min(100% - 28px,1120px)}nav{height:64px}.brand{font-size:1.08rem}.nav-note{display:none}.hero{padding:45px 0 58px}.hero-inner{max-width:84%}.hero p{font-size:.96rem}.orb-scene{right:-90px;opacity:.34;width:180px;height:180px}.search-panel{padding:15px;border-radius:14px}.search-grid{grid-template-columns:1fr 1fr}.field:first-child,.search-button{grid-column:1/-1}.search-button{grid-column:1/-1}.quick{gap:7px}.section-head{align-items:start;flex-direction:column}.job{grid-template-columns:42px minmax(0,1fr);gap:12px;padding:16px}.company-mark{width:42px;height:42px;border-radius:13px}.job-actions{grid-column:2;display:flex;justify-content:space-between;align-items:center}.posted{white-space:normal}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important}}
</style></head><body>
<nav class="wrap" aria-label="Main navigation">
  <a class="brand" href="/"><span class="brand-mark" aria-hidden="true">F</span>The Future Job</a>
  <span class="nav-note">Fresh opportunities. A brighter next step.</span>
</nav>
<header class="hero">
  <div class="wrap hero-inner">
    <span class="eyebrow"><span class="live-dot" aria-hidden="true"></span>New opportunities, every day</span>
    <h1>Your future<br>starts with a job.</h1>
    <p>Explore fresh job opportunities from employers across Germany and Europe. Search by role, location, and schedule, then compare vacancies on leading job boards.</p>
  </div>
  <div class="orb-scene" aria-hidden="true"><div class="orb"></div></div>
</header>
<div class="wrap">
  <section class="search-panel" aria-label="Find a job">
    <form method="get" class="search-grid">
      <div class="field"><label for="what">What are you looking for?</label><input id="what" name="what" value="{{ q.what }}" placeholder="Job title, skill or keyword"></div>
      <div class="field"><label for="where">Where?</label><input id="where" name="where" value="{{ q.where }}" placeholder="City or postcode"></div>
      <div class="field"><label for="type">Opportunity</label><select id="type" name="type">{% for k,v in types.items() %}<option value="{{ k }}" {{ 'selected' if k==q.type }}>{{ v }}</option>{% endfor %}</select></div>
      <div class="field"><label for="hours">Working hours</label><select id="hours" name="hours">{% for k,v in hours.items() %}<option value="{{ k }}" {{ 'selected' if k==q.hours }}>{{ v }}</option>{% endfor %}</select></div>
      <button class="search-button" type="submit">Search jobs <span aria-hidden="true">→</span></button>
    </form>
    <div class="quick" aria-label="Popular searches">Popular:
      <a href="/?what=IT&amp;where={{ q.where|urlencode }}">IT</a>
      <a href="/?what=Logistik&amp;where={{ q.where|urlencode }}">Logistics</a>
      <a href="/?what=Pflege&amp;where={{ q.where|urlencode }}">Care</a>
      <a href="/?type=apprenticeship&amp;where={{ q.where|urlencode }}">Apprenticeships</a>
    </div>
  </section>
  <section class="source-panel" aria-label="Search other job boards">
    <p class="source-heading">Explore more jobs on</p>
    <div class="source-links">
      <a class="source-link" href="{{ source_urls.agency }}" target="_blank" rel="noopener noreferrer">Federal Employment Agency <span aria-hidden="true">↗</span></a>
      <a class="source-link" href="https://www.arbeitnow.com/" target="_blank" rel="noopener noreferrer">Arbeitnow <span aria-hidden="true">↗</span></a>
      <a class="source-link" href="{{ source_urls.indeed }}" target="_blank" rel="noopener noreferrer">Indeed <span aria-hidden="true">↗</span></a>
      <a class="source-link" href="{{ source_urls.xing }}" target="_blank" rel="noopener noreferrer">XING <span aria-hidden="true">↗</span></a>
    </div>
    <p class="source-note">Live listings are supplied by <a href="https://www.arbeitnow.com/blog/job-board-api" target="_blank" rel="noopener noreferrer">Arbeitnow’s public job API</a>. Other boards open separately; their listings are not copied or mixed in.</p>
  </section>
</div>
<main class="wrap" id="jobs">
{% if error %}
  <div class="err" role="alert"><strong>Live job listings are temporarily unavailable.</strong><br>{{ error }} You can still search the linked job boards above.</div>
{% else %}
  {% if warning %}<p class="feed-status warning" role="status">{{ warning }}</p>{% else %}<p class="feed-status">Live feed · Updated hourly by Arbeitnow{% if updated_at %} · Last checked {{ updated_at }} UTC{% endif %}</p>{% endif %}
  <div class="section-head">
    <div><h2>{% if q.what %}{{ q.what }} jobs{% else %}New opportunities{% endif %}</h2><p>{{ total }} live listings{% if q.where %} matching {{ q.where }}{% endif %} · Filtered from employer-submitted postings</p></div>
    <span class="feed-label"><span class="live-dot" aria-hidden="true"></span> &nbsp;Live jobs</span>
  </div>
  <div class="results" id="results" aria-live="polite">
  {% for j in results %}
    <article class="job" data-job-id="{{ j.id }}">
      <div class="company-mark" aria-hidden="true">{{ j.employer[:1]|upper if j.employer else 'J' }}</div>
      <div>
        <h3><a class="job-title" href="{{ j.url }}" target="_blank" rel="noopener noreferrer">{{ j.title }}</a></h3>
        <div class="meta"><span>{{ j.employer }}</span><span>{{ j.place }}</span></div>
        <div class="job-tags">{% for tag in j.tags[:3] %}<span class="tag">{{ tag }}</span>{% endfor %}<span class="tag source-tag">via Arbeitnow</span></div>
      </div>
      <div class="job-actions"><span class="posted">Posted {{ j.posted }}</span><button class="save-job" type="button" aria-pressed="false" aria-label="Save {{ j.title }}">☆ Save</button></div>
    </article>
  {% else %}
    <p class="empty">No jobs found for these filters. Try another keyword, job type, or a wider search radius.</p>
  {% endfor %}
  </div>
  <div class="pager">
    {% if page > 1 %}<a href="{{ prev_url }}#jobs">← Previous</a>{% else %}<span></span>{% endif %}
    {% if has_next %}<a href="{{ next_url }}#jobs">More jobs →</a>{% endif %}
  </div>
{% endif %}
</main>
<footer><div class="wrap">The Future Job · Listings provided by <a href="https://www.arbeitnow.com/" target="_blank" rel="noopener noreferrer">Arbeitnow</a>. Confirm the details and apply on the original job posting.</div></footer>
<script>
(() => {
  const storageKey = "jobsuche-saved-jobs";
  const buttons = [...document.querySelectorAll(".save-job")];
  let saved = new Set();
  let storageAvailable = true;
  try {
    saved = new Set(JSON.parse(localStorage.getItem(storageKey) || "[]"));
  } catch {
    storageAvailable = false;
  }
  buttons.forEach(button => {
    const id = button.closest(".job").dataset.jobId;
    if (!storageAvailable) {
      button.disabled = true;
      button.title = "Saving jobs is unavailable in this browser session.";
      return;
    }
    const update = () => {
      const isSaved = saved.has(id);
      button.setAttribute("aria-pressed", String(isSaved));
      button.textContent = isSaved ? "★ Saved" : "☆ Save";
    };
    update();
    button.addEventListener("click", () => {
      if (saved.has(id)) saved.delete(id);
      else saved.add(id);
      try {
        localStorage.setItem(storageKey, JSON.stringify([...saved]));
        update();
      } catch {
        button.disabled = true;
        button.title = "Your browser could not save this job. Check your storage settings.";
      }
    });
  });
})();
</script>
</body></html>"""


def fetch_jobs():
    global _job_cache, _cache_updated_at, _cache_fetched_at
    with _cache_lock:
        now = time.monotonic()
        if _cache_fetched_at and now - _cache_updated_at < CACHE_SECONDS:
            return _job_cache, _cache_fetched_at, None
        try:
            response = requests.get(API, params={"page": 1}, timeout=15)
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError):
            if _cache_fetched_at:
                return _job_cache, _cache_fetched_at, "The live feed is temporarily unavailable; showing the last successful refresh."
            raise

        records = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(records, list):
            if _cache_fetched_at:
                return _job_cache, _cache_fetched_at, "The live feed returned unexpected data; showing the last successful refresh."
            raise ValueError("The job feed returned an unexpected response.")

        jobs = []
        for record in records:
            if not isinstance(record, dict):
                continue
            slug = str(record.get("slug") or "").strip()
            title = str(record.get("title") or "").strip()
            if not slug or not title:
                continue
            target = str(record.get("url") or "")
            if not target.startswith("https://www.arbeitnow.com/jobs/"):
                target = "https://www.arbeitnow.com/"
            created_at = record.get("created_at")
            try:
                posted = datetime.fromtimestamp(int(created_at), timezone.utc).strftime("%Y-%m-%d")
            except (TypeError, ValueError, OSError, OverflowError):
                posted = "Date unavailable"
            tags = record.get("tags")
            job_types = record.get("job_types")
            description = " ".join(
                html.unescape(re.sub(r"<[^>]*>", " ", str(record.get("description") or ""))).split()
            )
            jobs.append({
                "id": slug,
                "title": title,
                "employer": str(record.get("company_name") or "Employer not listed").strip(),
                "place": str(record.get("location") or "Location not listed").strip(),
                "tags": [str(tag) for tag in tags if isinstance(tag, str)] if isinstance(tags, list) else [],
                "job_types": [str(kind) for kind in job_types if isinstance(kind, str)] if isinstance(job_types, list) else [],
                "description": description,
                "remote": bool(record.get("remote")),
                "posted": posted,
                "url": target,
            })

        _job_cache = jobs
        _cache_updated_at = time.monotonic()
        _cache_fetched_at = time.time()
        return _job_cache, _cache_fetched_at, None


def _contains_all_terms(value, query):
    normalized = value.casefold()
    return all(term in normalized for term in query.casefold().split())


def _matches_job(job, q):
    searchable = " ".join(
        [job["title"], job["employer"], job["place"], job["description"]]
        + job["tags"] + job["job_types"]
    )
    if q["what"] and not _contains_all_terms(searchable, q["what"]):
        return False
    if q["where"] and not _contains_all_terms(job["place"], q["where"]):
        return False

    job_details = " ".join(job["job_types"] + job["tags"] + [job["title"]]).casefold()
    type_terms = {
        "apprenticeship": ("apprentice", "ausbildung", "trainee", "dual study"),
        "internship": ("intern", "praktikum", "stage"),
        "permanent": ("permanent", "full time", "full-time", "fulltime", "unbefristet", "cdi"),
        "contract": ("contract", "fixed term", "freelance"),
        "freelance": ("freelance", "self-employed", "contractor"),
    }
    if q["type"] and not any(term in job_details for term in type_terms.get(q["type"], ())):
        return False

    schedule_terms = {
        "full-time": ("full time", "full-time", "fulltime"),
        "part-time": ("part time", "part-time", "parttime", "teilzeit"),
        "mini-job": ("mini-job", "minijob", "geringfügig"),
    }
    if q["hours"] == "remote" and not job["remote"]:
        return False
    if q["hours"] in schedule_terms and not any(
        term in job_details for term in schedule_terms[q["hours"]]
    ):
        return False
    return True


def search(q, page):
    jobs, updated_at, warning = fetch_jobs()
    matches = [job for job in jobs if _matches_job(job, q)]
    start = (page - 1) * PAGE_SIZE
    return matches[start:start + PAGE_SIZE], len(matches), updated_at, warning


def source_urls(q):
    terms = q["what"]
    location = q["where"]
    return {
        "agency": "https://www.arbeitsagentur.de/jobsuche/suche?" + urlencode({
            key: value for key, value in (("was", terms), ("wo", location), ("suchbereich", "jobs"))
            if value
        }),
        "indeed": "https://de.indeed.com/jobs" + ("?" + urlencode({
            key: value for key, value in (("q", terms), ("l", location)) if value
        }) if terms or location else ""),
        "xing": "https://www.xing.com/jobs/search" + ("?" + urlencode({
            key: value for key, value in (("keywords", terms), ("location", location)) if value
        }) if terms or location else ""),
    }


@app.route("/")
def index():
    q = {
        "what": request.args.get("what", "").strip(),
        "where": request.args.get("where", "").strip(),
        "type": request.args.get("type", "") if request.args.get("type", "") in TYPES else "",
        "hours": request.args.get("hours", "") if request.args.get("hours", "") in HOURS else "",
    }
    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1
    results, total, error, warning, updated_at = [], 0, None, None, None
    try:
        results, total, updated, warning = search(q, page)
        updated_at = datetime.fromtimestamp(updated, timezone.utc).strftime("%Y-%m-%d %H:%M")
    except (requests.RequestException, ValueError) as e:
        details = (
            f"HTTP {e.response.status_code}"
            if isinstance(e, requests.HTTPError) and e.response is not None
            else e.__class__.__name__
        )
        error = f"Could not load the live Arbeitnow feed. Check your connection and try again. ({details})"
    base = request.args.to_dict()
    prev_url = "?" + urlencode({**base, "page": page - 1})
    next_url = "?" + urlencode({**base, "page": page + 1})
    return render_template_string(
        PAGE, q=q, types=TYPES, hours=HOURS, results=results, total=total,
        error=error, page=page, has_next=page * PAGE_SIZE < total, prev_url=prev_url, next_url=next_url,
        source_urls=source_urls(q), warning=warning, updated_at=updated_at)


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))