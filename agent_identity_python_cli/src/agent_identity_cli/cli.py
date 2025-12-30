# -*- coding: utf-8 -*-
"""CLI entry point for Agent Identity Toolkit."""

import argparse
import json
import sys
from typing import List, Optional

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from Tea.exceptions import TeaException

from .core.deployer import create_role, create_workload_identity
from .core.models import (
    CreateRoleConfig,
    CreateRoleResult,
    CreateWorkloadIdentityConfig,
    CreateWorkloadIdentityResult,
)


def _parse_args() -> argparse.Namespace:
    """Parse command line arguments with subcommands."""
    parser = argparse.ArgumentParser(
        description="Agent Identity Toolkit CLI - Create RAM roles and "
        "workload identities for AI Agent identity management.",
    )
    
    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        description="Available commands",
        help="Use 'agent-identity-cli <command> --help' for more info",
    )
    
    # Subcommand: create-role
    role_parser = subparsers.add_parser(
        "create-role",
        help="Create a RAM role with Agent Identity trust policy",
    )
    role_parser.add_argument(
        "--role-name",
        dest="role_name",
        default=None,
        help="Name of the RAM role. Defaults to AgentIdentityRole-{workload-identity-name} "
        "or AgentIdentityRole-{random} if not specified.",
    )
    role_parser.add_argument(
        "--workload-identity-name",
        dest="workload_identity_name",
        default=None,
        help="Workload identity name for trust policy. "
        "If not specified, trust policy allows all workload identities.",
    )
    
    # Subcommand: create-workload-identity
    identity_parser = subparsers.add_parser(
        "create-workload-identity",
        help="Create a Workload Identity",
    )
    identity_parser.add_argument(
        "--workload-identity-name",
        dest="workload_identity_name",
        required=True,
        help="Name of the workload identity (required).",
    )
    identity_parser.add_argument(
        "--associated-role-arn",
        dest="associated_role_arn",
        default=None,
        help="ARN of the RAM role to associate. "
        "If not specified, a new role will be created automatically.",
    )
    identity_parser.add_argument(
        "--identity-provider-name",
        dest="identity_provider_name",
        default=None,
        help="Name of the identity provider (optional).",
    )
    identity_parser.add_argument(
        "--allowed-resource-oauth2-return-urls",
        dest="allowed_resource_oauth2_return_urls",
        default=None,
        help="Comma-separated list of allowed OAuth2 return URLs (optional).",
    )
    
    return parser.parse_args()


def _parse_urls(urls_str: Optional[str]) -> Optional[List[str]]:
    """Parse comma-separated URLs string to list."""
    if not urls_str:
        return None
    return [url.strip() for url in urls_str.split(",") if url.strip()]


def _print_role_result(result: CreateRoleResult, console: Console) -> None:
    """Print create-role result using rich formatting."""
    # Create info table
    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_column("Key", style="bold cyan")
    info_table.add_column("Value", style="white")
    
    info_table.add_row("Role Name", result.role_name)
    info_table.add_row("Role ARN", escape(result.role_arn))
    info_table.add_row("Policy Name", result.policy_name)
    
    console.print()
    console.print(
        Panel(
            info_table,
            title="[bold green]Create Role Result[/bold green]",
            title_align="center",
            expand=False,
            border_style="green",
        )
    )
    
    # Print trust policy
    console.print()
    console.print("[bold cyan]Trust Policy:[/bold cyan]")
    trust_json = json.dumps(result.trust_policy, indent=2, ensure_ascii=False)
    syntax = Syntax(trust_json, "json", theme="monokai", line_numbers=False)
    console.print(syntax)
    
    # Print permission policy
    console.print()
    console.print("[bold cyan]Permission Policy:[/bold cyan]")
    perm_json = json.dumps(result.permission_policy, indent=2, ensure_ascii=False)
    syntax = Syntax(perm_json, "json", theme="monokai", line_numbers=False)
    console.print(syntax)
    console.print()


def _print_workload_identity_result(
    result: CreateWorkloadIdentityResult,
    console: Console,
) -> None:
    """Print create-workload-identity result using rich formatting."""
    # Create info table
    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_column("Key", style="bold cyan")
    info_table.add_column("Value", style="white")
    
    info_table.add_row("Workload Identity Name", result.workload_identity_name)
    info_table.add_row("Workload Identity ARN", escape(result.workload_identity_arn))
    
    if result.role_result:
        info_table.add_row("", "")  # Spacer
        info_table.add_row("[bold]Created Role[/bold]", "")
        info_table.add_row("Role Name", result.role_result.role_name)
        info_table.add_row("Role ARN", escape(result.role_result.role_arn))
        info_table.add_row("Policy Name", result.role_result.policy_name)
    
    console.print()
    console.print(
        Panel(
            info_table,
            title="[bold green]Create Workload Identity Result[/bold green]",
            title_align="center",
            expand=False,
            border_style="green",
        )
    )
    
    # Print policies if role was created
    if result.role_result:
        console.print()
        console.print("[bold cyan]Trust Policy:[/bold cyan]")
        trust_json = json.dumps(
            result.role_result.trust_policy, indent=2, ensure_ascii=False
        )
        syntax = Syntax(trust_json, "json", theme="monokai", line_numbers=False)
        console.print(syntax)
        
        console.print()
        console.print("[bold cyan]Permission Policy:[/bold cyan]")
        perm_json = json.dumps(
            result.role_result.permission_policy, indent=2, ensure_ascii=False
        )
        syntax = Syntax(perm_json, "json", theme="monokai", line_numbers=False)
        console.print(syntax)
    
    console.print()


def _print_error(error: Exception, console: Console) -> None:
    """Print error message using rich formatting."""
    # Format error message based on exception type
    if isinstance(error, TeaException):
        message = f"{error.code}: {error.message}"
    else:
        message = str(error)
    
    console.print()
    console.print(
        Panel(
            f"[bold red]Error:[/bold red] {message}",
            title="[bold red]Command Failed[/bold red]",
            title_align="center",
            expand=False,
            border_style="red",
        )
    )
    console.print()


def main() -> None:
    """Main entry point for CLI."""
    console = Console(emoji=False)
    
    try:
        args = _parse_args()
        
        if not args.command:
            console.print("[yellow]Please specify a command. Use --help for usage.[/yellow]")
            sys.exit(1)
        
        if args.command == "create-role":
            console.print("[cyan]Creating RAM role...[/cyan]")
            
            config = CreateRoleConfig(
                role_name=args.role_name,
                workload_identity_name=args.workload_identity_name,
            )
            result = create_role(config)
            _print_role_result(result, console)
            
        elif args.command == "create-workload-identity":
            console.print("[cyan]Creating Workload Identity...[/cyan]")
            
            config = CreateWorkloadIdentityConfig(
                workload_identity_name=args.workload_identity_name,
                associated_role_arn=args.associated_role_arn,
                identity_provider_name=args.identity_provider_name,
                allowed_resource_oauth2_return_urls=_parse_urls(
                    args.allowed_resource_oauth2_return_urls
                ),
            )
            result = create_workload_identity(config)
            _print_workload_identity_result(result, console)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        sys.exit(1)
    except Exception as e:
        _print_error(e, console)
        sys.exit(1)


if __name__ == "__main__":
    main()
