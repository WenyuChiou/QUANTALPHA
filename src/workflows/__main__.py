"""Command-line interface for daily workflow."""

import argparse
from .daily_workflow import DailyWorkflow


def main():
    parser = argparse.ArgumentParser(description="Run daily workflow")
    parser.add_argument("--universe", type=str, default="sp500", help="Universe name")
    parser.add_argument("--n_candidates", type=int, default=3, help="Number of candidates")
    parser.add_argument("--focus", type=str, nargs="+", help="Focus topics")
    
    args = parser.parse_args()
    
    workflow = DailyWorkflow(universe=args.universe)
    results = workflow.run_daily_cycle(
        n_candidates=args.n_candidates,
        focus_topics=args.focus
    )
    
    print("\nDaily workflow completed successfully!")


if __name__ == "__main__":
    main()

