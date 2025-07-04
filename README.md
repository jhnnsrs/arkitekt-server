# Arkitekt Server

A command-line tool for deploying and managing an Arkitekt server deployments. Arkitekt Server provides a comprehensive platform for scientific computing and data management, with built-in support for authentication, task orchestration, data storage, and containerized application deployment.

## Overview

Arkitekt Server is a deployment configuration management tool that simplifies the setup and management of the Arkitekt ecosystem. It generates Docker Compose configurations and handles the complex orchestration of multiple services including databases, message queues, object storage, and various scientific computing services.

## Requirements

- Python 3.12+
- Docker and Docker Compose
- Git (for development mode with repository mounting)

## Running

```bash
uvx arkitekt-server init default
```

This command initializes a new Arkitekt Server deployment with a default configuration. You can also specify different configurations such as `dev` for development mode or `minimal` for a lightweight setup.

### Non-UVX Usage

If you prefer not to use UVX, you can run the tool directly with:

```bash
pip install arkitekt-server
arkitekt-server init default
```

## Key Features

- **One-Command Deployment**: Generate complete Docker Compose configurations with sensible defaults
- **Service Deployment**: Deploy and manage multiple interconnected services
- **Authentication & Authorization**: Built-in user management with JWT-based authentication
- **Development Mode**: Hot-reload support for development with GitHub repository mounting (when available)

## Core Services

The Arkitekt ecosystem includes several specialized services:

- **Lok**: Authentication and authorization service with JWT token management
- **Rekuest**: Task orchestration and workflow management
- **Mikro**: Image and microscopy data management
- **Kabinet**: Container and application registry
- **Fluss**: Workflow execution engine
- **Kraph**: Knowledge graph and metadata management
- **Elektro**: Event streaming and notifications
- **Alpaka**: AI/ML model management with Ollama integration

## Quick Start

### Initialize a new deployment

```bash
# Create a default configuration
arkitekt-server init default

# Create a development configuration with GitHub mounting
arkitekt-server init dev

# Create a minimal configuration
arkitekt-server init minimal
```

### Configure services

```bash
# Enable/disable specific services
arkitekt-server service rekuest --enable
arkitekt-server service mikro --enable
arkitekt-server service kabinet --enable
```

### Manage users

```bash
# Add a new user
arkitekt-server auth user add
```

Allows you to add a new user with options for username, email, and password.


### Deploy

When ready to deploy, run:

```bash
# Generate Docker Compose files and deploy
arkitekt-server build docker
```

This command generates the necessary Docker Compose files based on your configuration and starts the services.

### Start the services

```bash
docker compose up
```

This command starts all the services defined in the generated Docker Compose files, wait for the services to be up and running, and then you can access the 
deployment though the orkestrator interface.


## Configuration

The tool generates and manages a `arkitekt_server_config.yaml` file that contains all deployment settings. This file includes:

- Service configurations and Docker images
- Database and Redis settings
- Object storage (MinIO) configuration
- Authentication keys and secrets
- User and group management
- Network and routing configuration

This file can be customized to suit your deployment needs, allowing you to specify local or remote databases, shared or dedicated storage buckets, and development or production deployment modes. This config-file is the central point for managing your Arkitekt Server deployment. And it is automatically generated based on the services you enable and the options you choose during initialization.

## Architecture

Arkitekt Server uses a self-container-service architecture with:

- **PostgreSQL**: Primary database for all services
- **Redis**: Message queuing and caching
- **MinIO**: S3-compatible object storage
- **Caddy**: Reverse proxy and gateway
- **Docker**: Container orchestration

Each service can be configured independently with options for:
- Local or remote databases
- Shared or dedicated storage buckets
- Development or production deployment modes
- Custom authentication configurations

## Development

For development workflows, the tool supports:

- GitHub repository mounting for live code reloading
- Debug mode with detailed logging
- Separate development configurations
- Hot-swappable service configurations



## License

MIT License
