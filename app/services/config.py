import os
import json
import logging
from typing import Any, Dict, List, Optional

import boto3


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)


def _get_ssm_client():
    return boto3.client("ssm")


def _get_ssm_parameter(name: str, with_decryption: bool = True) -> Optional[str]:
    try:
        client = _get_ssm_client()
        resp = client.get_parameter(Name=name, WithDecryption=with_decryption)
        return resp["Parameter"]["Value"]
    except Exception as exc:
        _logger.info(f"Could not load SSM parameter {name}: {exc}")
        return None


def _load_json(value: Optional[str], default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        _logger.warning("Failed to JSON-parse config value; using default")
        return default


def get_token() -> str:
    token = os.getenv("TOKEN", "")
    if not token:
        _logger.warning("TOKEN env var is empty")
    return token


def get_timezone() -> str:
    # Prefer SSM, then env, then UTC
    prefix = os.getenv("CONFIG_SSM_PREFIX")
    if prefix:
        tz = _get_ssm_parameter(f"{prefix}/timezone", with_decryption=False)
        if tz:
            return tz
    return os.getenv("DEFAULT_TIMEZONE", "UTC")


def get_broadcast_chat_ids() -> List[str]:
    # Prefer SSM, then env, else empty
    prefix = os.getenv("CONFIG_SSM_PREFIX")
    raw: Optional[str] = None
    if prefix:
        raw = _get_ssm_parameter(f"{prefix}/broadcast_chat_ids", with_decryption=False)
    if raw is None:
        raw = os.getenv("BROADCAST_CHAT_IDS_JSON")
    ids = _load_json(raw, default=[])
    # Normalize to strings (works for numeric IDs and @channel usernames)
    result: List[str] = []
    for item in ids:
        try:
            # keep as string
            result.append(str(item))
        except Exception:
            _logger.warning(f"Invalid chat id in config: {item}")
    return result


def get_league_mapping() -> Dict[str, int]:
    # Mapping of telegram chat_id (string or int) -> livefpl league id (int)
    prefix = os.getenv("CONFIG_SSM_PREFIX")
    raw: Optional[str] = None
    if prefix:
        raw = _get_ssm_parameter(f"{prefix}/league_mapping", with_decryption=False)
    if raw is None:
        raw = os.getenv("LEAGUE_MAPPING_JSON")
    mapping = _load_json(raw, default={})
    # Normalize keys to str for consistent handling; values to int
    normalized: Dict[str, int] = {}
    for key, value in mapping.items():
        try:
            normalized[str(int(key))] = int(value)
        except Exception:
            _logger.warning(f"Invalid league mapping entry: {key} -> {value}")
    return normalized


def get_players_mapping() -> Dict[str, Dict[str, List[str]]]:
    # Mapping of livefpl league id (int/str) -> { playerId: [displayName, teamName] }
    prefix = os.getenv("CONFIG_SSM_PREFIX")
    raw: Optional[str] = None
    if prefix:
        raw = _get_ssm_parameter(f"{prefix}/players_mapping", with_decryption=False)
    if raw is None:
        raw = os.getenv("PLAYERS_MAPPING_JSON")
    data = _load_json(raw, default={})
    # Keep structure as-is but normalize top-level keys to str
    normalized: Dict[str, Dict[str, List[str]]] = {}
    for league_id, players in data.items():
        normalized[str(int(league_id))] = players
    return normalized


def get_deadline_alert_windows_minutes() -> List[int]:
    # Default windows: 1h, 2h, 6h, 24h, 48h
    default_windows = [60, 120, 360, 1440, 2880]
    prefix = os.getenv("CONFIG_SSM_PREFIX")
    raw: Optional[str] = None
    if prefix:
        raw = _get_ssm_parameter(f"{prefix}/deadline_alert_windows_minutes", with_decryption=False)
    if raw is None:
        raw = os.getenv("DEADLINE_ALERT_WINDOWS_MINUTES_JSON")
    windows = _load_json(raw, default=default_windows)
    # ensure ints
    result: List[int] = []
    for w in windows:
        try:
            result.append(int(w))
        except Exception:
            _logger.warning(f"Invalid deadline window value: {w}")
    return result


def get_deadline_alert_tolerance_seconds() -> int:
    # Default ±3 minutes tolerance to accommodate 15-min schedules
    default_tolerance = 180
    prefix = os.getenv("CONFIG_SSM_PREFIX")
    raw: Optional[str] = None
    if prefix:
        raw = _get_ssm_parameter(f"{prefix}/deadline_alert_tolerance_seconds", with_decryption=False)
    if raw is None:
        raw = os.getenv("DEADLINE_ALERT_TOLERANCE_SECONDS")
    try:
        return int(raw) if raw is not None else default_tolerance
    except Exception:
        return default_tolerance 