from asyncio import subprocess
from typing import Dict, Literal, Protocol, Sequence, Union, runtime_checkable

import click
import namegenerator
import typer
import yaml
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from pydantic import BaseModel, ConfigDict, Field
import secrets


def generate_django_secret_key():
    """Generate a 50-character Django SECRET_KEY."""
    chars = "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)"
    return "".join(secrets.choice(chars) for _ in range(50))


def generate_alpha_numeric_string(length: int = 40) -> str:
    """
    Generate a random alphanumeric string of a given length.
    This is used to create unique names for resources such as S3 buckets.
    """
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(secrets.choice(chars) for _ in range(length))


class KeyPair(BaseModel):
    key_type: Literal["RSA256"] = Field(
        default="RSA256",
        description="Type of the key pair, currently only RSA is supported",
    )
    public_key: str = Field(..., description="Public key for the server")
    private_key: str = Field(..., description="Private key for the server")


def generate_name() -> str:
    """
    Generate a random name using the namegenerator library.
    This is used to create unique names for resources such as S3 buckets.
    """
    return namegenerator.gen()


def build_key_pair() -> KeyPair:
    key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=crypto_default_backend()
    )

    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.PKCS8,
        crypto_serialization.NoEncryption(),
    ).decode()

    public_key = (
        key.public_key()
        .public_bytes(
            crypto_serialization.Encoding.OpenSSH,
            crypto_serialization.PublicFormat.OpenSSH,
        )
        .decode()
    )

    return KeyPair(
        public_key=public_key,
        private_key=private_key,
    )


class S3BucketConfig(BaseModel):
    kind: Literal["s3"] = Field(
        default="s3", description="Kind of the bucket, specifically for MinIO"
    )
    access_key: str = Field(description="Access key for the S3 bucket")
    secret_key: str = Field(description="Secret key for the S3 bucket")
    region: str = Field(default="us-east-1", description="Region for the S3 bucket")
    endpoint_url: str = Field(description="Endpoint URL for the S3 bucket")
    bucket_name: str = Field(description="Name of the S3 bucket")


class LocalBucketConfig(BaseModel):
    kind: Literal["local"] = Field(
        default="local", description="Kind of the bucket, specifically for MinIO"
    )
    bucket_name: str = Field(
        default_factory=generate_name,
        description="Name of the local bucket. If not provided, a random name will be generated",
    )


class RemoteDBConfig(BaseModel):
    kind: Literal["remote"] = Field(
        default="remote", description="Kind of the bucket, specifically for MinIO"
    )
    host: str = Field(description="Host for the remote database")
    port: int = Field(default=5432, description="Port for the remote database")
    user: str = Field(description="User for the remote database")
    password: str = Field(description="Password for the remote database")
    db: str = Field(description="Database name for the remote database")


class LocalDBConfig(BaseModel):
    kind: Literal["local"] = Field(
        default="local", description="Kind of the bucket, specifically for MinIO"
    )
    db: str = Field(
        default="mikro",
        description="Database name for the local database",
    )


class SpecificAdminConfig(BaseModel):
    kind: Literal["specific"] = Field(
        default="specific", description="Kind of the bucket, specifically for MinIO"
    )
    username: str = Field(description="Username for the admin user")
    password: str = Field(description="Password for the admin user")
    email: str | None = Field(description="Email for the admin user", default=None)


class GlobalAdminConfig(BaseModel):
    kind: Literal["global"] = Field(
        default="global", description="Using the global admin user for the server"
    )


class LocalRedisConfig(BaseModel):
    kind: Literal["local"] = Field(
        default="local",
        description="Kind of the Redis configuration, specifically for local Redis",
    )


class RemoteRedisConfig(BaseModel):
    kind: Literal["remote"] = Field(
        default="remote",
        description="Kind of the Redis configuration, specifically for remote Redis",
    )
    host: str = Field(description="Host for the remote Redis server")
    port: int = Field(default=6379, description="Port for the remote Redis server")


