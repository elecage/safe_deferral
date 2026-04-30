"""Simulation State Store — shared live environment and device state for virtual nodes.

All environmental sensor virtual nodes and device state virtual nodes write
their values here when they publish.  Context (trigger) virtual nodes read from
this store at publish time so the assembled context payload reflects the current
simulated world state rather than a static baked-in template.

Authority boundary:
  - This is simulation-layer state only.
  - It is not policy authority, validator authority, or actuation authority.
  - Values here do not override canonical policy assets or physical node readings.
"""

import threading
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Default environment matching context_schema.json environmental_context
# ---------------------------------------------------------------------------
_DEFAULT_ENV: dict = {
    "temperature": 22.5,
    "illuminance": 30.0,
    "occupancy_detected": True,
    "smoke_detected": False,
    "gas_detected": False,
    "doorbell_detected": False,
}

# Default device states matching context_schema.json device_states
_DEFAULT_DEVICES: dict = {
    "living_room_light": "off",
    "bedroom_light": "off",
    "living_room_blind": "closed",
    "tv_main": "standby",
}

# Environmental sensor field names and their Python types
ENV_SENSOR_FIELDS: dict = {
    "temperature": float,
    "illuminance": float,
    "occupancy_detected": bool,
    "smoke_detected": bool,
    "gas_detected": bool,
    "doorbell_detected": bool,
}

# Device names and their allowed state strings
DEVICE_FIELDS: dict = {
    "living_room_light": ["on", "off"],
    "bedroom_light": ["on", "off"],
    "living_room_blind": ["open", "closed"],
    "tv_main": ["on", "off", "standby"],
}


def coerce_env_value(sensor: str, raw_value: Any) -> Any:
    """Coerce a raw value to the correct type for a given sensor field.

    Raises ValueError when sensor is not a recognised field.
    """
    typ = ENV_SENSOR_FIELDS.get(sensor)
    if typ is None:
        raise ValueError(f"Unknown env sensor field: {sensor!r}")
    if typ is bool:
        if isinstance(raw_value, bool):
            return raw_value
        if isinstance(raw_value, str):
            return raw_value.lower() in ("true", "1", "yes")
        return bool(raw_value)
    return typ(raw_value)


class SimStateStore:
    """Thread-safe store for virtual environment sensor and device states.

    Environmental sensor virtual nodes call update_env() when they publish.
    Device state virtual nodes call update_device() when they publish.

    Context (trigger) virtual nodes call get_snapshot() at publish time to
    assemble the complete pure_context_payload without needing environmental
    and device state baked into their template.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._env: dict = dict(_DEFAULT_ENV)
        self._devices: dict = dict(_DEFAULT_DEVICES)

    # ------------------------------------------------------------------
    # Write operations (called by virtual nodes on each publish)
    # ------------------------------------------------------------------

    def update_env(self, sensor: str, value: Any) -> None:
        """Update one environmental sensor field."""
        coerced = coerce_env_value(sensor, value)
        with self._lock:
            self._env[sensor] = coerced

    def update_device(self, device: str, state: str) -> None:
        """Update one device state field."""
        if device not in DEVICE_FIELDS:
            raise ValueError(f"Unknown device: {device!r}")
        with self._lock:
            self._devices[device] = state

    def update_from_dict(
        self,
        env: Optional[dict] = None,
        devices: Optional[dict] = None,
    ) -> None:
        """Batch-update env and/or device states (e.g. from a dashboard API call)."""
        with self._lock:
            if env:
                for k, v in env.items():
                    if k in ENV_SENSOR_FIELDS:
                        self._env[k] = coerce_env_value(k, v)
            if devices:
                for k, v in devices.items():
                    if k in DEVICE_FIELDS:
                        self._devices[k] = v

    def reset_to_defaults(self) -> None:
        """Restore all env and device states to default values."""
        with self._lock:
            self._env = dict(_DEFAULT_ENV)
            self._devices = dict(_DEFAULT_DEVICES)

    # ------------------------------------------------------------------
    # Read operations (called by context nodes at publish time)
    # ------------------------------------------------------------------

    def get_env(self) -> dict:
        """Return a snapshot of the current environmental_context."""
        with self._lock:
            return dict(self._env)

    def get_devices(self) -> dict:
        """Return a snapshot of the current device_states."""
        with self._lock:
            return dict(self._devices)

    def get_snapshot(self) -> dict:
        """Return a combined snapshot suitable for pure_context_payload injection."""
        with self._lock:
            return {
                "environmental_context": dict(self._env),
                "device_states": dict(self._devices),
            }

    def to_dict(self) -> dict:
        """Serialise the full store for dashboard display."""
        with self._lock:
            return {
                "env": dict(self._env),
                "devices": dict(self._devices),
                "env_fields": list(ENV_SENSOR_FIELDS.keys()),
                "device_fields": {k: v for k, v in DEVICE_FIELDS.items()},
            }
