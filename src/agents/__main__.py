"""Command-line interface for orchestrator."""

import argparse
from datetime import datetime
from .orchestrator import Orchestrator


def main():
    parser = argparse.ArgumentParser(description="Run factor mining orchestrator")
    parser.add_argument("--universe", type=str, default="sp500", help="Universe name")
    parser.add_argument("--n_candidates", type=int, default=3, help="Number of candidates per iteration")
    parser.add_argument("--n_iterations", type=int, default=1, help="Number of iterations")
    parser.add_argument("--days", type=int, default=2500, help="Lookback days")
    
    args = parser.parse_args()
    
    orchestrator = Orchestrator(universe=args.universe)
    
    # Initialize data
    end_date = datetime.now()
    start_date = datetime(end_date.year - 10, 1, 1)  # ~10 years
    orchestrator.initialize_data(start_date=start_date, end_date=end_date)
    
    # Run iterations
    if args.n_iterations > 1:
        results = orchestrator.run_multiple_iterations(
            n_iterations=args.n_iterations,
            n_candidates_per_iteration=args.n_candidates
        )
    else:
        results = orchestrator.run_iteration(n_candidates=args.n_candidates)
    
    print("\n" + "="*60)
    print("Iteration Complete!")
    print(f"Successful: {len(results.get('successful', []))}")
    print(f"Failed: {len(results.get('failed', []))}")
    print("="*60)


if __name__ == "__main__":
    main()

