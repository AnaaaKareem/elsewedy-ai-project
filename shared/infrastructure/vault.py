import os
import hvac
import logging

# Configure basic logging for the module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VaultClient:
    """
    A client wrapper for HashiCorp Vault interactions using the hvac library.
    
    This class handles authentication and connection to a Vault server, providing
    methods to retrieve secrets safely. It supports dual authentication modes:
    1.  **AppRole** (Production): Uses secure RoleID/SecretID injection.
    2.  **Token** (Development): Uses a root or developer token.
    
    Attributes:
        vault_addr (str): The URL of the Vault server (env: VAULT_ADDR).
        vault_token (str): The authentication token for Vault (env: VAULT_TOKEN).
        client (hvac.Client): The raw hvac client instance.
    """

    def __init__(self):
        """
        Initialize the VaultClient.
        
        Loads configuration from environment variables 'VAULT_ADDR' and 'VAULT_TOKEN'.
        Attempts to establish a connection immediately upon instantiation.
        """
        # Default to localhost for development if env vars are not set
        self.vault_addr = os.getenv('VAULT_ADDR', 'http://localhost:8200')
        self.vault_token = os.getenv('VAULT_TOKEN', 'root_token') # Default for dev mode
        self.client = None
        
        # Initiate connection immediately
        self.connect()

    def connect(self):
        """
        Establish connection to the Vault server.
        
        Prioritizes AppRole authentication if RoleID/SecretID are present.
        Falls back to Token authentication (Dev Mode).
        """
        try:
            self.client = hvac.Client(url=self.vault_addr)
            
            # 1. Check for AppRole Credentials
            role_id = os.getenv('VAULT_ROLE_ID')
            secret_id = os.getenv('VAULT_SECRET_ID')
            
            if role_id and secret_id:
                try:
                    if self.client.auth.approle.login(
                        role_id=role_id,
                        secret_id=secret_id
                    ):
                        logger.info("✅ Authenticated via AppRole.")
                except Exception as auth_err:
                    logger.error(f"❌ AppRole Login Failed: {auth_err}")
                    self.client = None
                    return
            else:
                # 2. Fallback to Token (Dev Mode)
                self.client.token = self.vault_token
            
            # 3. Verify
            if self.client.is_authenticated():
                logger.info(f"✅ Connected to Vault at {self.vault_addr}")
            else:
                logger.warning("⚠️ Failed to authenticate with Vault. Check Token or AppRole creds.")
                self.client = None

        except Exception as e:
            logger.error(f"❌ Could not connect to Vault: {e}")
            self.client = None

    def _fetch_vault_data(self, mount_point, path):
        """
        Internal helper to fetch the raw data dictionary from a specific Vault path.
        
        Args:
            mount_point (str): The mount point of the KV secret engine.
            path (str): The path to the secret.
            
        Returns:
            dict: The dictionary of secrets found at the path, or an empty dict if
                  fetch fails or path is invalid.
        """
        # If client is not connected, return empty immediately
        if not self.client:
            return {}
            
        try:
            # Try primary path read using KV v2 API
            response = self.client.secrets.kv.v2.read_secret_version(
                mount_point=mount_point,
                path=path
            )
            # Extract actual data from the response structure
            val = response.get('data', {}).get('data', {})
            return val
            
        except hvac.exceptions.InvalidPath:
            # LEGACY SUPPORT: Retry logic for 'sentinel' path specifically
            # This is to handle potential structure differences in older Vault setups
            if path == 'sentinel':
                try:
                    response = self.client.secrets.kv.v2.read_secret_version(
                        mount_point=mount_point,
                        path='secret/sentinel'
                    )
                    val = response.get('data', {}).get('data', {})
                    return val
                except Exception:
                    # If retry fails, ignore and return empty
                    pass
                    
        except Exception as e:
            # Log any other errors during read (e.g., permission denied)
            logger.warning(f"Vault read error: {e}")
            
        return {}

    def get_secret(self, key, mount_point='secret', path='sentinel'):
        """
        Retrieve a specific secret value by key with Fallback logic.
        
        Logic:
        1. Attempt to read from Vault at the specified path.
        2. If key exists, return it.
        3. If key missing or Vault error, attempt to read from Environment Variables.
        4. If both fail, log warning and return None.
        
        Args:
            key (str): The key of the secret to retrieve.
            mount_point (str, optional): Vault KV mount point. Defaults to 'secret'.
            path (str, optional): Vault secret path. Defaults to 'sentinel'.
            
        Returns:
            str or None: The secret value if found, otherwise None.
        """
        # Attempt to fetch from Vault first
        data = self._fetch_vault_data(mount_point, path)
        if key in data:
            logger.debug(f"🔑 Fetched '{key}' from Vault.")
            return data[key]

        # Fallback to Environment Variable if not in Vault
        val = os.getenv(key)
        if val:
            logger.debug(f"Fetched '{key}' from environment variables (fallback).")
        else:
            logger.warning(f"⚠️ Secret '{key}' not found in Vault or Environment.")
            
        return val

    def get_all_secrets(self, mount_point='secret', path='sentinel'):
        """
        Retrieve all secrets located at the specified path.
        
        Args:
            mount_point (str, optional): Vault KV mount point. Defaults to 'secret'.
            path (str, optional): Vault secret path. Defaults to 'sentinel'.
            
        Returns:
            dict: A dictionary of all secrets found at the path.
        """
        secrets = self._fetch_vault_data(mount_point, path)
        if secrets:
            logger.info("✅ Loaded secrets from Vault.")
        
        return secrets
