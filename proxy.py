"""
Main proxy server — connects all modules.
Owners: Ahmed Abdullah + Tayyab Ali Sandhu
"""

import argparse


def main():
    parser = argparse.ArgumentParser(description="HTTP Caching Proxy")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--origin", type=str, default="http://localhost:8000")
    args = parser.parse_args()

    print(f"Proxy listening on port {args.port}")
    print(f"Forwarding to origin: {args.origin}")
    # TODO: Wire up listener + parser + cache + logger


if __name__ == "__main__":
    main()
