"""Opti-Search — in-process search service mounted on the backend gateway.

Indexes three doc types from Redis pub/sub channels into Meilisearch:
- `decision`        — non-HOLD recommendations from `ai.recommendation`
- `crisis`          — rising-edge crisis_flags from `factory.telemetry`
- `safety_rollback` — events from `ai.safety_rollback`

See `C:\\Users\\ahmed\\.claude\\plans\\upgrade-ai-layer-jiggly-pinwheel.md`.
"""