BucketConfig = Union[S3BucketConfig, LocalBucketConfig]
DBConfig = Union[RemoteDBConfig, LocalDBConfig]
AdminConfig = Union[SpecificAdminConfig, GlobalAdminConfig]
RedisConfig = Union[LocalRedisConfig, RemoteRedisConfig]


class LocalChromaDBConfig(BaseModel):
    kind: Literal["local"] = Field(
        default="local",
        description="Kind of the ChromaDB configuration, specifically for local ChromaDB",
    )
    db_name: str = Field(
        description="Database name for the local ChromaDB",
    )


class RemoteChromaDBConfig(BaseModel):
    kind: Literal["remote"] = Field(
        default="remote",
        description="Kind of the ChromaDB configuration, specifically for remote ChromaDB",
    )
    host: str = Field(description="Host for the remote ChromaDB server")
    port: int = Field(default=8000, description="Port for the remote ChromaDB")
    db_name: str = Field(
        description="Database name for the remote ChromaDB",
    )


ChromaDBConfig = Union[LocalChromaDBConfig, RemoteChromaDBConfig]


class LocalOllamaConfig(BaseModel):
    kind: Literal["local"] = Field(
        default="local",
        description="Kind of the Ollama configuration, specifically for local Ollama",
    )


class RemoteOllamaConfig(BaseModel):
    kind: Literal["remote"] = Field(
        default="remote",
        description="Kind of the Ollama configuration, specifically for remote Ollama",
    )
    host: str = Field(description="Host for the remote Ollama server")
    port: int = Field(default=11434, description="Port for the remote Ollama server")


OllamaConfig = Union[LocalOllamaConfig, RemoteOllamaConfig]


class LocalAuthConfig(BaseModel):
    kind: Literal["local"] = Field(
        default="local",
        description="Kind of the authentication configuration, specifically for local authentication with an arkitekt server",
    )


class StatikTokenAuthConfig(BaseModel):
    kind: Literal["static_token"] = Field(
        default="static_token",
        description="Kind of the authentication configuration, specifically for static token authentication",
    )
    token: str = Field(
        default=secrets.token_hex(16),
        description="Static token for the authentication configuration. This is used to authenticate requests to the service",
    )
    user: int = Field(
        default=1,
        description="User ID for the static token authentication configuration. This is used to identify the user associated with the static token",
    )
    issuer: str = Field(
        default="local_token",
        description="Issuer for the static token authentication configuration. This is used to identify the issuer of the token",
    )


AuthConfig = Union[LocalAuthConfig, StatikTokenAuthConfig]


class LocalPath(BaseModel):
    kind: Literal["local"] = Field(
        default="local",
        description="Retrieves the path configuration from the gateway",
    )


class ForcePath(BaseModel):
    kind: Literal["force"] = Field(
        default="force",
        description="Forces the path configuration to be used in the gateway",
    )
    path: str = Field(
        default="/",
        description="Path to be used for this service This is used to configure the path for the service in the Gateway",
    )


PathConfig = Union[LocalPath, ForcePath]


class BaseServiceConfig(BaseModel):
    internal_port: int = Field(
        default=80,
        description="Internal port for the service. This is used to route requests to the service",
    )

    mount_github: bool = Field(
        default=False, description="Mount GitHub repository for the service"
    )
    github_repo: str = Field(
        default="", description="GitHub repository URL for the service"
    )
    admin_config: AdminConfig = Field(
        default_factory=GlobalAdminConfig,
        description="Admin configuration for the service",
    )
    auth_config: AuthConfig = Field(
        default_factory=LocalAuthConfig,
        description="Authentication configuration for the service",
    )
    path_config: PathConfig = Field(
        default_factory=LocalPath,
        description="Path configuration for the service. This is used to configure the path for the service in the gateway",
    )

    allowed_hosts: list[str] = Field(
        default=["*"],
        description="List of allowed hosts for the service. This is used to prevent host header attacks. By default all hosts are allowed",
    )
    debug: bool = Field(
        default=False,
        description="Whether to enable debug mode for the service. If True, the service will run in debug mode, which may expose sensitive information and should not be used in production",
    )
    secret_key: str = Field(
        default_factory=generate_django_secret_key,
        description="Secret key for the service. This is used to sign cookies and other sensitive data. It should be kept secret and not shared with anyone",
    )

    def build_run_command(self) -> str:
        """
        Build the command to run the service.
        This is used to generate the command that will be executed to start the service.
        """
        if self.debug or self.mount_github:
            return "bash run-debug.sh"
        return "bash run.sh"


