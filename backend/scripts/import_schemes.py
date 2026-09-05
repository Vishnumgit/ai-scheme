"""
CLI Entry point for government scheme ingestion pipeline.

Usage:
  python scripts/import_schemes.py --dry-run
  python scripts/import_schemes.py --seed
  python scripts/import_schemes.py --source msme_ministry --limit 20
  python scripts/import_schemes.py --incremental --category Women
"""
import argparse
import asyncio
import logging
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ingestion.importer import run_ingestion, load_seed_schemes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("import_schemes_cli")


def parse_args():
    parser = argparse.ArgumentParser(description="Government Scheme Ingestion Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Validate without persisting to DB")
    parser.add_argument("--source", type=str, default=None, help="Specific source identifier to run")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of schemes to fetch/process")
    parser.add_argument("--incremental", action="store_true", help="Skip unchanged schemes based on content hash")
    parser.add_argument("--category", type=str, default=None, help="Filter by scheme category/tag")
    parser.add_argument("--seed", action="store_true", help="Load initial seed schemes from seed_schemes.json")
    return parser.parse_args()


async def main():
    args = parse_args()
    logger.info("Starting scheme ingestion CLI...")
    if args.seed:
        count = await load_seed_schemes(dry_run=args.dry_run)
        logger.info(f"Loaded {count} seed schemes.")
        return

    stats = await run_ingestion(
        sources=[args.source] if args.source else None,
        dry_run=args.dry_run,
        limit=args.limit,
        incremental=args.incremental,
        category_filter=args.category
    )
    logger.info(f"Ingestion completed: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
