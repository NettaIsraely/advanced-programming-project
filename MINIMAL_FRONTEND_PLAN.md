# Minimal TLVFlow Frontend — Plan (updated)

## Overview

Add a minimal single-page UI to the existing React + Vite frontend that calls the TLVFlow FastAPI backend for health, register, nearest station, start/end ride, and active users—with CORS enabled on the backend and no new frontend dependencies.

---

## Current state

- **Backend**: FastAPI app in `src/tlvflow/api/app.py` with no CORS and no static file serving. Key endpoints (no prefix):
  - `GET /health` — health check
  - `POST /register` — register user (name, email, password, optional payment_method_id)
  - `GET /stations/nearest?lon=&lat=` — nearest station
  - `POST /rides/start` — body: `user_id`, `station_id`
  - `POST /rides/end` — body: `user_id`, `vehicle_id`, `station_id`
  - `GET /rides/active-users` — list users with active rides
- **Frontend**: React 18 + Vite + TypeScript in `frontend/` with a single card (“TLVFlow”, “Vehicle management”), existing `frontend/src/index.css` with `.card`, `.btn`, etc. No API calls or routing.

---

## Decisions / clarifications

1. **Register form — `payment_method_id`**
   - Backend: schema has `payment_method_id: str | None = None`; router uses `body.payment_method_id or ""`. Backend does **not** distinguish missing vs `""`.
   - **Decision:** When the field is left blank, **omit** the field from the JSON body entirely (do not send `payment_method_id`). Only include it when the user enters a value.

2. **Nearest station — lat/lon inputs**
   - Use `type="number"` with `step="any"` so the browser blocks non-numeric input.
   - Add `min`/`max`: lon `-180`–`180`, lat `-90`–`90` to match backend `Query(..., ge=..., le=...)`.
   - Optional: brief client-side message if value is out of range before submit; not required for “very simplistic.”

3. **Result/error state**
   - **Decision:** **Per-section** state only. Each section (Health, Register, Nearest station, Start ride, End ride, Active users) keeps its own result and error state so that e.g. checking health does not wipe the last ride result.

4. **Passing data between sections**
   - **Copy to clipboard:** Add a small “Copy” (or copy icon) next to any ID in result blocks (`user_id`, `ride_id`, `vehicle_id`, `station_id`).
   - **Current user:** After a successful Register (or any response that includes `user_id`), provide a “Use as current user” (or “Use for rides”) action that sets a shared `currentUserId`. Prefill the `user_id` field in Start ride and End ride from `currentUserId`; user can still edit. No need to persist across page reloads for this minimal UI.

5. **Error display**
   - Backend often returns `detail` as a **string**; for 422 validation errors FastAPI returns `detail` as an **array** of objects like `{ "loc": ["body", "email"], "msg": "Field required" }`.
   - **Decision:** Normalize in the frontend:
     - If `detail` is a string → show it as-is.
     - If `detail` is an array → show each `msg` (optionally with `loc` for which field), e.g. as a short bullet list. No heavy formatting.

6. **CORS**
   - Allow only the origins actually used: `http://localhost:5173` and `http://127.0.0.1:5173`. Do **not** add port 3000 unless the frontend is run on 3000. Do **not** use wildcard `*` for local dev; keep explicit origins.

---

## Implementation

### 1. Backend: enable CORS

In `src/tlvflow/api/app.py`, add `CORSMiddleware` with:
- `allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"]`
- Allow common methods and headers as needed for the frontend (e.g. GET, POST, headers for JSON).

### 2. Frontend: API base URL

- Add config for API base URL, e.g. `VITE_API_URL` in a small `frontend/src/api.ts` (or inline), default `http://localhost:8000`.
- Use `fetch` with that base for all requests.

### 3. Frontend: minimal UI sections

Expand `frontend/src/App.tsx` (or a few components in the same folder) with:

| Section            | Action                | Inputs / behavior                    | Output / display                    |
|--------------------|-----------------------|-------------------------------------|-------------------------------------|
| Health             | Button “Check health” | None                                | Status (e.g. “ok”) or error         |
| Register           | Form submit           | name, email, password; optional payment_method_id (omit if blank) | user_id + “Copy” + “Use as current user” or error |
| Nearest station    | Form submit           | lat, lon — `type="number"` `step="any"` `min`/`max` | Station info or error               |
| Start ride         | Form submit           | user_id (prefill from current user), station_id | ride_id, vehicle_id, station_id + Copy or error |
| End ride           | Form submit           | user_id (prefill), vehicle_id, station_id | ride_id, fee + Copy or error        |
| Active users       | Button “Refresh”      | None                                | List of users or error              |

- Per-section state for result and error.
- Shared `currentUserId` for prefill in Start/End ride.
- Error display: normalize `detail` (string vs array) as above.
- Reuse existing CSS (`.card`, `.btn`, `.divider`); add minimal new classes only if needed.

### 4. Running the stack

- **Backend:** `uvicorn tlvflow.api.app:app --reload` (default 8000). Ensure `data/vehicles.csv` and `data/stations.csv` exist.
- **Frontend:** `cd frontend && npm run dev` (Vite 5173). Set `VITE_API_URL=http://localhost:8000` in `.env` if different.

No new dependencies, no routing. Optional later: User upgrade, Report degraded, Treat vehicles as extra sections.
