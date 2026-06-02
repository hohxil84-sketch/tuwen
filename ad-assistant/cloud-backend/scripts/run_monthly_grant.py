#!/usr/bin/env python3
"""Run the monthly credit grant for all eligible users (S05-R04).

Usage::

    python scripts/run_monthly_grant.py
    python scripts/run_monthly_grant.py --year 2026 --month 6
    python scripts/run_monthly_grant.py --dry-run

Intended for manual execution or cron.
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone

# Ensure the cloud-backend package root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import async_session_factory
from app.services.monthly_grant_service import process_monthly_grants


def parse_args() -> argparse.Namespace:
    now = datetime.now(timezone.utc)
    parser = argparse.ArgumentParser(
        description="Process monthly credit grants for eligible users.",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=now.year,
        help=f"Target year (default: {now.year})",
    )
    parser.add_argument(
        "--month",
        type=int,
        choices=range(1, 13),
        default=now.month,
        metavar="1-12",
        help=f"Target month (default: {now.month})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Count eligible users without actually granting credits",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    async with async_session_factory() as db:
        try:
            summary = await process_monthly_grants(
                db, args.year, args.month, dry_run=args.dry_run,
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise

    mode = "[DRY RUN] " if args.dry_run else ""
    print(f"{mode}Monthly grant {args.year}-{args.month:02d} complete.")
    print(f"  Granted: {summary.granted}")
    print(f"  Skipped: {summary.skipped}")
    print(f"  Failed:  {summary.failed}")
    if summary.errors:
        print("  Errors:")
        for err in summary.errors:
            print(f"    - {err['account']} ({err['plan_code']}): {err['error']}")


if __name__ == "__main__":
    asyncio.run(main())
