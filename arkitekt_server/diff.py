import difflib
import tempfile
from pathlib import Path
from typing import Any, Dict

from pydantic import BaseModel
import typer
from .config import (
    ArkitektServerConfig,
    BaseService,
    LocalDBConfig,
    RemoteDBConfig,
    GlobalAdminConfig,
    SpecificAdminConfig,
    LocalRedisConfig,
    LocalBucketConfig,
    LocalAuthConfig,
    RemoteRedisConfig,
    StatikTokenAuthConfig,
    LocalPath,
    ForcePath,
)
import yaml


def iterate_service(config: ArkitektServerConfig) -> list[BaseService]:
    """Iterate over the services in the configuration."""
    all_services = [
        config.rekuest,
        config.kabinet,
        config.mikro,
        config.fluss,
        config.elektro,
        config.lok,
        config.alpaka,
        config.kraph,
    ]

    services = []
    for service in all_services:
        if isinstance(service, BaseService):
            if service.enabled:
                services.append(service)
        else:
            raise TypeError(
                f"Expected BaseServiceConfig, got {type(service).__name__} instead."
            )

    return services


def create_basic_config_values(
    config: ArkitektServerConfig, service: BaseService
) -> Dict[str, Any]:
    db = None
    if isinstance(service.db_config, LocalDBConfig):
        db = {
            "db_name": service.db_config.db,
            "engine": "django.db.backends.postgresql",
            "host": "db",
            "password": config.db.postgres_password,
            "port": 5432,
            "username": config.db.postgres_user,
        }
    elif isinstance(service.db_config, RemoteDBConfig):
        db = {
            "db_name": service.db_config.db,
            "engine": "django.db.backends.postgresql",
            "host": service.db_config.host,
            "password": service.db_config.password,
            "port": service.db_config.port,
            "username": service.db_config.user,
        }

    django_admin = None
    if isinstance(service.admin_config, GlobalAdminConfig):
        django_admin = {
            "email": config.global_admin_email,
            "password": config.global_admin_password,
            "username": config.global_admin,
        }
    elif isinstance(service.admin_config, SpecificAdminConfig):
        django_admin = {
            "email": service.admin_config.email,
            "password": service.admin_config.password,
            "username": service.admin_config.username,
        }

    redis = None
    if isinstance(service.redis_config, LocalRedisConfig):
        redis = {
            "host": config.local_redis.host,
            "port": config.local_redis.internal_port,
        }
    elif isinstance(service.redis_config, RemoteRedisConfig):
        redis = {
            "host": service.redis_config.host,
            "port": service.redis_config.port,
        }
    else:
        raise TypeError(
            f"Expected LocalRedisConfig or RemoteRedisConfig, got {type(service.redis_config).__name__} instead."
        )

    script_name = service.host
    config_values = {
        "csrf_trusted_origins": [],
        "db": db,
        "django": {
            "admin": django_admin,
            "debug": service.debug,
            "hosts": service.allowed_hosts,
            "secret_key": service.secret_key,
        },
        "lok": {
            "issuer": config.lok.issuer,
            "key_type": config.lok.auth_key_pair.key_type,
            "public_key": config.lok.auth_key_pair.public_key,
        },
        "force_script_name": script_name,
        "redis": redis,
        "s3": {
            "access_key": config.minio.access_key,
            "secret_key": config.minio.secret_key,
            "buckets": {
                key: config.bucket_name for key, config in service.get_buckets().items()
            },
            "host": config.minio.host,
            "port": config.minio.internal_port,
            "protocol": "http",
        },
    }
    return config_values


def create_config(
    service_name: str, config_values: Dict[str, Any], base_path: Path
) -> None:
    """Create a service configuration dictionary."""
    service_dir = base_path / "configs"
    service_dir.mkdir(parents=True, exist_ok=True)

    (service_dir / f"{service_name}.yaml").write_text(
        yaml.dump(config_values, default_flow_style=False)
    )


def build_default_service(
    config: ArkitektServerConfig, service: BaseService
) -> dict[str, Any]:
    return {
        "image": service.image,
        "command": service.build_run_command(),
        "depends_on": ["redis", "db", "minio"],
        "volumes": [f"./configs/{service.host}.yaml:/workspace/config.yaml"],
    }


def create_fluss_config(config: ArkitektServerConfig, base_path: Path) -> None:
    """Create the Fluss configuration file."""
    fluss_config = create_basic_config_values(config, config.fluss)
    create_config("fluss", fluss_config, base_path)


def create_lok_config(config: ArkitektServerConfig, base_path: Path) -> None:
    """Create the Fluss configuration file."""

    lok_config = create_basic_config_values(config, config.lok)

    create_config("lok", lok_config, base_path)


