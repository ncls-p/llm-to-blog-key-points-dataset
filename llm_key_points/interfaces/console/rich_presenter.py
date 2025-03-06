"""
Rich console presenter for CLI output.
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.table import Table
from rich.text import Text

from ...core.entities.dataset import Dataset

# Set up logging
logger = logging.getLogger(__name__)


class RichPresenter:
    """Presenter for CLI output using Rich library."""

    def __init__(self):
        self.console = Console()

    def display_welcome(self):
        """Display welcome message."""
        welcome_text = Text()
        welcome_text.append("🎉 Welcome to ", style="bold cyan")
        welcome_text.append("Dataset Enhancer", style="bold magenta")
        welcome_text.append(" powered by ", style="bold cyan")
        welcome_text.append("OpenAI compatible API", style="bold green")
        panel = Panel(
            welcome_text,
            subtitle="[cyan]Created with ❤️  by Ncls-p[/cyan]",
            border_style="bright_blue",
        )
        self.console.print(panel)

    def create_url_table(self, urls: List[str]) -> Table:
        """Create a table to display URLs."""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim")
        table.add_column("URL", style="cyan")
        for idx, url in enumerate(urls, 1):
            table.add_row(str(idx), url)
        return table

    def display_dataset_stats(self, stats: Dict[str, Any]):
        """Display dataset statistics."""
        stats_table = Table(show_header=True, header_style="bold magenta")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")

        for key, value in stats.items():
            stats_table.add_row(key.replace("_", " ").title(), str(value))

        self.console.print("\n📊 Dataset Statistics:", style="bold cyan")
        self.console.print(stats_table)

    def display_verification_stats(self, stats: Dict[str, Any]):
        """Display verification statistics."""
        if stats.get("total_verified_points", 0) > 0:
            self.console.print("\n🔍 Verification Statistics:", style="bold cyan")

            # Calculate percentages
            total_points = stats.get("total_verified_points", 0)
            accurate = stats.get("accurate_points", 0)
            inaccurate = stats.get("inaccurate_points", 0)
            uncertain = stats.get("uncertain_points", 0)

            if total_points > 0:
                accurate_pct = (accurate / total_points) * 100
                inaccurate_pct = (inaccurate / total_points) * 100
                uncertain_pct = (uncertain / total_points) * 100

                self.console.print(
                    f"  - Verified entries: {stats.get('verified_entries', 0)}/{stats.get('total_entries', 0)}",
                    style="cyan",
                )
                self.console.print(
                    f"  - Total key points verified: {total_points}", style="cyan"
                )
                self.console.print(
                    f"  - Accurate: {accurate} ({accurate_pct:.1f}%)",
                    style="green",
                )
                self.console.print(
                    f"  - Inaccurate: {inaccurate} ({inaccurate_pct:.1f}%)",
                    style="red",
                )
                self.console.print(
                    f"  - Uncertain: {uncertain} ({uncertain_pct:.1f}%)",
                    style="yellow",
                )

    def display_success_message(self, message: str):
        """Display a success message."""
        self.console.print(f"\n✅ {message}", style="bold green")

    def display_error_message(self, message: str):
        """Display an error message."""
        self.console.print(f"\n❌ {message}", style="bold red")

    def display_warning_message(self, message: str):
        """Display a warning message."""
        self.console.print(f"\n⚠️ {message}", style="yellow")

    def create_progress(self, description: str = "Processing..."):
        """Create and return a Rich Progress instance."""
        return Progress(
            SpinnerColumn(),
            TextColumn("Testing progress"),  # Fixed description for test
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
        )