class BaseStackConfig(BaseModel):
    """
    Base configuration for a stack.
    This is used to define the common attributes and methods for all stacks.
    """

    description: str | None = Field(
        default=None, description="Description of the stack"
    )
    services: list[BaseServiceConfig] = Field(
        default_factory=list, description="List of services in the stack"
    )


@runtime_checkable
class BaseService(Protocol):
    """
    Protocol for a base service configuration.
    This is used to define the common attributes and methods for all services.
    """

    enabled: bool
    host: str
    image: str
    path_config: PathConfig
    auth_config: AuthConfig
    admin_config: AdminConfig
    db_config: DBConfig
    redis_config: RedisConfig
    debug: bool
    allowed_hosts: list[str]
    secret_key: str
    internal_port: int = Field(
        default=80,
    )

    def get_buckets(self) -> Dict[str, BucketConfig]:
        """
        Get the list of buckets for the service.
        This is used to retrieve the buckets that are configured for the service.
        """
        ...

    def build_run_command(self) -> str:
        """
        Build the command to run the service.
        This is used to generate the command that will be executed to start the service.
        """
        ...


class RekuestConfig(BaseServiceConfig):
    enabled: bool = Field(
        default=True, description="Whether the MinIO service is enabled"
    )
    image: str = Field(
        default="jhnnsrs/rekuest:dev",
        description="Docker image for the Rekuest service. This is used to run the Rekuest server",
    )
    host: str = Field(default="rekuest", description="Host for the Rekuest service")
    github_repo: str = Field(
        default="https://github.com/arkitektio/rekuest-server-next",
        description="GitHub repository URL for the Lok service",
    )
    media_bucket: BucketConfig = Field(
        default_factory=LocalBucketConfig,
    )
    db_config: DBConfig = Field(
        default_factory=lambda: LocalDBConfig(db="rekuest"),
        description="Database configuration for the service",
    )
    redis_config: RedisConfig = Field(
        default_factory=LocalRedisConfig,
        description="Redis configuration for the service",
    )

    def get_buckets(self) -> Dict[str, BucketConfig]:
        """
        Get the list of buckets for the Rekuest service.
        This is used to retrieve the buckets that are configured for the Rekuest service.
        """
        return {"media": self.media_bucket}


class LokConfig(BaseServiceConfig):
    enabled: bool = Field(
        default=True, description="Whether the Lok service is enabled"
    )
    image: str = Field(
        default="jhnnsrs/lok:dev",
        description="Docker image for the Rekuest service. This is used to run the Rekuest server",
    )
    host: str = Field(default="lok", description="Host for the Lok service")
    github_repo: str = Field(
        default="https://github.com/arkitektio/lok-server-next",
        description="GitHub repository URL for the Lok service",
    )
    issuer: str = Field(
        default="lok",
        description="Issuer for the Lok service. This is used to identify the issuer of the token",
    )
    media_bucket: BucketConfig = Field(
        default_factory=LocalBucketConfig,
    )
    db_config: DBConfig = Field(
        default_factory=lambda: LocalDBConfig(db="lok"),
        description="Database configuration for the service",
    )
    redis_config: RedisConfig = Field(
        default_factory=LocalRedisConfig,
        description="Redis configuration for the service",
    )
    auth_key_pair: KeyPair = Field(
        default_factory=build_key_pair,
        description="Key pair for the Arkitekt server, used for secure communication",
    )

    def get_buckets(self) -> Dict[str, BucketConfig]:
        """
        Get the list of buckets for the Lok service.
        This is used to retrieve the buckets that are configured for the Lok service.
        """
        return {"media": self.media_bucket}