def parse_local_db_requests(config: ArkitektServerConfig) -> list[LocalDBConfig]:
    """Parse the database names from the configuration."""
    db_names = []
    for service in iterate_service(config):
        if isinstance(service.db_config, LocalDBConfig):
            db_names.append(service.db_config)
    return db_names


def parse_local_auth_requests(config: ArkitektServerConfig) -> list[LocalAuthConfig]:
    """Parse the database names from the configuration."""
    db_names = []
    for service in iterate_service(config):
        if isinstance(service.db_config, LocalDBConfig):
            db_names.append(service.db_config)
    return db_names


def parse_local_redis_request(config: ArkitektServerConfig) -> list[LocalRedisConfig]:
    """Parse the Redis database names from the configuration."""
    redis_dbs = []
    for service in iterate_service(config):
        if isinstance(service.redis_config, LocalRedisConfig):
            redis_dbs.append(service.redis_config)
    return redis_dbs


def parse_local_bucket_configs(config: ArkitektServerConfig) -> list[LocalBucketConfig]:
    """Parse the bucket names from the configuration."""
    bucket_names = []
    for service in iterate_service(config):
        buckets = service.get_buckets()
        if isinstance(buckets, dict):
            for bucket_name, bucket_config in buckets.items():
                if isinstance(bucket_config, LocalBucketConfig):
                    bucket_names.append(bucket_config)
    return bucket_names


def create_caddyfilepath(service: BaseService) -> str:
    caddyfile = f"\t@{service.host} path /{service.host}*\n"
    caddyfile += "\thandle @" + service.host + " { \n"
    caddyfile += f"\t\treverse_proxy {service.host}:{service.internal_port}\n"
    caddyfile += "\t}\n\n"
    return caddyfile


def create_caddy_file(config: ArkitektServerConfig) -> str:
    """Create a Caddyfile for the service."""

    caddyfile = "http:// {\n"

    for service in iterate_service(config):
        if not isinstance(service, BaseService):
            raise TypeError(
                f"Expected BaseServiceConfig, got {type(service).__name__} instead."
            )
        caddyfile += f"\t@{service.host} path /{service.host}*\n"
        caddyfile += "\thandle @" + service.host + " { \n"
        caddyfile += f"\t\treverse_proxy {service.host}:{service.internal_port}\n"
        caddyfile += "\t}\n\n"

    for bucket in parse_local_bucket_configs(config):
        caddyfile += f"\t@{bucket.bucket_name} path /{bucket.bucket_name}*\n"
        caddyfile += "\thandle @" + bucket.bucket_name + " { \n"
        caddyfile += (
            f"\t\treverse_proxy {config.minio.host}:{config.minio.internal_port}\n"
        )
        caddyfile += "\t}\n\n"

    caddyfile += "\t@.well-known path /.well-known/*\n"
    caddyfile += "\thandle @.well-known {\n"
    caddyfile += "\t\trewrite * /lok{uri}\n"
    caddyfile += f"\t\treverse_proxy {service.host}:{service.internal_port}\n"
    caddyfile += "\t}\n\n"

    caddyfile += "}\n"
    return caddyfile


class AliasConfig(BaseModel):
    challenge: str
    kind: str
    layer: str
    path: str


class InstanceConfig(BaseModel):
    service: str
    identifier: str
    alias: list[AliasConfig] = []


class RedeemTokenConfig(BaseModel):
    token: str
    user: str


def service_to_instance_config(
    service: BaseService, service_name: str
) -> InstanceConfig:
    """Convert a service to an instance configuration."""
    return InstanceConfig(
        service=service_name,
        identifier=service.host,
        alias=[
            AliasConfig(challenge="ht", kind="http", layer="public", path=service.host)
        ],
    )


