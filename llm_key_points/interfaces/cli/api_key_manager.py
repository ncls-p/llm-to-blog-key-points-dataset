"""
API key management functionality.
"""

import os
import re
import questionary
from ..console.rich_presenter import RichPresenter

presenter = RichPresenter()


def validate_api_key(api_key: str) -> bool:
    """Validate API key format."""
    return len(api_key) > 20


def get_api_key() -> str:
    """Get API key from environment or user input."""
    api_key = os.getenv("OPENAI_COMPATIBLE_API_KEY")

    if api_key and validate_api_key(api_key):
        return api_key

    presenter.display_warning_message("API key not found in environment or invalid.")

    api_key = questionary.text(
        "Please enter your OpenAI compatible API key:",
        validate=lambda text: validate_api_key(text) or "Invalid API key format",
    ).ask()

    if questionary.confirm("Would you like to save this API key to .env file?").ask():
        save_api_key(api_key)

    return api_key


def save_api_key(api_key: str) -> None:
    """Save API key to .env file."""
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            env_content = f.read()

        if "OPENAI_COMPATIBLE_API_KEY=" in env_content:
            env_content = re.sub(
                r"OPENAI_COMPATIBLE_API_KEY=.*",
                f"OPENAI_COMPATIBLE_API_KEY={api_key}",
                env_content,
            )
        else:
            env_content += f"\nOPENAI_COMPATIBLE_API_KEY={api_key}"

        with open(".env", "w") as f:
            f.write(env_content)
    else:
        with open(".env", "w") as f:
            f.write(f"OPENAI_COMPATIBLE_API_KEY={api_key}")

    presenter.display_success_message("API key saved to .env file")


def remove_api_key() -> None:
    """Remove API key by deleting .env file."""
    if os.path.exists(".env"):
        os.remove(".env")
        presenter.display_success_message("API key removed")
    else:
        presenter.display_warning_message("No .env file found")


def view_api_key() -> None:
    """Display current API key (masked)."""
    api_key = os.getenv("OPENAI_COMPATIBLE_API_KEY")
    if api_key:
        presenter.console.print(
            f"\n🔑 Current API key: {api_key[:8]}...{api_key[-4:]}", style="green"
        )
    else:
        presenter.display_warning_message("No API key found")


def manage_api_key():
    """Interactive API key management menu."""
    while True:
        choice = questionary.select(
            "API Key Management:",
            choices=[
                "View current API key",
                "Update API key",
                "Remove API key",
                "Back to main menu",
            ],
        ).ask()

        if choice == "View current API key":
            view_api_key()
        elif choice == "Update API key":
            api_key = get_api_key()
            if api_key:  # Only show success if we got a valid key
                presenter.display_success_message("API key updated")
        elif choice == "Remove API key":
            remove_api_key()
        else:
            break