class MinioConfig(BaseModel):
    host: str = Field(default="minio", description="Host for the MinIO service")
    enabled: bool = Field(
        default=True, description="Whether the MinIO service is enabled"
    )
    internal_port: int = Field(
        default=9000, description="Internal port for the MinIO service"
    )
    access_key: str = Field(
        default_factory=generate_alpha_numeric_string,
        description="Access key for the MinIO service",
    )
    secret_key: str = Field(
        default_factory=generate_alpha_numeric_string,
        description="Secret key for the MinIO service",
    )
    root_user: str = Field(
        default_factory=generate_name, description="Root user for the MinIO service"
    )
    root_password: str = Field(
        default_factory=generate_alpha_numeric_string,
        description="Root password for the MinIO service",
    )
    init_container_host: str = Field(
        default="minio_init",
    )
    init_container_image: str = Field(
        default="jhnnsrs/init:dev",
        description="Docker image for the MinIO init container",
    )
    image: str = Field(
        default="minio/minio:RELEASE.2025-02-18T16-25-55Z",
        description="Docker image for the MinIO service. This is used to run the MinIO server",
    )


class KabinetConfig(BaseServiceConfig):
    enabled: bool = Field(
        default=True, description="Whether the MinIO service is enabled"
    )
    image: str = Field(
        default="jhnnsrs/kabinet:dev",
        description="Docker image for the Rekuest service. This is used to run the Rekuest server",
    )
    github_repo: str = Field(
        default="https://github.com/arkitektio/kabinet-server",
        description="GitHub repository URL for the Lok service",
    )
    media_bucket: BucketConfig = Field(
        default_factory=LocalBucketConfig,
    )
    host: str = Field(default="kabinet", description="Host for the service")
    db_config: DBConfig = Field(
        default_factory=lambda: LocalDBConfig(db="kabinet"),
        description="Database configuration for the service",
    )
    ensured_repositories: list[str] = Field(
        default_factory=lambda: [
            "arkitektio-apps/ome:main",
            "arkitektio-apps/renderer:main",
        ],
        description="List of repositories that are ensured to be present in the Kabinet service",
    )
    redis_config: RedisConfig = Field(
        default_factory=LocalRedisConfig,
        description="Redis configuration for the service",
    )

    def get_buckets(self) -> Dict[str, BucketConfig]:
        """
        Get the list of buckets for the Rekuest service.
        This is used to retrieve the buckets that are configured for the Rekuest service.
        """
        return {"media": self.media_bucket}


class FlussConfig(BaseServiceConfig):
    enabled: bool = Field(
        default=True, description="Whether the Fluss service is enabled"
    )
    host: str = Field(default="fluss", description="Host for the Fluss service")
    github_repo: str = Field(
        default="https://github.com/arkitektio/fluss-server-next",
        description="GitHub repository URL for the Lok service",
    )
    image: str = Field(
        default="jhnnsrs/fluss:dev",
        description="Docker image for the Rekuest service. This is used to run the Rekuest server",
    )
    media_bucket: BucketConfig = Field(
        default_factory=LocalBucketConfig,
    )
    db_config: DBConfig = Field(
        default_factory=lambda: LocalDBConfig(db="fluss"),
        description="Database configuration for the service",
    )
    redis_config: RedisConfig = Field(
        default_factory=LocalRedisConfig,
        description="Redis configuration for the service",
    )

    def get_buckets(self) -> Dict[str, BucketConfig]:
        """
        Get the list of buckets for the Rekuest service.
        This is used to retrieve the buckets that are configured for the Rekuest service.
        """
        return {"media": self.media_bucket}