def write_virtual_config_files(tmpdir: Path, config: ArkitektServerConfig):
    """Generate expected config files into the temp dir."""

    services = {}

    instances = []
    redeem_tokens = []

    local_dbs = parse_local_db_requests(config)
    if len(local_dbs) > 1:
        services["db"] = {
            "image": config.db.image,
            "environment": {
                "POSTGRES_MULTIPLE_DATABASES": ",".join(
                    [request.db for request in local_dbs]
                ),
                "POSTGRES_PASSWORD": config.db.postgres_password,
                "POSTGRES_USER": config.db.postgres_user,
            },
            "volumes": [f"{config.db.db_mount}:/var/lib/postgresql/data"],
        }

    local_redis_requests = parse_local_redis_request(config)
    if len(local_redis_requests) > 1:
        services[config.local_redis.host] = {
            "image": config.local_redis.image,
        }

    local_bucket_requests = parse_local_bucket_configs(config)
    if len(local_bucket_requests) > 1:
        services[config.minio.host] = {
            "image": config.minio.image,
            "command": "server /data",
            "environment": {
                "MINIO_ROOT_USER": config.minio.root_user,
                "MINIO_ROOT_PASSWORD": config.minio.root_password,
            },
            "volumes": ["./data:/data"],
        }

        gconfig = {
            "buckets": [{"name": req.bucket_name} for req in local_bucket_requests],
            "users": [
                {
                    "access_key": config.minio.access_key,
                    "secret_key": config.minio.secret_key,
                    "policy": "readwrite",
                    "name": "Default User",
                }
            ],
        }

        create_config(config.minio.init_container_host, gconfig, tmpdir)
        # We also need to create the init container for MinIO
        services[config.minio.init_container_host] = {
            "image": config.minio.init_container_image,
            "volumes": ["./configs/minio-init.yaml:/workspace/config.yaml"],
            "environment": {
                "MINIO_ROOT_USER": config.minio.root_user,
                "MINIO_ROOT_PASSWORD": config.minio.root_password,
                "MINIO_HOST": config.minio.host,
            },
            "depends_on": {config.minio.host: {"condition": "service_started"}},
        }

    if config.deployer.enabled:
        services[config.deployer.host] = {
            "image": config.deployer.image,
            "volumes": ["/var/run/docker.sock:/var/run/docker.sock"],
            "command": (
                f"arkitekt-next run prod --redeem-token={config.deployer.redeem_token} "
                f"--url http://{config.gateway.host}:{config.gateway.internal_port}"
            ),
            "deploy": {
                "restart_policy": {
                    "condition": "on-failure",
                    "delay": "10s",
                    "max_attempts": 10,
                    "window": "300s",
                }
            },
            "environment": {
                "ARKITEKT_GATEWAY": f"http://{config.gateway.host}:{config.gateway.internal_port}",
                "ARKITEKT_NETWORK": config.internal_network,
                "INSTANCE_ID": config.deployer.instance_id,
            },
        }

        redeem_tokens.append(
            RedeemTokenConfig(
                token=config.deployer.redeem_token, user=config.deployer.user
            )
        )

    if config.fluss.enabled:
        services[config.fluss.host] = build_default_service(config, config.fluss)

        gconfig = create_basic_config_values(config, config.fluss)
        create_config(config.fluss.host, gconfig, tmpdir)
        instances.append(
            service_to_instance_config(config.fluss, "arkitekt.live.fluss")
        )

    if config.kabinet.enabled:
        services[config.kabinet.host] = build_default_service(config, config.kabinet)

        gconfig = create_basic_config_values(config, config.kabinet)
        create_config(config.kabinet.host, gconfig, tmpdir)
        instances.append(
            service_to_instance_config(config.kabinet, "arkitekt.live.kabinet")
        )

    if config.elektro.enabled:
        services[config.elektro.host] = build_default_service(config, config.elektro)

        gconfig = create_basic_config_values(config, config.elektro)
        create_config(config.elektro.host, gconfig, tmpdir)
        instances.append(
            service_to_instance_config(config.elektro, "arkitekt.live.elektro")
        )

    if config.kraph.enabled:
        services[config.kraph.host] = build_default_service(config, config.kraph)

        gconfig = create_basic_config_values(config, config.kraph)
        create_config(config.kraph.host, gconfig, tmpdir)
        instances.append(
            service_to_instance_config(config.kraph, "arkitekt.live.kraph")
        )

    if config.alpaka.enabled:
        services[config.alpaka.host] = build_default_service(config, config.alpaka)

        lok_config = create_basic_config_values(config, config.alpaka)
        create_config(config.alpaka.host, lok_config, tmpdir)
        instances.append(
            service_to_instance_config(config.alpaka, "arkitekt.live.alpaka")
        )

    if config.mikro.enabled:
        services[config.mikro.host] = build_default_service(config, config.mikro)

        lok_config = create_basic_config_values(config, config.mikro)
        create_config(config.mikro.host, lok_config, tmpdir)
        instances.append(
            service_to_instance_config(config.mikro, "arkitekt.live.mikro")
        )

    if config.rekuest.enabled:
        services[config.rekuest.host] = build_default_service(config, config.rekuest)

        lok_config = create_basic_config_values(config, config.rekuest)
        create_config(config.rekuest.host, lok_config, tmpdir)
        instances.append(
            service_to_instance_config(config.rekuest, "arkitekt.live.rekuest")
        )

    services["caddy"] = {
        "image": "caddy:latest",
        "ports": ["80:80"],
        "networks": [config.internal_network, "default"],
        "volumes": ["./configs/Caddyfile:/etc/caddy/Caddyfile"],
    }

    caddyfile = create_caddy_file(config)
    mkkdirs = tmpdir / "configs"
    mkkdirs.mkdir(parents=True, exist_ok=True)
    (tmpdir / "configs" / "Caddyfile").write_text(caddyfile)

    # Create Lok service configuration
    services[config.lok.host] = {
        "command": config.lok.build_run_command(),
        "image": config.lok.image,
        "volumes": [f"./configs/{config.lok.host}.yaml:/workspace/config.yaml"],
        "deploy": {
            "restart_policy": {
                "condition": "on-failure",
                "delay": "10s",
                "max_attempts": 10,
                "window": "300s",
            }
        },
    }

    gconfig = create_basic_config_values(config, config.lok)

    users = []
    groups = []

    for user in config.users:
        users.append(
            {
                "username": user.username,
                "password": user.password,
                "email": user.email,
            }
        )

    for group in config.groups:
        groups.append(
            {
                "name": group.name,
                "description": group.description,
            }
        )

    gconfig["deployment"] = {"name": "test"}
    gconfig["email"] = {
        "host": config.email.host if config.email else "NOT_SET",
        "port": config.email.port if config.email else 587,
        "user": config.email.username if config.email else "NOT_SET",
        "password": config.email.password if config.email else "NOT_SET",
        "email": config.email.email if config.email else "NOT_SET",
    }
    gconfig["private_key"] = config.lok.auth_key_pair.private_key
    gconfig["public_key"] = config.lok.auth_key_pair.public_key
    gconfig["redeem_tokens"] = [instance.model_dump() for instance in redeem_tokens]

    gconfig["scopes"] = {
        "kabinet_add_repo": "Add repositories to the database",
        "kabinet_deploy": "Deploy containers",
        "mikro_read": "Read image from the database",
        "mikro_write": "Write image to the database",
        "openid": "The open id connect scope",
        "read": "A generic read access",
        "read_image": "Read image from the database",
        "rekuest_agent": "Act as an agent",
        "rekuest_call": "Call other apps with rekuest",
        "write": "A generic write access",
    }
    gconfig["token_expire_seconds"] = 800000
    gconfig["users"] = users
    gconfig["groups"] = groups
    gconfig["instances"] = [instance.model_dump() for instance in instances]

    create_config(config.lok.host, gconfig, tmpdir)

    docker_compose_content = {
        "services": services,
        "networks": {
            config.internal_network: {
                "driver": "bridge",
                "name": config.internal_network,
            }
        },
    }

    (tmpdir / "docker-compose.yaml").write_text(
        yaml.dump(docker_compose_content, default_flow_style=False)
    )
    (tmpdir / "README.md").write_text("# Example Config\nAuto-generated by script.\n")


