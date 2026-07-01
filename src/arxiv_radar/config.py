from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field


DEFAULT_CONFIG_PATH = Path("arxiv-radar.yaml")


class RadarConfig(BaseModel):
    """Research profile used to query, filter, and score arXiv papers."""

    model_config = ConfigDict(extra="forbid")

    categories: list[str] = Field(
        default_factory=lambda: ["quant-ph", "physics.optics", "cond-mat.quant-gas", "math-ph"]
    )
    high_priority_keywords: list[str] = Field(
        default_factory=lambda: [
            "waveguide QED",
            "few-photon scattering",
            "multi-photon scattering",
            "photon scattering",
            "atomic arrays",
            "subwavelength arrays",
            "non-Gaussian light",
            "photon correlations",
            "third-order cumulant",
            "scattering matrix",
        ]
    )
    method_keywords: list[str] = Field(
        default_factory=lambda: [
            "Yudson",
            "Bethe ansatz",
            "input-output theory",
            "Lippmann-Schwinger",
            "resolvent",
            "cumulant expansion",
            "BBGKY",
            "master equation",
            "Lindblad",
        ]
    )
    broader_discovery_keywords: list[str] = Field(
        default_factory=lambda: [
            "quantum nonlinear optics",
            "chiral quantum optics",
            "collective decay",
            "dark states",
            "spin waves",
            "topological photonics",
            "open quantum systems",
        ]
    )
    author_watchlist: list[str] = Field(default_factory=list)

    @property
    def all_keywords(self) -> list[str]:
        keywords = [
            *self.high_priority_keywords,
            *self.method_keywords,
            *self.broader_discovery_keywords,
        ]
        return dedupe_preserve_order(keywords)

    def with_categories(self, categories: list[str] | None) -> "RadarConfig":
        if not categories:
            return self
        return self.model_copy(update={"categories": dedupe_preserve_order(categories)})


def dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.strip()
        key = normalized.casefold()
        if normalized and key not in seen:
            seen.add(key)
            result.append(normalized)
    return result


def default_config() -> RadarConfig:
    return RadarConfig()


def config_to_yaml(config: RadarConfig | None = None) -> str:
    active = config or default_config()
    data: dict[str, Any] = active.model_dump()
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


def write_default_config(path: Path = DEFAULT_CONFIG_PATH, overwrite: bool = False) -> Path:
    if path.exists() and not overwrite:
        raise FileExistsError(f"Config already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(config_to_yaml(), encoding="utf-8")
    return path


def load_config(path: Path | None = None) -> RadarConfig:
    config_path = path or DEFAULT_CONFIG_PATH
    if path is None and not config_path.exists():
        return default_config()
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Could not parse YAML config {config_path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ValueError(f"Config file must contain a YAML mapping: {config_path}")
    return RadarConfig.model_validate(raw)

