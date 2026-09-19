# CI/CD Notes — Phase 4

## What we built
A GitHub Actions workflow (.github/workflows/ci.yml) that runs automatically
on every push to main:
1. `test` job: installs dependencies, spins up a real ephemeral Postgres
   container, creates the alerts schema, and runs the pytest suite against
   a genuine database -- not a mock.
2. `docker-build` job: only runs if `test` passes (`needs: test`), and
   verifies the API's Dockerfile actually builds successfully.

## Bug found and fixed: tests initially failed in CI
First CI run failed with `psycopg2.OperationalError: connection to server
at "localhost" ... port 5433 failed: Connection refused`. Root cause: the
initial workflow only installed Python dependencies, but never started a
database -- so a test that writes a real alert (via the real /score
endpoint) had nothing to connect to on GitHub's fresh runner.

Considered two fixes: (1) make the test avoid touching the database
entirely, or (2) add a real, ephemeral Postgres service to the CI job
itself so the test exercises the genuine code path. Chose (2), since it
tests the real behavior rather than working around it -- GitHub Actions
supports "service containers" specifically for this pattern.

## Why this matters
This is genuine, automatic verification that the code works from a clean
environment, independent of the developer's own machine -- directly
addressing the classic "works on my machine" problem. Every future push
is automatically checked before being trusted.
