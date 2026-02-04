#!/usr/bin/env python3
"""
MedBot API Server Launcher

This script starts the FastAPI server for the MedBot REST API.

Usage:
    python run_api.py [--port PORT] [--host HOST] [--reload]

Environment Variables:
    MEDBOT_API_PORT: Port to run on (default: 8001)
    MEDBOT_API_HOST: Host to bind to (default: 0.0.0.0)
"""

import os
import sys
import argparse
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    """Start the MedBot API server."""
    parser = argparse.ArgumentParser(description="MedBot API Server")
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MEDBOT_API_PORT", 8001)),
        help="Port to run on (default: 8001)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default=os.environ.get("MEDBOT_API_HOST", "0.0.0.0"),
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1)"
    )

    args = parser.parse_args()

    # Import uvicorn
    try:
        import uvicorn
    except ImportError:
        print("Error: uvicorn is not installed.")
        print("Install with: pip install uvicorn")
        sys.exit(1)

    # Print startup banner
    print("""
    ╔═══════════════════════════════════════════════╗
    ║           MedBot REST API Server              ║
    ║       Apple Watch & iOS Integration           ║
    ╠═══════════════════════════════════════════════╣
    ║  Endpoints:                                   ║
    ║    POST /api/v1/symptoms/analyze              ║
    ║    POST /api/v1/medication/lookup             ║
    ║    POST /api/v1/records/analyze               ║
    ║    POST /api/v1/doctors/search                ║
    ║    POST /api/v1/clinics/search                ║
    ║    GET  /api/v1/health                        ║
    ╠═══════════════════════════════════════════════╣
    ║  Documentation: http://{host}:{port}/docs      ║
    ╚═══════════════════════════════════════════════╝
    """.format(host=args.host if args.host != "0.0.0.0" else "localhost", port=args.port))

    # Run server
    uvicorn.run(
        "api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
        log_level="info",
    )


if __name__ == "__main__":
    main()
