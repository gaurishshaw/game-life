#!/usr/bin/env python3
"""Generate a bcrypt password hash and print the secrets.toml snippet.

Usage:
    python scripts/add_user.py --username yourname --password yourpassword
"""
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="Generate credentials for Life Game")
    parser.add_argument("--username", required=True, help="Login username")
    parser.add_argument("--password", required=True, help="Login password")
    args = parser.parse_args()

    try:
        import bcrypt
    except ImportError:
        print("ERROR: bcrypt not installed. Run: pip install bcrypt", file=sys.stderr)
        sys.exit(1)

    hashed = bcrypt.hashpw(args.password.encode(), bcrypt.gensalt()).decode()

    print(f"""
Paste this into .streamlit/secrets.toml
(or into the Streamlit Cloud Secrets UI):
─────────────────────────────────────────
[auth]
username = "{args.username}"
password_hash = "{hashed}"
─────────────────────────────────────────
""")


if __name__ == "__main__":
    main()
