"""
Run tests for the BoringTrade trading bot.
"""
import os
import sys
import unittest
import argparse

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run tests for the BoringTrade trading bot")
    parser.add_argument("--test", type=str, help="Specific test to run (e.g., 'tests.test_orb_strategy')")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    return parser.parse_args()


def main():
    """Main entry point."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Set verbosity level
    verbosity = 2 if args.verbose else 1
    
    # Run specific test if provided
    if args.test:
        print(f"Running test: {args.test}")
        test_suite = unittest.defaultTestLoader.loadTestsFromName(args.test)
        test_runner = unittest.TextTestRunner(verbosity=verbosity)
        result = test_runner.run(test_suite)
        sys.exit(0 if result.wasSuccessful() else 1)
    
    # Run all tests
    print("Running all tests")
    test_suite = unittest.defaultTestLoader.discover("tests")
    test_runner = unittest.TextTestRunner(verbosity=verbosity)
    result = test_runner.run(test_suite)
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
