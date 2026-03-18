# TLVFlow

Vehicle management and ride-sharing API.

## Vehicle selection (start ride)

When multiple vehicle types are available at the nearest station (by Euclidean distance to the user’s `lon`/`lat`), the system uses a **deterministic selection rule**:

1. Prefer **bike**, then **ebike**, then **scooter** (fixed type order).
2. Within the same type, choose the vehicle with the **smallest `vehicle_id`** (lexicographic).

Only vehicles that are **eligible** are considered: `status == AVAILABLE` and `rides_since_last_treated <= 10`.
