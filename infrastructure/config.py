import os
from infrastructure.vault import VaultClient

"""
Configuration module for the Sentinel application.

This module provides a centralized `Config` class that manages application settings,
credentials, and infrastructure endpoints. It integrates with HashiCorp Vault for
secure secret management and supports environment variable overrides.
"""

class Config:
    """
    Centralized configuration for Sentinel services.
    
    This singleton class loads and exposes configuration parameters required by
    various components of the application. It prioritizes security by fetching
    sensitive keys from Vault, while allowing flexibility for infrastructure
    hosts via environment variables.

    Attributes:
        vault (VaultClient): Instance of the Vault client for secret retrieval.
        DB_HOST (str): Hostname of the PostgreSQL database.
        REDIS_HOST (str): Hostname of the Redis cache service.
        RABBITMQ_HOST (str): Hostname of the RabbitMQ broker.
        KEYS (dict): Dictionary containing API keys for external services (FRED, EIA, COMTRADE).
        DB_CONFIG (dict): Dictionary containing database connection parameters.
    """
    def __init__(self):
        """
        Initialize the Config instance.
        
        Sets up the Vault connection and populates configuration attributes.
        - Infrastructure hosts are read from environment variables with defaults to 'localhost'.
        - API keys and passwords are fetched from Vault using the `VaultClient`.
        """
        # Initialize Vault client for secret management
        self.vault = VaultClient()
        
        # Infrastructure Hosts configuration
        # Defaulting to 'localhost' for local development convenience
        self.DB_HOST = os.getenv('DB_HOST', 'localhost')
        self.REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
        self.RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
        
        # API Keys for external data services
        # Fetched securely from Vault
        self.KEYS = {
            'fred': self.vault.get_secret('FRED_API_KEY'),
            'eia': self.vault.get_secret('EIA_API_KEY'),
            'comtrade': self.vault.get_secret('COMTRADE_API_KEY')
        }

        # Database connection configuration
        # 'sentinel_db' is the default database name
        self.DB_CONFIG = {
            'host': self.DB_HOST,
            'database': 'sentinel_db',
            'user': 'postgres',
            'password': self.vault.get_secret('DB_PASSWORD') # Secure password retrieval
        }

# Singleton instance for easy import across the application
config = Config()
