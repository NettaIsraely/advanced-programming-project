# TLVFlow

A vehicle-sharing management system for Tel Aviv, built as a RESTful API.
Users can register, rent bikes, e-bikes and scooters from docking stations across the city, and return them to any station with available capacity.
The system handles the full ride lifecycle including payments, vehicle maintenance, degradation reporting, and persistent state across restarts.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Domain Model](#domain-model)
- [API Endpoints](#api-endpoints)
- [Vehicle Selection Logic](#vehicle-selection-logic)
- [Setup & Installation](#setup--installation)
- [Running the Server](#running-the-server)
- [Running Tests](#running-tests)
- [Data Files](#data-files)
- [Design Patterns & OOP Principles](#design-patterns--oop-principles)
- [State Persistence](#state-persistence)
- [Authors](#authors)

## Features

- **User management** — registration with hashed passwords (PBKDF2-SHA256), email uniqueness enforcement, and upgrade path from regular to Pro accounts.
- **Ride lifecycle** — start a ride from the nearest station with an eligible vehicle, end at the nearest station with capacity, automatic fee calculation and payment processing.
- **Three vehicle types** — Bikes, E-Bikes, and Scooters with type-specific maintenance treatments and rental eligibility rules.
- **1,000 stations / 18,754 vehicles** — loaded from CSV on cold start; linked to stations with capacity enforcement.
- **Pro users** — license-validated users who can rent all vehicle types (including electric); regular users are limited to non-electric bikes.
- **Payment processing** — mocked async payment service supporting charges, receipts, and refunds tied to a user's stored payment token.
- **Vehicle degradation** — mid-ride reporting of degraded vehicles; ride ends fee-free, vehicle moves to a degraded pool.
- **Maintenance pipeline** — batch treatment of eligible vehicles (10+ rides or degraded), with type-specific treatments (chain lubrication, battery inspection, firmware update, etc.).
- **Concurrency safety** — async locks per station and per user to prevent double-booking, station overflow, and duplicate ride starts.
- **State persistence** — full application state serialized to JSON on shutdown and restored on startup (atomic writes via temp file + rename).

## Tech Stack

| Component       | Technology            |
|-----------------|-----------------------|
| Language        | Python 3.12           |
| Web Framework   | FastAPI               |
| Server          | Uvicorn (ASGI)        |
| Validation      | Pydantic v2           |
| Testing         | pytest, httpx         |
| Linting         | Ruff                  |
| Type Checking   | mypy (strict mode)    |
| Build System    | setuptools            |

## Architecture

The project follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────┐
│          API Layer              │  FastAPI routers, Pydantic schemas,
│   (routes, schemas, routers)    │  request/response validation
├─────────────────────────────────┤
│        Service Layer            │  Business logic orchestration,
│   (rides, users, vehicles,      │  coordinates domain + persistence
│    stations, degraded)          │
├─────────────────────────────────┤
│        Domain Layer             │  Core entities, enums, business rules,
│   (vehicles, stations, rides,   │  validation, factory methods
│    users, payments, reports)    │
├─────────────────────────────────┤
│      Persistence Layer          │  In-memory repositories with
│   (repositories, state store,   │  snapshot/restore, CSV loaders,
│    loaders)                     │  Protocol-based interfaces
└─────────────────────────────────┘
```

## Project Structure

```
advanced-programming-project/
├── data/
│   ├── vehicles.csv              # 18,754 vehicles with type, status, station
│   ├── stations.csv              # 1,000 stations with coordinates and capacity
│   └── state.json                # Auto-generated application state snapshot
├── src/
│   └── tlvflow/
│       ├── api/
│       │   ├── app.py            # FastAPI app, lifespan (startup/shutdown)
│       │   ├── routes.py         # Top-level router aggregation
│       │   ├── schemas.py        # Pydantic request/response models
│       │   └── routers/
│       │       ├── health_router.py
│       │       ├── users_router.py
│       │       ├── vehicles_router.py
│       │       ├── rides_router.py
│       │       └── stations_router.py
│       ├── domain/
│       │   ├── enums.py          # VehicleStatus, RideStatus, PaymentKind, etc.
│       │   ├── vehicles.py       # Vehicle ABC, Bike, EBike, Scooter, VehicleFactory
│       │   ├── stations.py       # Station entity with dock/undock/checkout
│       │   ├── rides.py          # Ride entity with lifecycle management
│       │   ├── users.py          # User, ProUser with auth and permissions
│       │   ├── payment.py        # Payment record model
│       │   ├── payment_service.py# Mocked async payment processing
│       │   ├── reports.py        # VehicleReport with damage verification
│       │   ├── maintenance_event.py # Maintenance event tracking
│       │   └── exceptions.py     # Custom domain exceptions
│       ├── services/
│       │   ├── rides_service.py  # Ride start/end orchestration
│       │   ├── users_service.py  # Registration, upgrade, active users
│       │   ├── vehicles_service.py # Treatment and degradation handling
│       │   ├── stations_service.py # Nearest-station lookups
│       │   ├── link_vehicles.py  # Startup vehicle-to-station linking
│       │   └── degraded_vehicles_service.py # Degraded pool management
│       ├── persistence/
│       │   ├── in_memory.py      # VehicleRepository, StationRepository
│       │   ├── users_repository.py
│       │   ├── rides_repository.py
│       │   ├── payments_repository.py
│       │   ├── maintenance_repository.py
│       │   ├── active_users_repository.py
│       │   ├── degraded_vehicles_repository.py
│       │   ├── state_store.py    # JSON state persistence (atomic save)
│       │   └── loaders.py        # CSV parsing for vehicles and stations
│       ├── repositories/
│       │   └── interfaces.py     # Protocol-based repository abstractions
│       └── logging.py            # Centralized logging configuration
├── tests/
│   ├── unit/                     # Unit tests for domain, services, repositories
│   │   ├── modules/              # Domain entity tests
│   │   ├── services/             # Service layer tests
│   │   └── repositories/         # Repository tests
│   └── integration/              # Integration tests against the full API
├── pyproject.toml                # Build config, dependencies, tool settings
└── README.md
```

## Domain Model

### Entities

| Entity              | Description                                                                 |
|---------------------|-----------------------------------------------------------------------------|
| **Vehicle** (ABC)   | Abstract base with `Bike`, `EBike`, `Scooter` subclasses. Tracks status, ride count, station assignment, and maintenance eligibility. |
| **Station**         | Docking station with coordinates, capacity, and a managed list of docked vehicles. Supports dock/undock/checkout operations. |
| **Ride**            | Represents a single ride with start/end locations, timestamps, status, fee calculation, and associated user/vehicle. |
| **User**            | Regular user with hashed credentials, payment token, ride history. Limited to non-electric vehicles. |
| **ProUser**         | Extends User with a validated driver's license. Can rent all vehicle types. |
| **Payment**         | Immutable record for charges, receipts, or refunds linked to a ride.       |
| **VehicleReport**   | User-submitted damage report with mock AI verification.                    |
| **MaintenanceEvent**| Tracks a maintenance episode with treatments, timestamps, and status.      |

### Enums

| Enum              | Values                                                    |
|-------------------|-----------------------------------------------------------|
| `VehicleStatus`   | AVAILABLE, IN_USE, AWAITING_REPORT_REVIEW, DEGRADED       |
| `RideStatus`      | ACTIVE, COMPLETED, CANCELLED                              |
| `PaymentKind`     | CHARGE, RECEIPT, REFUND                                   |
| `ReportStatus`    | SUBMITTED, UNDER_REVIEW, VERIFIED, REJECTED               |
| `EventStatus`     | OPEN, IN_PROGRESS, CLOSED                                 |
| `TreatmentType`   | GENERAL_INSPECTION, CHAIN_LUBRICATION, BATTERY_INSPECTION, SCOOTER_FIRMWARE_UPDATE |

## API Endpoints

| Method | Path                       | Description                                              |
|--------|----------------------------|----------------------------------------------------------|
| GET    | `/health`                  | Health check — returns `{ "status": "ok" }`              |
| POST   | `/register`                | Register a new user (name, email, password, payment token) |
| POST   | `/user/upgrade`            | Upgrade a user to Pro with license details               |
| GET    | `/rides/active-users`      | List all users with an active ride                       |
| POST   | `/ride/start`              | Start a ride — finds nearest station, assigns vehicle    |
| POST   | `/ride/end`                | End a ride — docks vehicle, processes payment            |
| POST   | `/vehicle/treat`           | Batch-treat eligible and degraded vehicles               |
| POST   | `/vehicle/report-degraded` | Report a vehicle as degraded during an active ride       |
| GET    | `/stations/nearest`        | Find the nearest station to given coordinates            |

All request/response bodies are validated with Pydantic (`extra="forbid"` rejects unknown fields).

## Vehicle Selection Logic

When a ride starts, the system finds the nearest station (by Euclidean distance) that has an eligible vehicle. A vehicle is eligible if:

- `status == AVAILABLE`
- `rides_since_last_treated <= 10`
- The user is allowed to rent it (regular users: non-electric only; Pro users: all types)

When multiple eligible vehicles exist at a station, a **deterministic selection rule** applies:

1. Prefer **bike**, then **ebike**, then **scooter** (fixed type priority).
2. Within the same type, choose the vehicle with the **smallest `vehicle_id`** (lexicographic order).

## Setup & Installation

**Prerequisites:** Python 3.12+

```bash
# Clone the repository
git clone <repository-url>
cd advanced-programming-project

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate    # macOS/Linux

# Install the package with dev dependencies
pip install -e ".[dev]"
```

## Running the Server

```bash
uvicorn tlvflow.api.app:app --reload
```

The API will be available at `http://localhost:8000`. FastAPI auto-generates interactive documentation at:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

On first launch, the server loads vehicles and stations from CSV files in `data/`. On subsequent launches, it restores state from `data/state.json` if present.

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

The test suite includes **27 test files** organized into:

- **Unit tests** — domain entities, services, repositories, and loaders tested in isolation.
- **Integration tests** — full API tests using FastAPI's `TestClient` via httpx, covering health, users, vehicles, stations, and rides endpoints.

## Data Files

| File              | Records | Description                                                    |
|-------------------|---------|----------------------------------------------------------------|
| `vehicles.csv`    | 18,754  | Vehicle ID, station ID, type (scooter/electric_bicycle/bicycle), status, rides since last treated, last treated date |
| `stations.csv`    | 1,000   | Station ID, name, latitude, longitude, max capacity            |
| `state.json`      | —       | Auto-generated on shutdown; contains full serialized application state |

## Design Patterns & OOP Principles

| Pattern / Principle       | Where Applied                                                                 |
|---------------------------|-------------------------------------------------------------------------------|
| **Abstract Base Class**   | `Vehicle` ABC with `Bike`, `EBike`, `Scooter` concrete implementations        |
| **Factory**               | `VehicleFactory.create_vehicle()` with a type registry                        |
| **Inheritance**           | `ProUser` extends `User` with license validation and expanded permissions     |
| **Polymorphism**          | `can_rent()` differs between User (non-electric only) and ProUser (all types); `get_required_treatments()` differs per vehicle type; `is_electric` property differs per subclass |
| **Encapsulation**         | Protected (`_`) and private (`__`) attributes with read-only properties throughout all domain entities |
| **Protocol (Structural Typing)** | Repository interfaces defined as `Protocol` classes for loose coupling |
| **Repository Pattern**    | Each entity has a dedicated repository with consistent `add`/`get`/`snapshot`/`restore` interface |
| **Dependency Injection**  | Services receive repositories and external services as function parameters     |
| **Async Concurrency**     | `asyncio.Lock` per station and per user to prevent race conditions            |
| **Atomic Persistence**    | State saved via temp file + `os.rename` to prevent corruption                 |

## State Persistence

The application maintains full state across restarts:

**Shutdown:** all repositories serialize their state into a single JSON snapshot saved atomically to `data/state.json`.

**Startup:** if `state.json` exists, all repositories restore from it. Vehicles are re-linked to stations, and degraded vehicles are moved to the degraded pool. If no snapshot exists (cold start), data is loaded from the CSV files.

**Snapshot keys:** `vehicles`, `stations`, `users`, `active_users`, `rides`, `maintenance`, `payments`, `degraded_vehicles`.
