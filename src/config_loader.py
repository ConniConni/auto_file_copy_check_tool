"""Configuration loader module for file copy tool."""

import configparser
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class PhaseCode(StrEnum):
    """Enumeration of phase codes."""

    PHASE_030 = "030"
    PHASE_040 = "040"
    PHASE_050 = "050"
    PHASE_060 = "060"
    PHASE_070 = "070"
    PHASE_080 = "080"
    PHASE_090 = "090"


@dataclass
class Config:
    """Configuration data class.

    Attributes:
        base_path_internal: Base path for internal area (project member workspace).
        base_path_external: Base path for external area (customer-facing).
        document_patterns: Document name patterns for each phase.
        extra_files: List of extra file names to include (exact match).
        project_name: Default project name (None if not set).
        quarter: Default quarter (None if not set).
        item_name: Default item name (None if not set).
    """

    base_path_internal: Path
    base_path_external: Path
    document_patterns: dict[PhaseCode, list[str]] = field(default_factory=dict)
    extra_files: list[str] = field(default_factory=list)
    project_name: str | None = None
    quarter: str | None = None
    item_name: str | None = None


def load_config(config_path: Path) -> Config:
    """Load configuration from INI file.

    Args:
        config_path: Path to the configuration file.

    Returns:
        Config: Loaded configuration data.

    Raises:
        FileNotFoundError: If config file does not exist.
        configparser.NoSectionError: If required section is missing.
        configparser.NoOptionError: If required option is missing.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    parser = configparser.ConfigParser()
    parser.read(config_path, encoding="utf-8")

    # Load paths
    base_path_internal = Path(parser.get("Paths", "base_path_internal"))
    base_path_external = Path(parser.get("Paths", "base_path_external"))

    # Load document patterns
    document_patterns: dict[PhaseCode, list[str]] = {}
    for phase in PhaseCode:
        pattern_str = parser.get("Documents", phase.value)
        if pattern_str.strip():
            # Split by comma and strip whitespace
            patterns = [p.strip() for p in pattern_str.split(",") if p.strip()]
            document_patterns[phase] = patterns
        else:
            document_patterns[phase] = []

    # Load extra files
    extra_files_str = parser.get("ExtraFiles", "include_files")
    if extra_files_str.strip():
        extra_files = [f.strip() for f in extra_files_str.split(",") if f.strip()]
    else:
        extra_files = []

    # Load project information (optional)
    project_name = None
    quarter = None
    item_name = None
    if parser.has_section("Project"):
        if parser.has_option("Project", "project_name"):
            project_name_str = parser.get("Project", "project_name").strip()
            project_name = project_name_str if project_name_str else None
        if parser.has_option("Project", "quarter"):
            quarter_str = parser.get("Project", "quarter").strip()
            quarter = quarter_str if quarter_str else None
        if parser.has_option("Project", "item_name"):
            item_name_str = parser.get("Project", "item_name").strip()
            item_name = item_name_str if item_name_str else None

    return Config(
        base_path_internal=base_path_internal,
        base_path_external=base_path_external,
        document_patterns=document_patterns,
        extra_files=extra_files,
        project_name=project_name,
        quarter=quarter,
        item_name=item_name,
    )
