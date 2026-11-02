# PC Flip Hunter — automatic polling prototype

Run with Python 3.10+:

```bash
pip install -r requirements.txt
python server.py
```

Open http://localhost:8765 . The backend checks public MyMarket category pages at most once every 15 minutes; the frontend requests cached data every minute. It does not bypass access restrictions, log in, or use private APIs. Stop if MyMarket disallows automated access. Respect robots.txt and the site's terms before deployment.

**Important:** Scraping has not been validated against the live site from this environment (outbound network DNS unavailable). The site's HTML may differ, so the parser may show zero results. The dashboard reports errors instead of inventing listings. No guaranteed profit: market price is unverified and ROI is not calculated for fetched listings. No background push notifications yet; running server is necessary.
