from typing import Literal

from pydantic import BaseModel, ConfigDict, Field  # type: ignore[misc]

# extra="forbid":
# this is a crucial setting that tells Pydantic to reject any fields that are not explicitly defined in the model that are sent by postman, immediately getting a clean 422.
# This is important to ensure that your API is strict and only accepts the fields you expect, which helps catch errors early and maintain a clear contract for your API endpoints.


# Shared / small responses
class OkResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    result: Literal["ok"] = "ok"


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    detail: str


# Health
class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["ok"]


# Stations : matches stations_service.station_to_dict(...)
class StationNearestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    station_id: int
    name: str
    lat: float
    lon: float
    capacity: int
    available_slots: int
    is_full: bool
    is_empty: bool


# Users / Register: (adjust fields to your actual endpoint spec)


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # choose the fields your /register endpoint expects
    name: str
    email: str
    password: str
    payment_method_id: str | None = None


class RegisterResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str


# Rides: (based on your ticket screenshots: /ride/start, /ride/end)
class RideStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(min_length=1)
    station_id: str = Field(min_length=1)


class RideStartResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ride_id: str
    vehicle_id: str
    station_id: str


class RideEndRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(min_length=1)
    vehicle_id: str = Field(min_length=1)


class RideEndResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ride_id: str
    fee: float


# Vehicle report degraded
class ReportDegradedRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(min_length=1)
    vehicle_id: str = Field(min_length=1)
