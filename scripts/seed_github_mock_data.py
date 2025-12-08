"""
GitHub Mock Data Seeding Script

This script fetches file information from GitHub repositories and creates
mock data in the database following the Rhizome architecture.

The script reads default values from .env file (GITHUB_OWNER, GITHUB_REPO, GITHUB_BRANCH, GITHUB_TOKEN)
and allows overriding them via command-line arguments.

Usage:
    # Use values from .env file
    python scripts/seed_github_mock_data.py
    
    # Override specific values
    python scripts/seed_github_mock_data.py --owner octocat --repo Hello-World
    
    # Use custom token
    python scripts/seed_github_mock_data.py --token <your_token>
    
    # All options
    python scripts/seed_github_mock_data.py --owner <owner> --repo <repo> [--branch <branch>] [--token <token>]

Examples:
    python scripts/seed_github_mock_data.py
    python scripts/seed_github_mock_data.py --owner octocat --repo Hello-World --branch main
"""
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import and run the controller
from src.controllers.github_seed_controller import main

if __name__ == "__main__":
    main()
