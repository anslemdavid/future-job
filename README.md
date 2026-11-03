# The Future Job

**A simpler way to find your next opportunity.**

The Future Job is a lightweight job-search website for people looking for work in Germany. Search current vacancies from the Federal Employment Agency, compare the same search on Indeed or XING, and save interesting opportunities in your browser.

## What it does

- Searches the Federal Employment Agency's live job-search feed by keyword, location, distance, job type, and working hours.
- Shows the employer, location, profession, start date, and publication date supplied with each listing.
- Provides direct links to search the same keywords and location on Indeed and XING.
- Saves jobs in the current browser using local storage; there are no accounts or tracking profiles.
- Works on mobile and desktop, supports keyboard focus and reduced-motion preferences, and includes a small animated 3D-style visual.
- Includes a `/health` endpoint for hosting-platform health checks.

Listings refresh when someone searches; this project does not fabricate vacancies or claim to merge results from different providers. Application details and availability are managed by the site that published each job. If the official feed cannot be reached, the app clearly reports that and keeps links to the other job boards available.

## Run locally

Requires Python 3.10 or later.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000>.

## Deploy on Render

1. Push the contents of this folder to a GitHub repository.
2. In Render, choose **New → Blueprint** and connect the repository containing `render.yaml`.
3. Create the web service. Render installs `requirements.txt` and launches the app with Gunicorn.
4. Open Render's generated `onrender.com` address and check `/health`.

The free Render plan may spin down after inactivity. The jobs feed is a live external service, so availability and the freshness of listings depend on the Federal Employment Agency. When the feed is unavailable, the website reports the problem rather than showing made-up jobs.

## Project files

- `app.py` — Flask application and responsive website.
- `requirements.txt` — runtime dependencies.
- `render.yaml` — Render Blueprint configuration.
- `.gitignore` — keeps Python caches, virtual environments, and local secrets out of Git.

## Data and privacy

Searches are sent to the Federal Employment Agency's public job-search service. Indeed and XING open separately and return their own results; this app does not scrape or combine their job listings. Saved job IDs stay in the user's browser local storage.