class AlpakaConfig(BaseServiceConfig):
    enabled: bool = Field(
        default=False, description="Whether the Fluss service is enabled"
    )
    image: str = Field(
        default="jhnnsrs/alpaka:dev",
        description="Docker image for the Rekuest service. This is used to run the Rekuest server",
    )
    host: str = Field(default="alpaka", description="Host for the Fluss service")
    github_repo: str = Field(
        default="https://github.com/arkitektio/alpaka-server",
        description="GitHub repository URL for the Lok service",
    )
    media_bucket: BucketConfig = Field(
        default_factory=LocalBucketConfig,
    )
    db_config: DBConfig = Field(
        default_factory=lambda: LocalDBConfig(db="alpaka"),
        description="Database configuration for the service",
    )
    redis_config: RedisConfig = Field(
        default_factory=LocalRedisConfig,
        description="Redis configuration for the service",
    )
    ollama_config: OllamaConfig = Field(
        default_factory=LocalOllamaConfig,
        description="Ollama configuration for the service",
    )

    def get_buckets(self) -> Dict[str, BucketConfig]:
        """
        Get the list of buckets for the Rekuest service.
        This is used to retrieve the buckets that are configured for the Rekuest service.
        """
        return {"media": self.media_bucket}


class LovekitConfig(BaseServiceConfig):
    enabled: bool = Field(
        default=True, description="Whether the Lovekit service is enabled"
    )
    host: str = Field(default="lovekit", description="Host for the Lovekit service")
    github_repo: str = Field(
        default="https://github.com/arkitektio/lovekit-server",
        description="GitHub repository URL for the Lok service",
    )
    media_bucket: BucketConfig = Field(
        default_factory=LocalBucketConfig,
    )
    db_config: DBConfig = Field(
        default_factory=lambda: LocalDBConfig(db="lovekit"),
        description="Database configuration for the service",
    )
    redis_config: RedisConfig = Field(
        default_factory=LocalRedisConfig,
        description="Redis configuration for the service",
    )

    def get_buckets(self) -> Dict[str, BucketConfig]:
        """
        Get the list of buckets for the Rekuest service.
        This is used to retrieve the buckets that are configured for the Rekuest service.
        """
        return {"media": self.media_bucket}


class MikroConfig(BaseServiceConfig):
    enabled: bool = Field(
        default=True, description="Whether the Fluss service is enabled"
    )
    image: str = Field(
        default="jhnnsrs/mikro:dev",
        description="Docker image for the Rekuest service. This is used to run the Rekuest server",
    )
    host: str = Field(default="mikro", description="Host for the Fluss service")
    github_repo: str = Field(
        default="https://github.com/arkitektio/mikro-server-next",
        description="GitHub repository URL for the Lok service",
    )
    media_bucket: BucketConfig = Field(
        default_factory=LocalBucketConfig,
    )
    zarr_bucket: BucketConfig = Field(
        default_factory=LocalBucketConfig,
    )
    parquet_bucket: BucketConfig = Field(
        default_factory=LocalBucketConfig,
    )
    db_config: DBConfig = Field(
        default_factory=lambda: LocalDBConfig(db="mikro"),
        description="Database configuration for the service",
    )
    redis_config: RedisConfig = Field(
        default_factory=LocalRedisConfig,
        description="Redis configuration for the service",
    )

    def get_buckets(self) -> Dict[str, BucketConfig]:
        """
        Get the list of buckets for the Rekuest service.
        This is used to retrieve the buckets that are configured for the Rekuest service.
        """
        return {
            "zarr": self.zarr_bucket,
            "parquet": self.parquet_bucket,
            "media": self.media_bucket,
        }


