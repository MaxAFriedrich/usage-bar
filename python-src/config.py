"""Configuration management for usage-bar monitor."""
import os
from pathlib import Path
import yaml


def load_config():
    """Load configuration from config.yml.
    
    Searches for config.yml in the following order:
    1. ~/.config/usage-bar/config.yml
    2. /etc/usage-bar/config.yml
    3. ./config.yml (current directory)
    4. Script directory (for development)
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
    print("Warning: No config file found, using defaults")
    return {
        'break_threshold': 300,
        'overspeed_threshold': 15,
        'overspeed_count_multiplier': 2,
        'max_overspeed_penalty': 600,
    }


class Config:
    """Configuration holder."""
    def __init__(self):
        config = load_config()
        self.break_threshold = config['break_threshold']
        self.overspeed_threshold = config['overspeed_threshold']
        self.overspeed_count_multiplier = config['overspeed_count_multiplier']
        self.max_overspeed_penalty = config['max_overspeed_penalty']
        self.socket_path = "/tmp/usage-bar.sock"
