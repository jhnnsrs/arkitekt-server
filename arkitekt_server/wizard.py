from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich.align import Align
import click
import inquirer
from .utils import safe_org_slug
from .logo import ASCI_LOGO
from .config import ArkitektServerConfig, Organization, EmailConfig, User, Membership
from .config import generate_name, generate_alpha_numeric_string

console = Console()


def prompt_config(console: Console) -> ArkitektServerConfig:
    config = ArkitektServerConfig()

    # Welcome
    console.print(
        Panel(
            Align.center(
                Text(
                    ASCI_LOGO,
                    style="bold cyan",
                )
            ),
            title="",
            border_style="cyan",
            expand=True,
            subtitle=Text(
                "Welcome to the Arkitekt Server Setup Wizard",
                style="bold cyan",
            ),
        )
    )

    console.print(
        Panel(
            Markdown("""
This wizard will guide you through setting up your **Arkitekt Server**.

Arkitekt is a multi-tenant server designed to manage data and workflows for various labs, institutions, or projects.
As such, it supports multiple organizations, users, and roles.

You will configure:
- A **global admin** account to manage server settings
- One or more **organizations** (e.g. `openuc2`, `anatlab`)
- **Users** who can access the server, each belonging to an organization
- Optional **email support** for notifications (experimental)

🔐 First, you'll configure the global admin — the account that manages the server settings.
            """),
            border_style="cyan",
            expand=True,
        )
    )

    config.global_admin = click.prompt(
        "Enter the global admin username", default="admin"
    )
    config.global_admin_password = click.prompt(
        "Enter the global admin password", hide_input=True
    )

    # Organization setup
    console.print(
        Panel(
            Markdown("""
### Organizations

Lets configure the organizations that will use twith this Arkitekt server.

You can define:
- A **single global organization**, or
- **Multiple named organizations** (e.g. `openuc2`, `anatlab`)

Users ca belong to multiple organizations, and each organization can specify its own roles 
which will be used to manage permissions and access control. Some common roles include:

- `admin`: Full access to manage the organization
- `user`: Regular user with limited permissions
- `bot`: Automated processes or services that interact with the organization

You can define custom organizations here, or use a single global organization.
"""),
            title="🔧 Organization Setup",
            border_style="magenta",
            expand=True,
        )
    )

    organizations: list[Organization] = []

    if click.confirm("Would you like to define custom organizations?", default=True):
        while True:
            org_name = click.prompt(
                "Enter the organization name (max 8 characters)",
                default=generate_name(),
            )

            org_slug = None

            while org_slug is None:
                org_slug = click.prompt(
                    "Enter the organization slug (max 8 characters)",
                    default=safe_org_slug(org_name.lower()),
                )
                if len(org_slug) > 12:
                    org_slug = None
                    console.print(
                        "[bold red]⚠️ Organization slug must be max 12 characters.[/bold red]"
                    )
                    continue

                if org_slug != safe_org_slug(org_slug):
                    org_slug = None
                    console.print(
                        "[bold red]⚠️ Organization slug must be alphanumeric and _[/bold red]"
                    )
                    continue

            org_description = click.prompt(
                "Enter a short description",
                default="This is a sample organization for the Arkitekt server.",
            )

            organizations.append(
                Organization(
                    name=org_name, description=org_description, identifier=org_slug
                )
            )

            if not click.confirm("Add another organization?"):
                break
    else:
        console.print("[yellow]Using a single global organization.[/yellow]")
        organizations.append(
            Organization(
                name="global",
                description="This is the global organization for the Arkitekt server.",
                identifier="global",
            )
        )

    config.organizations = organizations
    config.users = []

    # Email support
    console.print(
        Panel(
            Markdown("""
### Email Support (Experimental)

You can enable email notifications (e.g. for password resets or invites) via an SMTP server.

This is optional and can be skipped if you're running locally or without email features.
"""),
            title="📧 Email Setup",
            border_style="blue",
            expand=True,
        )
    )

    if click.confirm("Would you like to enable email support?", default=False):
        host = click.prompt("SMTP host", default="smtp.example.com")
        port = click.prompt("SMTP port", type=int, default=587)
        username = click.prompt("SMTP username", default="")
        password = click.prompt("SMTP password", hide_input=True, default="")
        email = click.prompt("Sender email address", default="noreply@example.com")

        config.email = EmailConfig(
            host=host,
            port=port,
            username=username,
            password=password,
            email=email,
        )

    # User setup
    console.print(
        Panel(
            Markdown("""
### User Setup

Now you can define users who can access the Arkitekt services.

Each user:
- Belongs to one organization
- Has one or more roles (`admin`, `user`) in that organization

The **global admin** you defined earlier is not included here — these are standard users.

Attention: We will autogenerate a Bot user for you for some arkitekt internal services, which will be used for automated tasks and 
background processes. This user will have the `bot` role in all organizations.
"""),
            title="👤 Users",
            border_style="green",
            expand=True,
        )
    )

    while True:
        username = click.prompt("Enter the username")
        password = click.prompt("Enter the password", hide_input=True)
        email = click.prompt("Enter the email (optional)", default="")

        # Select organization
        org_choice: dict[str, list[str]] = inquirer.prompt(  # type: ignore
            [
                inquirer.Checkbox(
                    "organizations",
                    message="Select the organizations this user belongs to",
                    choices=[o.identifier for o in config.organizations],
                    default=[[o.identifier for o in config.organizations][0]],
                )
            ]
        )
        if not org_choice:
            console.print(
                "[bold red]⚠️ No organization selected, please select at least one organization.[/bold red]"
            )
            continue

        org_choices: list[str] = org_choice.get("organizations", []) or []
        if not org_choices:
            console.print(
                "[bold red]⚠️ No organization selected, please select at least one organization.[/bold red]"
            )
            continue

        memberships: list[Membership] = []

        for org in org_choices:
            memberships.append(Membership(organization=org, roles=[]))
            roles: list[str] = []

            while not roles:
                role_choices = [
                    slug for slug in ["admin", "user", "bot", "viewer", "editor"]
                ]

                # Select roles
                inquisition: dict[str, list[str]] = inquirer.prompt(  # type: ignore
                    [
                        inquirer.Checkbox(
                            "roles",
                            message=f"Select the roles for this user within the {org} organization",
                            choices=role_choices,
                            default=[role_choices[0]],
                        )
                    ]
                )

                roles: list[str] = inquisition.get("roles", [])
                if not roles:
                    console.print(
                        "[bold red]⚠️ No roles selected, please select at least one role.[/bold red]"
                    )
                    continue

            memberships.append(
                Membership(
                    organization=org,
                    roles=roles,
                )
            )

        # Select organization
        org_choice: dict[str, str] = inquirer.prompt(  # type: ignore
            [
                inquirer.List(
                    "organization",
                    message="Select the active organization for this user",
                    choices=[o for o in org_choices],
                    default=[o for o in org_choices][0],
                )
            ]
        )

        config.users.append(
            User(
                username=username,
                password=password,
                email=email or None,
                active_organization=org_choice.get("organization", org_choices[0]),
                memberships=memberships,
            )
        )

        print("Added user:", username)

        if not click.confirm("Add another user?", default=False):
            break

    # Final message
    console.print(
        Panel(
            Align.center(
                Text("✔️ Arkitekt configuration complete!", style="bold green")
            ),
            border_style="green",
            expand=True,
        )
    )

    return config
