#!/usr/bin/env python3
"""
Birth Chart Generator CLI

Command-line interface for generating astrological birth charts.
"""

import argparse
import sys
import logging
from pathlib import Path

from birth_chart import generate_birth_chart

def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Generate astrological birth charts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python generate_birth_chart.py --date 1986-11-09 --time 16:28 --lat 46.2044 --lon 6.1432

  # With custom icons and output directory
  python generate_birth_chart.py --date 1986-11-09 --time 16:28 --lat 46.2044 --lon 6.1432 \\
    --icons ./icons --out outputs/

  # Using Porphyry house system
  python generate_birth_chart.py --date 1986-11-09 --time 16:28 --lat 46.2044 --lon 6.1432 \\
    --house-system porphyry
        """
    )
    
    # Required arguments
    parser.add_argument("--date", required=True,
                       help="Date of birth (YYYY-MM-DD)")
    parser.add_argument("--time", required=True,
                       help="Local time of birth (HH:MM 24h format)")
    parser.add_argument("--lat", required=True, type=float,
                       help="Latitude of birth place")
    parser.add_argument("--lon", required=True, type=float,
                       help="Longitude of birth place")
    
    # Optional arguments
    parser.add_argument("--icons", default="icons",
                       help="Directory containing PNG icons (default: icons)")
    parser.add_argument("--house-system", default="placidus",
                       choices=["placidus", "porphyry"],
                       help="House system to use (default: placidus)")
    parser.add_argument("--zodiac", default="tropical",
                       choices=["tropical"],
                       help="Zodiac system (default: tropical)")
    parser.add_argument("--out", type=str,
                       help="Output directory (default: outputs/)")
    parser.add_argument("--output-path", type=str,
                       help="Full output path (overrides --out)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Determine output path
        output_path = None
        if args.output_path:
            output_path = args.output_path
        elif args.out:
            # Generate filename and combine with output directory
            from birth_chart.service import _generate_output_path
            filename = Path(_generate_output_path(args.date, args.time, args.lat, args.lon)).name
            output_path = str(Path(args.out) / filename)
        
        # Generate birth chart
        logger.info("Starting birth chart generation...")
        result_path = generate_birth_chart(
            date=args.date,
            time=args.time,
            lat=args.lat,
            lon=args.lon,
            icons_dir=args.icons,
            house_system=args.house_system,
            zodiac=args.zodiac,
            output_path=output_path
        )
        
        print(f"✅ Birth chart generated successfully!")
        print(f"📁 Saved to: {result_path}")
        
        return 0
        
    except ValueError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except ImportError as e:
        print(f"❌ Missing dependency: {e}", file=sys.stderr)
        print("💡 Install required packages with:", file=sys.stderr)
        print("   pip install flatlib timezonefinderL matplotlib pillow", file=sys.stderr)
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
