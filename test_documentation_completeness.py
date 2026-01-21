#!/usr/bin/env python3
"""
Property Test for Documentation Completeness
Tests Property 18: Code Documentation Completeness
"""

import sys
import os
import ast
import inspect
from pathlib import Path
from typing import List, Dict, Any, Set

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))


class DocumentationChecker:
    """Checks documentation completeness across the codebase."""
    
    def __init__(self, package_path: str = "secure_data_wiping"):
        """
        Initialize documentation checker.
        
        Args:
            package_path: Path to the package to check
        """
        self.package_path = Path(package_path)
        self.missing_docs = []
        self.documented_items = []
        
    def check_file_documentation(self, file_path: Path) -> Dict[str, Any]:
        """
        Check documentation completeness for a single Python file.
        
        Args:
            file_path: Path to Python file to check
            
        Returns:
            Dict containing documentation analysis results
        """
        results = {
            'file': str(file_path),
            'module_docstring': False,
            'classes': [],
            'functions': [],
            'methods': [],
            'missing_docs': [],
            'total_items': 0,
            'documented_items': 0
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the AST
            tree = ast.parse(content)
            
            # Check module docstring
            if ast.get_docstring(tree):
                results['module_docstring'] = True
                results['documented_items'] += 1
            else:
                results['missing_docs'].append(f"Module {file_path.name}")
            results['total_items'] += 1
            
            # Check classes and their methods
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = {
                        'name': node.name,
                        'has_docstring': bool(ast.get_docstring(node)),
                        'methods': []
                    }
                    
                    if class_info['has_docstring']:
                        results['documented_items'] += 1
                    else:
                        results['missing_docs'].append(f"Class {node.name}")
                    results['total_items'] += 1
                    
                    # Check methods in the class
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_info = {
                                'name': item.name,
                                'has_docstring': bool(ast.get_docstring(item)),
                                'is_private': item.name.startswith('_'),
                                'is_dunder': item.name.startswith('__') and item.name.endswith('__')
                            }
                            
                            # Only require docstrings for public methods and important private methods
                            if not method_info['is_dunder']:
                                if method_info['has_docstring']:
                                    results['documented_items'] += 1
                                else:
                                    results['missing_docs'].append(f"Method {node.name}.{item.name}")
                                results['total_items'] += 1
                            
                            class_info['methods'].append(method_info)
                    
                    results['classes'].append(class_info)
                
                elif isinstance(node, ast.FunctionDef) and not any(isinstance(parent, ast.ClassDef) for parent in ast.walk(tree) if hasattr(parent, 'body') and node in getattr(parent, 'body', [])):
                    # Top-level functions (not methods)
                    func_info = {
                        'name': node.name,
                        'has_docstring': bool(ast.get_docstring(node)),
                        'is_private': node.name.startswith('_'),
                        'is_dunder': node.name.startswith('__') and node.name.endswith('__')
                    }
                    
                    # Only require docstrings for public functions and important private functions
                    if not func_info['is_dunder']:
                        if func_info['has_docstring']:
                            results['documented_items'] += 1
                        else:
                            results['missing_docs'].append(f"Function {node.name}")
                        results['total_items'] += 1
                    
                    results['functions'].append(func_info)
        
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def check_package_documentation(self) -> Dict[str, Any]:
        """
        Check documentation completeness for the entire package.
        
        Returns:
            Dict containing comprehensive documentation analysis
        """
        package_results = {
            'package_path': str(self.package_path),
            'files_checked': 0,
            'total_items': 0,
            'documented_items': 0,
            'missing_docs': [],
            'file_results': [],
            'documentation_coverage': 0.0
        }
        
        # Find all Python files in the package
        python_files = list(self.package_path.rglob('*.py'))
        
        for file_path in python_files:
            # Skip __pycache__ and test files for this check
            if '__pycache__' in str(file_path) or file_path.name.startswith('test_'):
                continue
            
            file_results = self.check_file_documentation(file_path)
            package_results['file_results'].append(file_results)
            package_results['files_checked'] += 1
            package_results['total_items'] += file_results['total_items']
            package_results['documented_items'] += file_results['documented_items']
            package_results['missing_docs'].extend(file_results['missing_docs'])
        
        # Calculate coverage
        if package_results['total_items'] > 0:
            package_results['documentation_coverage'] = (
                package_results['documented_items'] / package_results['total_items']
            ) * 100
        
        return package_results


def test_property_18_documentation_completeness():
    """
    Test Property 18: Code Documentation Completeness
    
    Validates: Requirements 10.2
    For any class or function in the system, the code should include 
    comprehensive docstrings for documentation purposes.
    """
    print("Testing Property 18: Code Documentation Completeness")
    
    checker = DocumentationChecker()
    results = checker.check_package_documentation()
    
    print(f"Files checked: {results['files_checked']}")
    print(f"Total items: {results['total_items']}")
    print(f"Documented items: {results['documented_items']}")
    print(f"Documentation coverage: {results['documentation_coverage']:.1f}%")
    
    # Define minimum acceptable coverage
    MIN_COVERAGE = 85.0  # 85% minimum coverage
    
    if results['documentation_coverage'] >= MIN_COVERAGE:
        print(f"✓ Property 18 test passed: {results['documentation_coverage']:.1f}% >= {MIN_COVERAGE}%")
        
        # Show detailed results for well-documented files
        well_documented_files = []
        for file_result in results['file_results']:
            if file_result['total_items'] > 0:
                file_coverage = (file_result['documented_items'] / file_result['total_items']) * 100
                if file_coverage >= MIN_COVERAGE:
                    well_documented_files.append((file_result['file'], file_coverage))
        
        print(f"\nWell-documented files ({len(well_documented_files)}):")
        for file_path, coverage in sorted(well_documented_files, key=lambda x: x[1], reverse=True):
            print(f"  ✓ {Path(file_path).name}: {coverage:.1f}%")
        
        return True
    else:
        print(f"✗ Property 18 test failed: {results['documentation_coverage']:.1f}% < {MIN_COVERAGE}%")
        
        # Show missing documentation details
        if results['missing_docs']:
            print(f"\nMissing documentation ({len(results['missing_docs'])} items):")
            for missing in results['missing_docs'][:10]:  # Show first 10
                print(f"  - {missing}")
            if len(results['missing_docs']) > 10:
                print(f"  ... and {len(results['missing_docs']) - 10} more")
        
        # Show files that need improvement
        needs_improvement = []
        for file_result in results['file_results']:
            if file_result['total_items'] > 0:
                file_coverage = (file_result['documented_items'] / file_result['total_items']) * 100
                if file_coverage < MIN_COVERAGE:
                    needs_improvement.append((file_result['file'], file_coverage, len(file_result['missing_docs'])))
        
        if needs_improvement:
            print(f"\nFiles needing documentation improvement:")
            for file_path, coverage, missing_count in sorted(needs_improvement, key=lambda x: x[1]):
                print(f"  - {Path(file_path).name}: {coverage:.1f}% ({missing_count} missing)")
        
        return False


def test_specific_modules_documentation():
    """Test documentation for specific critical modules."""
    print("\nTesting specific module documentation...")
    
    critical_modules = [
        'secure_data_wiping/wipe_engine/wipe_engine.py',
        'secure_data_wiping/hash_generator/hash_generator.py',
        'secure_data_wiping/blockchain_logger/blockchain_logger.py',
        'secure_data_wiping/certificate_generator/certificate_generator.py',
        'secure_data_wiping/system_controller/system_controller.py'
    ]
    
    checker = DocumentationChecker()
    all_passed = True
    
    for module_path in critical_modules:
        if Path(module_path).exists():
            results = checker.check_file_documentation(Path(module_path))
            
            if results['total_items'] > 0:
                coverage = (results['documented_items'] / results['total_items']) * 100
                module_name = Path(module_path).name
                
                if coverage >= 90.0:  # Higher standard for critical modules
                    print(f"  ✓ {module_name}: {coverage:.1f}% coverage")
                else:
                    print(f"  ✗ {module_name}: {coverage:.1f}% coverage (needs improvement)")
                    all_passed = False
            else:
                print(f"  - {Path(module_path).name}: No documentable items found")
        else:
            print(f"  - {module_path}: File not found")
            all_passed = False
    
    return all_passed


def test_docstring_quality():
    """Test the quality of existing docstrings."""
    print("\nTesting docstring quality...")
    
    # Import key modules to check docstring quality
    try:
        from secure_data_wiping.wipe_engine import WipeEngine
        from secure_data_wiping.hash_generator import HashGenerator
        from secure_data_wiping.system_controller import SystemController
        
        modules_to_check = [
            (WipeEngine, 'WipeEngine'),
            (HashGenerator, 'HashGenerator'),
            (SystemController, 'SystemController')
        ]
        
        quality_passed = True
        
        for module_class, name in modules_to_check:
            # Check class docstring
            class_doc = inspect.getdoc(module_class)
            if class_doc and len(class_doc) > 50:  # Reasonable length
                print(f"  ✓ {name}: Good class documentation")
            else:
                print(f"  ✗ {name}: Class documentation needs improvement")
                quality_passed = False
            
            # Check key methods
            key_methods = [method for method in dir(module_class) 
                          if not method.startswith('_') and callable(getattr(module_class, method))]
            
            documented_methods = 0
            for method_name in key_methods[:5]:  # Check first 5 public methods
                method = getattr(module_class, method_name)
                if inspect.getdoc(method):
                    documented_methods += 1
            
            if documented_methods >= len(key_methods[:5]) * 0.8:  # 80% of methods documented
                print(f"  ✓ {name}: Good method documentation")
            else:
                print(f"  ✗ {name}: Method documentation needs improvement")
                quality_passed = False
        
        return quality_passed
        
    except ImportError as e:
        print(f"  ✗ Could not import modules for quality check: {e}")
        return False


def main():
    """Run all documentation completeness tests."""
    print("=== Documentation Completeness Testing ===")
    print("Testing Property 18: Code Documentation Completeness\n")
    
    # Test overall documentation completeness
    property_18_passed = test_property_18_documentation_completeness()
    
    # Test specific critical modules
    specific_modules_passed = test_specific_modules_documentation()
    
    # Test docstring quality
    quality_passed = test_docstring_quality()
    
    # Summary
    print(f"\n{'='*60}")
    print("DOCUMENTATION TESTING SUMMARY")
    print(f"{'='*60}")
    
    tests = [
        ("Property 18: Overall Documentation Coverage", property_18_passed),
        ("Critical Modules Documentation", specific_modules_passed),
        ("Docstring Quality", quality_passed)
    ]
    
    passed_tests = sum(1 for _, passed in tests if passed)
    
    for test_name, passed in tests:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed_tests}/{len(tests)} tests passed")
    
    if passed_tests == len(tests):
        print("🎉 All documentation tests PASSED!")
        print("✓ Property 18: Code Documentation Completeness - VALIDATED")
        return True
    else:
        print("⚠️  Some documentation tests failed. Please improve documentation coverage.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)