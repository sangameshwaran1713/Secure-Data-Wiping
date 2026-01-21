"""
Configuration Management

Handles system configuration loading, validation, and management for the secure data wiping system.
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import asdict

from .data_models import SystemConfig
from .logging_config import get_component_logger


class ConfigManager:
    """
    Manages system configuration from multiple sources.
    
    Supports configuration from files, environment variables, and database.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file (YAML or JSON)
        """
        self.logger = get_component_logger('config')
        self.config_file = config_file or "config.yaml"
        self._config = SystemConfig()
        self._load_configuration()
    
    def _load_configuration(self) -> None:
        """Load configuration from all available sources."""
        # Start with default configuration
        config_dict = asdict(self._config)
        
        # Load from file if it exists
        if os.path.exists(self.config_file):
            file_config = self._load_from_file(self.config_file)
            config_dict.update(file_config)
            self.logger.info(f"Loaded configuration from {self.config_file}")
        
        # Override with environment variables
        env_config = self._load_from_environment()
        config_dict.update(env_config)
        
        # Create updated configuration object
        self._config = SystemConfig(**config_dict)
        
        # Validate configuration
        self._validate_configuration()
    
    def _load_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load configuration from YAML or JSON file.
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        try:
            with open(file_path, 'r') as f:
                if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                    return yaml.safe_load(f) or {}
                elif file_path.endswith('.json'):
                    return json.load(f) or {}
                else:
                    self.logger.warning(f"Unsupported config file format: {file_path}")
                    return {}
        except Exception as e:
            self.logger.error(f"Failed to load config file {file_path}: {e}")
            return {}
    
    def _load_from_environment(self) -> Dict[str, Any]:
        """
        Load configuration from environment variables.
        
        Environment variables should be prefixed with 'SECURE_WIPE_'
        
        Returns:
            Dict[str, Any]: Configuration dictionary from environment
        """
        env_config = {}
        prefix = "SECURE_WIPE_"
        
        env_mappings = {
            f"{prefix}GANACHE_URL": "ganache_url",
            f"{prefix}CONTRACT_ADDRESS": "contract_address",
            f"{prefix}DEFAULT_OPERATOR": "default_operator",
            f"{prefix}LOG_LEVEL": "log_level",
            f"{prefix}CERTIFICATE_TEMPLATE": "certificate_template",
            f"{prefix}MAX_RETRY_ATTEMPTS": "max_retry_attempts",
            f"{prefix}DATABASE_PATH": "database_path",
            f"{prefix}CERTIFICATES_DIR": "certificates_dir",
            f"{prefix}LOGS_DIR": "logs_dir"
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert numeric values
                if config_key == "max_retry_attempts":
                    try:
                        value = int(value)
                    except ValueError:
                        self.logger.warning(f"Invalid numeric value for {env_var}: {value}")
                        continue
                
                env_config[config_key] = value
                self.logger.debug(f"Loaded from environment: {config_key} = {value}")
        
        return env_config
    
    def _validate_configuration(self) -> None:
        """Validate the loaded configuration."""
        errors = []
        
        # Validate Ganache URL
        if not self._config.ganache_url:
            errors.append("Ganache URL is required")
        elif not self._config.ganache_url.startswith(('http://', 'https://')):
            errors.append("Ganache URL must be a valid HTTP/HTTPS URL")
        
        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self._config.log_level.upper() not in valid_log_levels:
            errors.append(f"Log level must be one of: {valid_log_levels}")
        
        # Validate retry attempts
        if self._config.max_retry_attempts < 1:
            errors.append("Max retry attempts must be at least 1")
        
        # Validate paths
        if not self._config.database_path:
            errors.append("Database path is required")
        
        if not self._config.certificates_dir:
            errors.append("Certificates directory is required")
        
        if not self._config.logs_dir:
            errors.append("Logs directory is required")
        
        if errors:
            error_msg = "Configuration validation failed: " + "; ".join(errors)
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        self.logger.info("Configuration validation passed")
    
    def get_config(self) -> SystemConfig:
        """
        Get the current system configuration.
        
        Returns:
            SystemConfig: Current configuration object
        """
        return self._config
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """
        Get a specific configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Any: Configuration value
        """
        return getattr(self._config, key, default)
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        Update configuration with new values.
        
        Args:
            updates: Dictionary of configuration updates
        """
        config_dict = asdict(self._config)
        config_dict.update(updates)
        
        # Create new configuration object
        self._config = SystemConfig(**config_dict)
        
        # Re-validate
        self._validate_configuration()
        
        self.logger.info(f"Configuration updated: {list(updates.keys())}")
    
    def save_to_file(self, file_path: Optional[str] = None) -> None:
        """
        Save current configuration to file.
        
        Args:
            file_path: Path to save configuration (defaults to current config file)
        """
        save_path = file_path or self.config_file
        config_dict = asdict(self._config)
        
        try:
            # Create directory if it doesn't exist
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'w') as f:
                if save_path.endswith('.yaml') or save_path.endswith('.yml'):
                    yaml.dump(config_dict, f, default_flow_style=False, indent=2)
                elif save_path.endswith('.json'):
                    json.dump(config_dict, f, indent=2)
                else:
                    # Default to YAML
                    yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Configuration saved to {save_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration to {save_path}: {e}")
            raise
    
    def create_directories(self) -> None:
        """Create necessary directories based on configuration."""
        directories = [
            self._config.certificates_dir,
            self._config.logs_dir,
            Path(self._config.database_path).parent
        ]
        
        for directory in directories:
            try:
                Path(directory).mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Created directory: {directory}")
            except Exception as e:
                self.logger.error(f"Failed to create directory {directory}: {e}")
                raise
    
    def get_database_path(self) -> str:
        """Get the full database path."""
        return self._config.database_path
    
    def get_certificates_dir(self) -> str:
        """Get the certificates directory path."""
        return self._config.certificates_dir
    
    def get_logs_dir(self) -> str:
        """Get the logs directory path."""
        return self._config.logs_dir
    
    def is_ganache_local(self) -> bool:
        """Check if Ganache URL is local (localhost or 127.0.0.1)."""
        url = self._config.ganache_url.lower()
        return 'localhost' in url or '127.0.0.1' in url or '0.0.0.0' in url


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_file: Optional[str] = None) -> ConfigManager:
    """
    Get the global configuration manager instance.
    
    Args:
        config_file: Path to configuration file (only used on first call)
        
    Returns:
        ConfigManager: Global configuration manager
    """
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigManager(config_file)
    
    return _config_manager


def get_config() -> SystemConfig:
    """
    Get the current system configuration.
    
    Returns:
        SystemConfig: Current system configuration
    """
    return get_config_manager().get_config()


def initialize_system_directories() -> None:
    """Initialize all system directories based on configuration."""
    get_config_manager().create_directories()