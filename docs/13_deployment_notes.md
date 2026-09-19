# Deployment Notes — Phase 4

## What's deployed live
- **API**: FastAPI service deployed to Render (free tier), Docker-based,
  at https://fraud-intelligence-platform.onrender.com
- **Database**: Postgres deployed to Render (free tier), holding the
  `alerts` table -- the only table the live API needs
- **Dashboard**: static HTML/CSS/JS, hosted on GitHub Pages, at
  https://lohith0703.github.io/fraud-intelligence-platform/

## Honest scoping decision
Kafka, the streaming producer/consumer, and Feast are NOT deployed to the
cloud -- running these 24/7 costs real money and isn't necessary for a
demo. These remain part of the local, Docker Compose-based development
environment and are demoed locally (e.g. in an interview setting).

The deployed system is: live API (model + SHAP + alerts) + live Postgres
+ live dashboard. This is described explicitly in the README rather than
implied to be the full pipeline running in production.

## Known limitation: free-tier cold starts
Render's free web service tier spins down after ~15 minutes of
inactivity. The first request after idling takes 30-60 seconds to
respond while the service wakes up. This is disclosed upfront rather
than presented as a bug if encountered during a demo.

## Verified end-to-end
Sent real scoring requests directly to the live API (not just locally),
confirmed correct model score, SHAP explanation, and alert creation
against the live Postgres database. Confirmed the live GitHub Pages
dashboard successfully connects to the live API and displays real,
correctly-created alerts -- not a local-only demo.