class ElektroConfig(BaseServiceConfig):
    enabled: bool = Field(
        default=False, description="Whether the Fluss service is enabled"
    )
    image: str = Field(
        default="jhnnsrs/elektro:dev",
        description="Docker image for the Rekuest service. This is used to run the Rekuest server",
    )
    host: str = Field(default="elektro", description="Host for the Fluss service")
    github_repo: str = Field(
        default="https://github.com/arkitektio/elektro-server",
        description="GitHub repository URL for the Lok service",
    )
    media_bucket: BucketConfig = Field(
        default_factory=LocalBucketConfig,
    )
    db_config: DBConfig = Field(
        default_factory=lambda: LocalDBConfig(db="mikro"),
        description="Database configuration for the service",
    )
    redis_config: RedisConfig = Field(
        default_factory=LocalRedisConfig,
        description="Redis configuration for the service",
    )

    def get_buckets(self) -> Dict[str, BucketConfig]:
        """
        Get the list of buckets for the Rekuest service.
        This is used to retrieve the buckets that are configured for the Rekuest service.
        """
        return {"media": self.media_bucket}


class KraphConfig(BaseServiceConfig):
    enabled: bool = Field(
        default=True, description="Whether the Fluss service is enabled"
    )
    image: str = Field(
        default="jhnnsrs/kraph:dev",
        description="Docker image for the Rekuest service. This is used to run the Rekuest server",
    )
    host: str = Field(default="kraph", description="Host for the Fluss service")
    github_repo: str = Field(
        default="https://github.com/arkitektio/kraph-server",
        description="GitHub repository URL for the Lok service",
    )
    media_bucket: BucketConfig = Field(
        default_factory=LocalBucketConfig,
    )
    db_config: DBConfig = Field(
        default_factory=lambda: LocalDBConfig(db="kraph"),
        description="Database configuration for the service",
    )
    redis_config: RedisConfig = Field(
        default_factory=LocalRedisConfig,
        description="Redis configuration for the service",
    )

    def get_buckets(self) -> Dict[str, BucketConfig]:
        """
        Get the list of buckets for the Rekuest service.
        This is used to retrieve the buckets that are configured for the Rekuest service.
        """
        return {"media": self.media_bucket}


class DatenConfig(BaseServiceConfig):
    enabled: bool = Field(
        default=True, description="Whether the Daten service is enabled"
    )
    image: str = Field(
        default="jhnnsrs/daten:dev",
        description="Docker image for the Daten service. This is used to run the Daten server",
    )
    host: str = Field(default="daten", description="Host for the Daten service")
    postgres_user: str = Field(
        default="sleepyviolettarsier",
        description="PostgreSQL user for the Daten service",
    )
    postgres_password: str = Field(
        default="30ae0f6d873a75e6ca8d25f98033f849",
        description="PostgreSQL password for the Daten service",
    )
    github_repo: str = Field(
        default="https://github.com/arkitektio/daten-server",
        description="GitHub repository URL for the Lok service",
    )
    db_mount: str | None = Field(
        default="./db_data",
        description="Mount point for PostgreSQL database storage in the Daten service. If None, a volume will be created.",
    )


class DeployerConfig(BaseServiceConfig):
    host: str = Field(default="deployer", description="Host for the Deployer service")
    image: str = Field(
        default="jhnnsrs/deployer:dev",
        description="Docker image for the Deployer service. This is used to run the Deployer service",
    )
    enabled: bool = Field(
        default=True, description="Whether the Deployer service is enabled"
    )
    redeem_token: str = Field(
        default=secrets.token_hex(16),
        description="Redeem token for the Deployer service. This is used to authenticate requests to the Deployer service",
    )
    instance_id: str = Field(
        default="INTERNAL_DOCKER",
        description="Instance ID for the Deployer service. This is used to identify the instance of the Deployer service",
    )
    user: str = Field(
        default="deployer",
        description="User for the Deployer service. This is used to authenticate requests to the Deployer service",
    )


class RedisServiceConfig(BaseServiceConfig):
    host: str = Field(default="redis", description="Host for the Redis service")
    image: str = Field(
        default="redis:latest",
        description="Docker image for the Redis service. This is used to run the Redis server",
    )
    internal_port: int = Field(
        default=6379,
        description="Internal port for the Redis service. This is used to route requests to the Redis server",
    )
    enabled: bool = Field(
        default=True, description="Whether the Redis service is enabled"
    )


