import os
import json
import argparse
from pathlib import Path
from datasets import Dataset
from huggingface_hub import HfApi, login


def upload_dataset(
    dataset_path: str,
    hf_token: str = None,
    repo_id: str = None,
    private: bool = False,
    readme_path: str = "dataset_card.md",
):
    """Upload dataset to Hugging Face Hub."""
    # Load dataset
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Convert to Hugging Face Dataset
    dataset = Dataset.from_list(data)

    # Login to Hugging Face
    if hf_token:
        login(token=hf_token)
    else:
        print("No token provided. Using stored credentials if available.")

    # Get or create repo_id
    if not repo_id:
        username = input("Enter your Hugging Face username: ")
        dataset_name = input("Enter dataset name (e.g., article-key-points): ")
        repo_id = f"{username}/{dataset_name}"

    # Push to Hub
    dataset.push_to_hub(repo_id=repo_id, private=private, readme_path=readme_path)

    print(f"✅ Dataset uploaded successfully to {repo_id}")
    print(f"🔗 View your dataset at: https://huggingface.co/datasets/{repo_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload dataset to Hugging Face Hub")
    parser.add_argument(
        "--dataset",
        type=str,
        default="Alpaca Data Cleaned.json",
        help="Path to dataset file",
    )
    parser.add_argument("--token", type=str, help="Hugging Face API token")
    parser.add_argument(
        "--repo_id", type=str, help="Repository ID in format username/dataset-name"
    )
    parser.add_argument(
        "--private", action="store_true", help="Make the dataset private"
    )
    parser.add_argument(
        "--readme", type=str, default="dataset_card.md", help="Path to README file"
    )

    args = parser.parse_args()

    upload_dataset(
        dataset_path=args.dataset,
        hf_token=args.token,
        repo_id=args.repo_id,
        private=args.private,
        readme_path=args.readme,
    )
