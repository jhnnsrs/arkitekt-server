from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich.align import Align
import click
import inquirer
from .utils import safe_org_slug
from .logo import ASCI_LOGO
from .config import ArkitektServerConfig, Organization, EmailConfig, User
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

    organizations = []

    if click.confirm("Would you like to define custom organizations?", default=True):
        while True:
            org_name = click.prompt(
                "Enter the organization name (max 8 characters)",
                default=generate_name(),
            )

            okay_slug = False

            while not okay_slug:
                org_slug = click.prompt(
                    "Enter the organization slug (max 8 characters)",
                    default=safe_org_slug(org_name.lower()),
                )
                if len(org_slug) <= 8:
                    if org_slug.isalnum() and org_slug.islower():
                        okay_slug = True

                else:
                    console.print(
                        "[bold red]⚠️ Organization slug must be max 8 characters.[/bold red]"
                    )

            console.print(
                "[bold red]⚠️ Organization name must be slug-safe and max 8 characters.[/bold red]"
            )

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
        org_choice = inquirer.prompt(
            [
                inquirer.List(
                    "organization",
                    message="Select the organization this user belongs to",
                    choices=[o.name for o in config.organizations],
                )
            ]
        )

        org_slug = org_choice["organization"]

        role_choies = [f"{org_slug}:{slug}" for slug in ["admin", "user"]]

        # Select roles
        role_choice = inquirer.prompt(
            [
                inquirer.Checkbox(
                    "roles",
                    message="Select the roles for this user",
                    choices=role_choies,
                    default=role_choies,
                )
            ]
        )

        if not role_choice or "roles" not in role_choice:
            console.print(
                "[bold yellow]⚠️ No roles selected, defaulting to 'user'.[/bold yellow]"
            )
            role_choice = {"roles": ["user"]}

        config.users.append(
            User(
                username=username,
                password=password,
                email=email or None,
                active_organization=org_slug,
                roles=role_choice["roles"],
            )
        )

        if not click.confirm("Add another user?", default=False):
            break

    for org in config.organizations:
        # Add a bot user for each organization
        config.users.append(
            User(
                username=org.bot_name,
                password=generate_alpha_numeric_string(12),
                email=None,
                active_organization=org.name,
                roles=[f"{org.name}:bot"],
            )
        )

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