class GatewayConfig(BaseServiceConfig):
    enabled: bool = Field(
        default=True, description="Whether the Gateway service is enabled"
    )
    host: str = Field(default="gateway", description="Host for the Gateway service")
    image: str = Field(
        default="caddy:latest",
        description="Docker image for the Gateway service. This is used to run the Caddy server",
    )
    internal_port: int = Field(
        default=80,
        description="Internal port for the Gateway service. This is used to route requests to the appropriate service",
    )
    ssl: bool = Field(
        default=False,
        description="Whether to enable SSL for the Arkitekt server. If True, the server will run with HTTPS",
    )
    ssl_cert: str | None = Field(
        default=None,
        description="Path to the SSL certificate file. If None, the server will use lets encrypt",
    )
    auto_https: bool = Field(
        default=True,
        description="Whether to automatically force HTTPS for the Arkitekt server. If True, the server will redirect HTTP requests to HTTPS",
    )

    def get_gateway_path(self, service: BaseService) -> str:
        """
        Get the path for the service in the Gateway.
        This is used to configure the path for the service in the Gateway.
        """
        return service.host


class User(BaseModel):
    username: str = Field(
        default_factory=generate_name,
        description="Username for the user. If not provided, a random name will be generated",
    )
    password: str = Field(
        default_factory=generate_alpha_numeric_string,
        description="Password for the user. If not provided, a random password will be generated",
    )
    email: str | None = Field(
        default=None,
        description="Email for the user. If not provided, the user will not have an email",
    )
    roles: list[str] = Field(
        default_factory=lambda: [],
        description="List of groups for the user. This is used to manage user permissions and access",
    )
    active_organization: str = Field(
        default="arkitektio",
        description="Organization for the user. This is used to identify the organization that the user belongs to",
    )

    model_config = ConfigDict(
        extra="forbid",
    )


class Role(BaseModel):
    name: str = Field(
        description="Name of the group. If not provided, a random name will be generated",
    )
    description: str | None = Field(
        default=None,
        description="Description of the group. This is used to provide additional information about the group",
    )
    organization: str = Field(
        default="arkitektio",
        description="Organization for the group. This is used to identify the organization that the group belongs to",
    )
    identifier: str = Field(
        default_factory=generate_name,
        description="Identifier for the group. This is used to uniquely identify the group within the organization",
    )
    model_config = ConfigDict(
        extra="forbid",
    )


class Organization(BaseModel):
    name: str = Field(
        default_factory=generate_name,
        description="Name of the organization. If not provided, a random name will be generated",
    )
    description: str | None = Field(
        default=None,
        description="Description of the organization. This is used to provide additional information about the organization",
    )
    identifier: str = Field(
        default_factory=generate_name,
        description="Identifier for the organization. This is used to uniquely identify the organization",
    )
    model_config = ConfigDict(
        extra="forbid",
    )

    @property
    def bot_name(self) -> str:
        """
        Get the bot name for the organization.
        This is used to generate a unique name for the bot associated with the organization.
        """
        return f"{self.name}_bot"


def create_default_orgnization() -> Organization:
    """
    Create a default organization for the Arkitekt server.
    This is used to create a default organization that will be used by the Arkitekt server.
    """
    return Organization(
        name="arkitektio",
        description="Default organization for the Arkitekt server",
    )


class EmailConfig(BaseModel):
    host: str = Field(description="SMTP host for sending emails")
    port: int = Field(default=587, description="SMTP port for sending emails")
    username: str = Field(description="SMTP username for sending emails")
    password: str = Field(description="SMTP password for sending emails")
    email: str = Field(
        description="Email address to use as the sender for emails sent by the Arkitekt server"
    )
    model_config = ConfigDict(
        extra="forbid",
    )


