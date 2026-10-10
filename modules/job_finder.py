
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load the project's root .env file without displaying secrets.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=False)

ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs"


def search_adzuna_jobs(
    keywords="Python",
    location="India",
    results_per_page=10,
    page=1,
):
    """Search Adzuna India listings and return normalized job records."""

    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")

    if not app_id or not app_key:
        raise RuntimeError(
            "Adzuna credentials missing. Check ADZUNA_APP_ID "
            "and ADZUNA_APP_KEY in the project's .env file."
        )

    keywords = (keywords or "Python").strip()
    location = (location or "India").strip()

    results_per_page = max(1, min(int(results_per_page), 20))
    page = max(1, int(page))

    url = f"{ADZUNA_BASE_URL}/in/search/{page}"

    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": results_per_page,
        "what": keywords,
        "where": location,
        "content-type": "application/json",
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Could not retrieve Adzuna jobs: {exc}"
        ) from exc
    except ValueError as exc:
        raise RuntimeError(
            "Adzuna returned an invalid JSON response."
        ) from exc

    jobs = []
    seen_ids = set()

    for item in payload.get("results", []):
        job_id = str(item.get("id") or "").strip()
        apply_url = item.get("redirect_url") or ""

        # Deduplicate by job ID, falling back to the application URL.
        unique_key = job_id or apply_url
        if unique_key and unique_key in seen_ids:
            continue
        if unique_key:
            seen_ids.add(unique_key)

        salary_min = item.get("salary_min")
        salary_max = item.get("salary_max")

        if salary_min is not None and salary_max is not None:
            salary = f"{salary_min:,.0f} - {salary_max:,.0f}"
        elif salary_min is not None:
            salary = f"From {salary_min:,.0f}"
        elif salary_max is not None:
            salary = f"Up to {salary_max:,.0f}"
        else:
            salary = "Not disclosed"

        company = item.get("company") or {}
        location_data = item.get("location") or {}
        category = item.get("category") or {}

        jobs.append({
            "id": job_id,
            "title": item.get("title") or "Untitled role",
            "company": company.get("display_name") or "Not specified",
            "location": location_data.get("display_name") or location,
            "salary": salary,
            "description": item.get("description") or "",
            "apply_url": apply_url,
            "created": item.get("created") or "",
            "category": category.get("label") or "",
            "source": "Adzuna",
        })

    return {
        "total_results": payload.get("count", len(jobs)),
        "jobs": jobs,
    }
