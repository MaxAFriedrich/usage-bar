"""Configuration management for usage-bar monitor."""
import os
from pathlib import Path
import yaml


def load_config():
    """Load configuration from config.yml.

    Searches for config.yml in the following order
    """
    config_paths = [
        Path.home() / ".config" / "usage-bar" / "config.yml",
        Path("/etc/usage-bar/config.yml"),
        Path("config.yml"),
        Path(__file__).parent.parent / "config.yml",
    ]

    for config_path in config_paths:
        if config_path.exists():
            print(f"Loading config from: {config_path}")
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)

    # Return default configuration if no config file found
    raise Exception("Warning: No config file found, using defaults")


class Config:
    """Configuration holder."""
    def __init__(self):
        config = load_config()
        self.break_threshold = config['break_threshold']
        self.break_length = config['break_length']
        self.overspeed_threshold = config['overspeed_threshold']
        self.overspeed_count_multiplier = config['overspeed_count_multiplier']
        self.max_overspeed_penalty = config['max_overspeed_penalty']
        self.socket_path = "/tmp/usage-bar.sock"