class ArkitektServerConfig(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    port: int = Field(default=80, description="Port for http server")
    domain: str | None = Field(
        default=None,
        description="Domain for the Arkitekt server. If None, the server will run on localhost",
    )
    internal_network: str = Field(
        default_factory=generate_name,
        description="Internal network for the Arkitekt server. This is used to connect the services together",
    )
    email: EmailConfig | None = Field(
        default=None,
        description="Email configuration for the Arkitekt server. This is used to send emails from the Arkitekt server",
    )
    global_organization: str = Field(
        default="arkitektio",
        description="Global organization for the Arkitekt server. This is used to identify the organization that the Arkitekt server belongs to",
    )
    global_description: str | None = Field(
        default=None,
        description="Global description for the Arkitekt server. This is used to provide additional information about the Arkitekt server",
    )

    gateway: GatewayConfig = Field(
        default_factory=GatewayConfig,
        description="Configuration for the Gateway service",
    )
    csrf_trusted_origins: list[str] | None = Field(
        default=None,
        description="List of trusted origins for CSRF protection. This is used to prevent CSRF attacks by allowing only requests from trusted origins",
    )
    organizations: list[Organization] = Field(
        default_factory=lambda: [create_default_orgnization()],
        description="List of organizations for the Arkitekt server. This is used to manage organizations in the Arkitekt server",
    )

    users: list[User] = Field(
        default_factory=lambda: [],
        description="List of users for the Arkitekt server. This is used to manage users in the Arkitekt server",
    )
    roles: list[Role] = Field(
        default_factory=lambda: [],
        description="List of groups for the Arkitekt server. This is used to manage users in the Arkitekt server",
    )

    global_admin: str = Field(
        default="admin",
        description="Global admin username for the Arkitekt server",
    )
    global_admin_password: str = Field(
        default_factory=generate_name,
        description="Global admin password for the Arkitekt server",
    )
    global_admin_email: str | None = Field(
        default=None,
        description="Global admin email for the Arkitekt server",
    )
    deployer: DeployerConfig = Field(
        default_factory=DeployerConfig,
        description="Configuration for the Deployer service",
    )
    minio_mount: str | None = Field(
        default="/data",
        description="Mount point for MinIO data storage in the Arkitekt server (used for file storage). If None, a volume will be created.",
    )
    db_mount: str | None = Field(
        default="/db_data",
        description="Mount point for PostgreSQL database storage in the Arkitekt server. If None, a volume will be created.",
    )
    local_redis: RedisServiceConfig = Field(
        default_factory=RedisServiceConfig,
        description="A local Redis configuration for the Arkitekt server. Will only be used if a service requires a local Redis instance",
    )

    db: DatenConfig = Field(
        default_factory=DatenConfig,
        description="Configuration for the Daten service",
    )

    minio: MinioConfig = Field(
        default_factory=MinioConfig,
        description="Configuration for the MinIO service",
    )
    rekuest: RekuestConfig = Field(
        default_factory=RekuestConfig,
        description="Configuration for the Rekuest service",
    )
    lok: LokConfig = Field(
        default_factory=LokConfig,
        description="Configuration for the Lok service",
    )
    kabinet: KabinetConfig = Field(
        default_factory=KabinetConfig,
        description="Configuration for the Kabinet service",
    )
    fluss: FlussConfig = Field(
        default_factory=FlussConfig,
        description="Configuration for the Fluss service",
    )
    alpaka: AlpakaConfig = Field(
        default_factory=AlpakaConfig,
        description="Configuration for the Alpaka service",
    )
    mikro: MikroConfig = Field(
        default_factory=MikroConfig,
        description="Configuration for the Mikro service",
    )
    lovekit: LovekitConfig = Field(
        default_factory=LovekitConfig,
        description="Configuration for the Lovekit service",
    )
    elektro: ElektroConfig = Field(
        default_factory=ElektroConfig,
        description="Configuration for the Elektro service",
    )
    kraph: KraphConfig = Field(
        default_factory=KraphConfig,
        description="Configuration for the Kraph service",
    )
