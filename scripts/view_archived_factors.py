"""CLI tool for viewing archived factors."""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.archive.archive_viewer import ArchiveViewer, print_factor_summary


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="View and analyze archived success factors"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List archived factors')
    list_parser.add_argument(
        '--min-sharpe',
        type=float,
        help='Minimum Sharpe ratio filter'
    )
    list_parser.add_argument(
        '--min-ic',
        type=float,
        help='Minimum IC filter'
    )
    list_parser.add_argument(
        '--top',
        type=int,
        help='Show only top N factors'
    )
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show factor details')
    show_parser.add_argument(
        'factor_path',
        help='Path to archived factor'
    )
    
    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare factors')
    compare_parser.add_argument(
        'factor_paths',
        nargs='+',
        help='Paths to factors to compare'
    )
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    viewer = ArchiveViewer()
    
    if args.command == 'list':
        df = viewer.list_factors(
            min_sharpe=args.min_sharpe,
            min_ic=args.min_ic,
            top_n=args.top
        )
        
        if df.empty:
            print("No archived factors found.")
        else:
            print(f"\nFound {len(df)} archived factors:\n")
            print(df.to_string(index=False))
            print()
    
    elif args.command == 'show':
        print_factor_summary(args.factor_path)
    
    elif args.command == 'compare':
        df = viewer.compare_factors(args.factor_paths)
        
        print("\nFactor Comparison:\n")
        print(df.to_string(index=False))
        print()


if __name__ == '__main__':
    main()
