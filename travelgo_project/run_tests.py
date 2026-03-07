#!/usr/bin/env python3
"""
Test Runner for TravelGo
=========================
This script runs all tests for the TravelGo application.
Run: python run_tests.py
"""

import os
import sys
import unittest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def discover_tests():
    """Discover and return all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Load test modules
    test_dir = os.path.join(os.path.dirname(__file__), 'tests')
    
    # Add test modules
    suite.addTests(loader.discover(test_dir, pattern='test_*.py'))
    
    return suite


def run_tests(verbosity=2):
    """Run all tests with specified verbosity"""
    print("=" * 60)
    print("  TravelGo Test Suite")
    print("=" * 60)
    print()
    
    # Discover tests
    suite = discover_tests()
    
    # Count tests
    test_count = suite.countTestCases()
    print(f"Found {test_count} tests")
    print()
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    # Print summary
    print()
    print("=" * 60)
    print("  Test Summary")
    print("=" * 60)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print()
    
    if result.wasSuccessful():
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed!")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}")
        
        return 1


def run_specific_test(test_name):
    """Run a specific test by name"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(test_name)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    # Check for specific test argument
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        exit_code = run_specific_test(test_name)
    else:
        exit_code = run_tests(verbosity=2)
    
    sys.exit(exit_code)

