"""Configuration management for Abra MCP server."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class AbraConfig(BaseSettings):
    """Configuration for Abra Gen API connection.

    All values are loaded from environment variables with ABRA_ prefix.
    Example:
        ABRA_HOST=http://localhost:699
        ABRA_DATABASE=Demo
        ABRA_USERNAME=apiuser
        ABRA_PASSWORD=secretpassword
    """

    model_config = SettingsConfigDict(
        env_prefix="ABRA_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    host: str = "http://localhost:699"
    """Abra Gen API host URL (e.g., http://localhost:699 or http://192.168.1.100:8080)"""

    database: str = "Demo"
    """Database/connection identifier (e.g., Demo, D, Production)"""

    username: str = ""
    """API username for authentication"""

    password: str = ""
    """API password for authentication"""

    timeout: int = 30
    """HTTP request timeout in seconds"""

    max_retries: int = 3
    """Maximum number of retry attempts for failed requests"""

    @property
    def base_url(self) -> str:
        """Construct base URL for API requests.

        Returns:
            Base URL in format: {host}/{database}
        """
        return f"{self.host.rstrip('/')}/{self.database}"

    def validate_required_fields(self) -> None:
        """Validate that all required fields are set.

        Raises:
            ValueError: If any required field is missing
        """
        errors = []

        if not self.host:
            errors.append("ABRA_HOST is required")
        if not self.database:
            errors.append("ABRA_DATABASE is required")
        if not self.username:
            errors.append("ABRA_USERNAME is required")
        if not self.password:
            errors.append("ABRA_PASSWORD is required")

        if errors:
            raise ValueError(
                "Missing required configuration. Please set the following environment variables:\n"
                + "\n".join(f"  - {error}" for error in errors)
            )

    def __repr__(self) -> str:
        """String representation with password masked."""
        return (
            f"AbraConfig("
            f"host={self.host!r}, "
            f"database={self.database!r}, "
            f"username={self.username!r}, "
            f"password={'***' if self.password else ''!r})"
        )


def get_config() -> AbraConfig:
    """Get and validate Abra configuration.

    Returns:
        AbraConfig instance with validated settings

    Raises:
        ValueError: If required configuration is missing
    """
    config = AbraConfig()
    config.validate_required_fields()
    return config
