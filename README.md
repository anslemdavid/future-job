# The Future Job

**A simpler way to find your next opportunity.**

The Future Job is a lightweight job-search website for people looking for work in Germany and Europe. Browse current employer-submitted vacancies, search by role, location, and work arrangement, compare searches on other job boards, and save interesting roles in your browser.

## What it does

- Displays live jobs from Arbeitnow's public Job Board API, including employer, location, tags, publication date, and a link to the original listing.
- Searches loaded listings by role, employer, description, tags, location, opportunity type, and schedule.
- Provides direct links to search the same keywords and location on the Federal Employment Agency, Indeed, XING, and Arbeitnow.
- Saves jobs in the current browser using local storage; there are no accounts or tracking profiles.
- Works on mobile and desktop, supports keyboard focus and reduced-motion preferences, and includes a small animated 3D-style visual.
- Includes a `/health` endpoint for hosting-platform health checks.

The API currently returns up to 300 recent jobs per page, primarily from European employers and applicant-tracking systems. The app caches a successful feed response for up to one hour to reduce unnecessary requests. Arbeitnow states that its listings are updated hourly; actual job availability is controlled by the original publisher. If the API is unavailable, the app reports the problem rather than showing made-up listings.

Arbeitnow requests that API users link back to its site. The app includes provider attribution and a direct link to Arbeitnow. Read the [API documentation](https://www.arbeitnow.com/blog/job-board-api) and [terms of service](https://www.arbeitnow.com/terms) before deploying or changing how its data is used. Indeed and XING are not scraped or republished; their links open each site's own search results.

## Run locally

Requires Python 3.10 or later.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000>.

## Tests

```powershell
python -m unittest discover -s tests
```

## Deploy on Render

1. Push the contents of this folder to a GitHub repository.
2. In Render, choose **New → Blueprint** and connect the repository containing `render.yaml`.
3. Create the web service. Render installs `requirements.txt` and launches the app with Gunicorn.
4. Open Render's generated `onrender.com` address and check `/health`.

The free Render plan may spin down after inactivity. The job feed is a live external service, so availability depends on Arbeitnow. When the feed is unavailable, the site reports the issue and serves the last successful cached listings when available.

## Project files

- `app.py` — Flask application and responsive website.
- `requirements.txt` — runtime dependencies.
- `render.yaml` — Render Blueprint configuration.
- `.gitignore` — keeps Python caches, virtual environments, and local secrets out of Git.

## Data and privacy

Search terms are applied to the public Arbeitnow feed in the app. Indeed, XING, and the Federal Employment Agency open separately and return their own results; this app does not scrape or combine their job listings. Saved job IDs stay in the user's browser local storage.
