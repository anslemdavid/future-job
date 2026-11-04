import unittest
from unittest.mock import Mock, patch

import app


class FutureJobTests(unittest.TestCase):
    def setUp(self):
        app._job_cache = []
        app._cache_updated_at = 0.0
        app._cache_fetched_at = 0.0
        self.client = app.app.test_client()
        self.job = {
            "id": "software-engineer-berlin",
            "title": "Software Engineer",
            "employer": "Example GmbH",
            "place": "Berlin",
            "tags": ["Engineering", "Python"],
            "job_types": ["Full Time", "Permanent employment"],
            "description": "Build software for customers.",
            "remote": True,
            "posted": "2026-11-03",
            "url": "https://www.arbeitnow.com/jobs/companies/example/software-engineer-berlin",
        }

    def test_search_filters_by_keyword_location_type_and_schedule(self):
        self.assertTrue(app._matches_job(self.job, {
            "what": "software engineer", "where": "Berlin",
            "type": "permanent", "hours": "full-time",
        }))
        self.assertFalse(app._matches_job(self.job, {
            "what": "nurse", "where": "Berlin", "type": "", "hours": "",
        }))
        self.assertFalse(app._matches_job(self.job, {
            "what": "", "where": "Munich", "type": "", "hours": "",
        }))

    def test_search_paginates_matching_jobs(self):
        jobs = [dict(self.job, id=str(index)) for index in range(25)]
        with patch("app.fetch_jobs", return_value=(jobs, 1234.0, None)):
            results, total, _, warning = app.search(
                {"what": "", "where": "", "type": "", "hours": ""}, 2
            )
        self.assertEqual(total, 25)
        self.assertEqual(len(results), 5)
        self.assertEqual(results[0]["id"], "20")
        self.assertIsNone(warning)

    @patch("app.requests.get")
    def test_api_records_are_normalized_and_cached(self, get):
        response = Mock()
        response.json.return_value = {"data": [{
            "slug": "engineer-berlin",
            "title": "Engineer",
            "company_name": "Example GmbH",
            "location": "Berlin",
            "description": "<p>Build <b>great</b> software.</p>",
            "tags": ["Engineering"],
            "job_types": ["Full Time"],
            "remote": True,
            "created_at": 1793664000,
            "url": "https://www.arbeitnow.com/jobs/companies/example/engineer-berlin",
        }]}
        response.raise_for_status.return_value = None
        get.return_value = response

        jobs, _, warning = app.fetch_jobs()
        cached_jobs, _, cached_warning = app.fetch_jobs()

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["title"], "Engineer")
        self.assertEqual(jobs[0]["description"], "Build great software.")
        self.assertTrue(jobs[0]["remote"])
        self.assertEqual(cached_jobs, jobs)
        self.assertIsNone(warning)
        self.assertIsNone(cached_warning)
        get.assert_called_once_with(app.API, params={"page": 1}, timeout=15)

    @patch("app.requests.get")
    def test_failed_refresh_uses_cached_results_with_warning(self, get):
        app._job_cache = [self.job]
        app._cache_updated_at = 0.0
        app._cache_fetched_at = 1234.0
        get.side_effect = app.requests.ConnectionError()

        jobs, fetched_at, warning = app.fetch_jobs()

        self.assertEqual(jobs, [self.job])
        self.assertEqual(fetched_at, 1234.0)
        self.assertIn("last successful refresh", warning)

    @patch("app.fetch_jobs")
    def test_homepage_renders_jobs_and_job_board_search_links(self, fetch_jobs):
        fetch_jobs.return_value = ([self.job], 1234.0, None)
        response = self.client.get("/?what=software+engineer&where=Berlin")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"The Future Job", response.data)
        self.assertIn(b"Software Engineer", response.data)
        self.assertIn(b"Example GmbH", response.data)
        self.assertIn(b"arbeitnow.com/jobs/companies/example/software-engineer-berlin", response.data)
        self.assertIn(b"indeed.com/jobs?q=software", response.data)
        self.assertIn(b"xing.com/jobs/search?keywords=software", response.data)

    @patch("app.fetch_jobs")
    def test_homepage_reports_feed_failure_without_fake_jobs(self, fetch_jobs):
        fetch_jobs.side_effect = app.requests.ConnectionError()
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Live job listings are temporarily unavailable", response.data)
        self.assertNotIn(b"Software Engineer", response.data)
        self.assertIn(b"Indeed", response.data)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
