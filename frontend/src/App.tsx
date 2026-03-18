import { useState } from "react";
import { apiUrl } from "./api";

function formatErrorDetail(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item: { msg?: string; loc?: unknown[] }) => {
        const msg = item?.msg ?? "Validation error";
        const loc = Array.isArray(item?.loc) ? item.loc.join(" ") : "";
        return loc ? `${loc}: ${msg}` : msg;
      })
      .join("\n");
  }
  return String(detail);
}

function CopyButton({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(value).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };
  return (
    <button type="button" className="btn btn-copy" onClick={copy}>
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

function App() {
  const [currentUserId, setCurrentUserId] = useState("");

  const [healthResult, setHealthResult] = useState<string | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);

  const [registerName, setRegisterName] = useState("");
  const [registerEmail, setRegisterEmail] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");
  const [registerPaymentMethodId, setRegisterPaymentMethodId] = useState("");
  const [registerResult, setRegisterResult] = useState<{ user_id: string } | null>(null);
  const [registerError, setRegisterError] = useState<string | null>(null);

  const [nearestLat, setNearestLat] = useState("");
  const [nearestLon, setNearestLon] = useState("");
  const [nearestResult, setNearestResult] = useState<{
    station_id: number;
    name: string;
    lat: number;
    lon: number;
    capacity: number;
    available_slots: number;
    is_full: boolean;
    is_empty: boolean;
  } | null>(null);
  const [nearestError, setNearestError] = useState<string | null>(null);

  const [startUserId, setStartUserId] = useState("");
  const [startStationId, setStartStationId] = useState("");
  const [startResult, setStartResult] = useState<{
    ride_id: string;
    vehicle_id: string;
    station_id: string;
  } | null>(null);
  const [startError, setStartError] = useState<string | null>(null);

  const [endUserId, setEndUserId] = useState("");
  const [endVehicleId, setEndVehicleId] = useState("");
  const [endStationId, setEndStationId] = useState("");
  const [endResult, setEndResult] = useState<{ ride_id: string; fee: number } | null>(null);
  const [endError, setEndError] = useState<string | null>(null);

  const [activeUsersResult, setActiveUsersResult] = useState<{ users: unknown[] } | null>(null);
  const [activeUsersError, setActiveUsersError] = useState<string | null>(null);

  const checkHealth = async () => {
    setHealthError(null);
    setHealthResult(null);
    try {
      const res = await fetch(apiUrl("/health"));
      const data = await res.json();
      if (!res.ok) throw new Error(formatErrorDetail(data.detail ?? data));
      setHealthResult(data.status ?? "ok");
    } catch (e) {
      setHealthError(e instanceof Error ? e.message : String(e));
    }
  };

  const register = async (e: React.FormEvent) => {
    e.preventDefault();
    setRegisterError(null);
    setRegisterResult(null);
    const body: { name: string; email: string; password: string; payment_method_id?: string } = {
      name: registerName,
      email: registerEmail,
      password: registerPassword,
    };
    if (registerPaymentMethodId.trim() !== "") body.payment_method_id = registerPaymentMethodId.trim();
    try {
      const res = await fetch(apiUrl("/register"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(formatErrorDetail(data.detail ?? data));
      setRegisterResult(data);
    } catch (e) {
      setRegisterError(e instanceof Error ? e.message : String(e));
    }
  };

  const useAsCurrentUser = (userId: string) => {
    setCurrentUserId(userId);
    setStartUserId(userId);
    setEndUserId(userId);
  };

  const findNearest = async (e: React.FormEvent) => {
    e.preventDefault();
    setNearestError(null);
    setNearestResult(null);
    const lat = Number(nearestLat);
    const lon = Number(nearestLon);
    if (Number.isNaN(lat) || Number.isNaN(lon)) {
      setNearestError("Lat and lon must be numbers");
      return;
    }
    try {
      const res = await fetch(apiUrl(`/stations/nearest?lat=${lat}&lon=${lon}`));
      const data = await res.json();
      if (!res.ok) throw new Error(formatErrorDetail(data.detail ?? data));
      setNearestResult(data);
    } catch (e) {
      setNearestError(e instanceof Error ? e.message : String(e));
    }
  };

  const startRide = async (e: React.FormEvent) => {
    e.preventDefault();
    setStartError(null);
    setStartResult(null);
    const stationId = Number(startStationId);
    if (Number.isNaN(stationId) || stationId < 1) {
      setStartError("Station ID must be a positive number");
      return;
    }
    try {
      const res = await fetch(apiUrl("/rides/start"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: startUserId, station_id: stationId }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(formatErrorDetail(data.detail ?? data));
      setStartResult(data);
    } catch (e) {
      setStartError(e instanceof Error ? e.message : String(e));
    }
  };

  const endRide = async (e: React.FormEvent) => {
    e.preventDefault();
    setEndError(null);
    setEndResult(null);
    const stationId = Number(endStationId);
    if (Number.isNaN(stationId) || stationId < 1) {
      setEndError("Station ID must be a positive number");
      return;
    }
    try {
      const res = await fetch(apiUrl("/rides/end"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: endUserId,
          vehicle_id: endVehicleId,
          station_id: stationId,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(formatErrorDetail(data.detail ?? data));
      setEndResult(data);
    } catch (e) {
      setEndError(e instanceof Error ? e.message : String(e));
    }
  };

  const fetchActiveUsers = async () => {
    setActiveUsersError(null);
    setActiveUsersResult(null);
    try {
      const res = await fetch(apiUrl("/rides/active-users"));
      const data = await res.json();
      if (!res.ok) throw new Error(formatErrorDetail(data.detail ?? data));
      setActiveUsersResult(data);
    } catch (e) {
      setActiveUsersError(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <main className="app">
      <div className="card app-card">
        <h1 className="app-title">TLVFlow</h1>
        <p className="app-tagline">Vehicle management</p>
      </div>

      {currentUserId && (
        <div className="card section-card">
          <p className="section-note">Current user for rides: {currentUserId}</p>
        </div>
      )}

      <div className="card section-card">
        <h2 className="section-title">Health</h2>
        <button type="button" className="btn" onClick={checkHealth}>
          Check health
        </button>
        {healthError && <p className="result-error">{healthError}</p>}
        {healthResult && <p className="result-ok">{healthResult}</p>}
      </div>

      <div className="card section-card">
        <h2 className="section-title">Register</h2>
        <form onSubmit={register} className="form">
          <label className="form-row">
            <span>Name</span>
            <input
              type="text"
              value={registerName}
              onChange={(e) => setRegisterName(e.target.value)}
              required
            />
          </label>
          <label className="form-row">
            <span>Email</span>
            <input
              type="email"
              value={registerEmail}
              onChange={(e) => setRegisterEmail(e.target.value)}
              required
            />
          </label>
          <label className="form-row">
            <span>Password</span>
            <input
              type="password"
              value={registerPassword}
              onChange={(e) => setRegisterPassword(e.target.value)}
              required
            />
          </label>
          <label className="form-row">
            <span>Payment method ID (optional)</span>
            <input
              type="text"
              value={registerPaymentMethodId}
              onChange={(e) => setRegisterPaymentMethodId(e.target.value)}
            />
          </label>
          <button type="submit" className="btn">
            Register
          </button>
        </form>
        {registerError && <p className="result-error">{registerError}</p>}
        {registerResult && (
          <div className="result-block">
            <p className="result-ok">user_id: {registerResult.user_id}</p>
            <div className="result-actions">
              <CopyButton value={registerResult.user_id} />
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => useAsCurrentUser(registerResult.user_id)}
              >
                Use as current user
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="card section-card">
        <h2 className="section-title">Nearest station</h2>
        <form onSubmit={findNearest} className="form">
          <label className="form-row">
            <span>Latitude</span>
            <input
              type="number"
              step="any"
              min={-90}
              max={90}
              value={nearestLat}
              onChange={(e) => setNearestLat(e.target.value)}
              required
            />
          </label>
          <label className="form-row">
            <span>Longitude</span>
            <input
              type="number"
              step="any"
              min={-180}
              max={180}
              value={nearestLon}
              onChange={(e) => setNearestLon(e.target.value)}
              required
            />
          </label>
          <button type="submit" className="btn">
            Find nearest
          </button>
        </form>
        {nearestError && <p className="result-error">{nearestError}</p>}
        {nearestResult && (
          <div className="result-block">
            <p>Station: {nearestResult.name} (id: {nearestResult.station_id})</p>
            <p>Lat: {nearestResult.lat}, Lon: {nearestResult.lon}</p>
            <p>Capacity: {nearestResult.capacity}, Available: {nearestResult.available_slots}</p>
            <p>{nearestResult.is_full ? "Full" : nearestResult.is_empty ? "Empty" : "Has slots"}</p>
            <CopyButton value={String(nearestResult.station_id)} />
          </div>
        )}
      </div>

      <div className="card section-card">
        <h2 className="section-title">Start ride</h2>
        <form onSubmit={startRide} className="form">
          <label className="form-row">
            <span>User ID</span>
            <input
              type="text"
              value={startUserId}
              onChange={(e) => setStartUserId(e.target.value)}
              placeholder={currentUserId || undefined}
              required
            />
          </label>
          <label className="form-row">
            <span>Station ID</span>
            <input
              type="number"
              min={1}
              value={startStationId}
              onChange={(e) => setStartStationId(e.target.value)}
              required
            />
          </label>
          <button type="submit" className="btn">
            Start ride
          </button>
        </form>
        {startError && <p className="result-error">{startError}</p>}
        {startResult && (
          <div className="result-block">
            <p className="result-ok">ride_id: {startResult.ride_id}</p>
            <p>vehicle_id: {startResult.vehicle_id}</p>
            <p>station_id: {startResult.station_id}</p>
            <div className="result-actions">
              <CopyButton value={startResult.ride_id} />
              <CopyButton value={startResult.vehicle_id} />
            </div>
          </div>
        )}
      </div>

      <div className="card section-card">
        <h2 className="section-title">End ride</h2>
        <form onSubmit={endRide} className="form">
          <label className="form-row">
            <span>User ID</span>
            <input
              type="text"
              value={endUserId}
              onChange={(e) => setEndUserId(e.target.value)}
              placeholder={currentUserId || undefined}
              required
            />
          </label>
          <label className="form-row">
            <span>Vehicle ID</span>
            <input
              type="text"
              value={endVehicleId}
              onChange={(e) => setEndVehicleId(e.target.value)}
              required
            />
          </label>
          <label className="form-row">
            <span>Station ID</span>
            <input
              type="number"
              min={1}
              value={endStationId}
              onChange={(e) => setEndStationId(e.target.value)}
              required
            />
          </label>
          <button type="submit" className="btn">
            End ride
          </button>
        </form>
        {endError && <p className="result-error">{endError}</p>}
        {endResult && (
          <div className="result-block">
            <p className="result-ok">ride_id: {endResult.ride_id}, fee: {endResult.fee}</p>
            <CopyButton value={endResult.ride_id} />
          </div>
        )}
      </div>

      <div className="card section-card">
        <h2 className="section-title">Active users</h2>
        <button type="button" className="btn" onClick={fetchActiveUsers}>
          Refresh
        </button>
        {activeUsersError && <p className="result-error">{activeUsersError}</p>}
        {activeUsersResult && (
          <div className="result-block">
            <pre className="result-json">
              {JSON.stringify(activeUsersResult.users, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </main>
  );
}

export default App;