def collect_all_files(base: Path) -> dict:
    """Return all files in a directory tree relative to the base path."""
    files = {}
    for path in base.rglob("*"):
        if path.is_file():
            relative_path = path.relative_to(base)
            files[relative_path] = path
    return files


def compare_filesystems(
    virtual_dir: Path, real_dir: Path, *, allow_deletes: bool = True
):
    """Compare the virtual and real directory structures and print diffs."""
    virtual_files = collect_all_files(virtual_dir)
    real_files = collect_all_files(real_dir)

    all_paths = sorted(set(virtual_files) | set(real_files))

    for path in all_paths:
        v_file = virtual_files.get(path)
        r_file = real_files.get(path)

        if v_file and not r_file:
            print(f"[+] Would create: {path}")
        elif not v_file and r_file:
            if allow_deletes:
                print(f"[-] Would delete: {path}")
        elif v_file and r_file:
            v_lines = v_file.read_text().splitlines(keepends=True)
            r_lines = r_file.read_text().splitlines(keepends=True)

            if v_lines != r_lines:
                diff = list(
                    difflib.unified_diff(
                        r_lines,
                        v_lines,
                        fromfile=f"{path} (current)",
                        tofile=f"{path} (new)",
                        lineterm="",
                    )
                )
                print(f"[~] Would modify: {path}")
                print("".join(diff))


def run_dry_run_diff(
    config: ArkitektServerConfig, real_dir: Path, allow_deletes: bool = False
):
    """Main logic to run the dry-run config comparison."""

    with tempfile.TemporaryDirectory() as tmp:
        virtual_dir = Path(tmp)
        print(f"🛠  Generating virtual config in: {virtual_dir}")
        write_virtual_config_files(virtual_dir, config)

        print(f"\n🔍 Comparing to real directory: {real_dir}\n")
        compare_filesystems(virtual_dir, real_dir, allow_deletes=allow_deletes)

        typer.confirm(
            "Do you want to apply these changes?",
            abort=True,
        )

        # copy the virtual files to the real directory
        for path in virtual_dir.rglob("*"):
            if path.is_file():
                relative_path = path.relative_to(virtual_dir)
                target_path = real_dir / relative_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, "r") as src_file:
                    with open(target_path, "w") as dst_file:
                        dst_file.write(src_file.read())
