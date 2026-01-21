#!/usr/bin/env python3
"""
Unit Tests for Academic Deliverables
Tests that all required academic documentation exists and contains required content.
"""

import sys
import os
import re
from pathlib import Path
from typing import List, Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))


class AcademicDeliverablesValidator:
    """Validates academic deliverables for completeness and quality."""
    
    def __init__(self):
        """Initialize the validator."""
        self.project_root = Path('.')
        self.docs_dir = self.project_root / 'docs'
        self.required_sections = {}
        self.validation_results = {}
    
    def validate_academic_documentation(self) -> Dict[str, Any]:
        """
        Validate the main academic project documentation.
        
        Returns:
            Dict containing validation results
        """
        doc_path = self.docs_dir / 'ACADEMIC_PROJECT_DOCUMENTATION.md'
        
        if not doc_path.exists():
            return {
                'exists': False,
                'error': f'Academic documentation not found at {doc_path}'
            }
        
        content = doc_path.read_text(encoding='utf-8')
        
        # Required sections for academic documentation
        required_sections = [
            'Abstract',
            'Problem Statement',
            'Literature Review',
            'Methodology and Implementation Approach',
            'Performance Metrics and Analysis',
            'Technical Specifications',
            'Innovation and Contributions',
            'Limitations and Future Work',
            'Conclusion',
            'References'
        ]
        
        results = {
            'exists': True,
            'file_size': len(content),
            'word_count': len(content.split()),
            'sections_found': [],
            'missing_sections': [],
            'section_analysis': {},
            'quality_metrics': {}
        }
        
        # Check for required sections
        for section in required_sections:
            # Look for section headers (various markdown formats)
            patterns = [
                rf'^#{1,3}\s+{re.escape(section)}',
                rf'^#{1,3}\s+\d+\.\s*{re.escape(section)}',
                rf'^\*\*{re.escape(section)}\*\*',
                # More flexible patterns for numbered sections
                rf'^#{1,3}\s+\d+\.\d*\s*{re.escape(section)}',
                # Pattern for sections that might have slight variations
                rf'^#{1,3}\s+\d*\.?\s*{re.escape(section.split()[0])}.*{re.escape(section.split()[-1]) if len(section.split()) > 1 else ""}',
                # Simple substring match in headers
                rf'^#{1,3}.*{re.escape(section)}',
                # Exact word match in headers
                rf'^#{1,3}.*\b{re.escape(section)}\b',
            ]
            
            found = False
            for pattern in patterns:
                if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                    found = True
                    break
            
            # Additional check for content-based detection
            if not found:
                # Check if section content exists even if header format is different
                section_keywords = section.lower().split()
                if len(section_keywords) >= 1:
                    # Look for lines containing the section keywords
                    lines = content.lower().split('\n')
                    for line in lines:
                        if line.startswith('#') and section.lower() in line:
                            found = True
                            break
            
            if found:
                results['sections_found'].append(section)
            else:
                results['missing_sections'].append(section)
        
        # Analyze section content quality
        results['section_analysis'] = self._analyze_section_content(content)
        
        # Calculate quality metrics
        results['quality_metrics'] = {
            'sections_coverage': len(results['sections_found']) / len(required_sections) * 100,
            'minimum_word_count_met': results['word_count'] >= 5000,  # Minimum for academic paper
            'has_references': 'References' in results['sections_found'],
            'has_methodology': 'Methodology' in results['sections_found'],
            'has_evaluation': 'Performance Metrics' in results['sections_found']
        }
        
        return results
    
    def validate_project_abstract(self) -> Dict[str, Any]:
        """
        Validate the project abstract document.
        
        Returns:
            Dict containing validation results
        """
        abstract_path = self.docs_dir / 'PROJECT_ABSTRACT.md'
        
        if not abstract_path.exists():
            return {
                'exists': False,
                'error': f'Project abstract not found at {abstract_path}'
            }
        
        content = abstract_path.read_text(encoding='utf-8')
        
        # Required elements for project abstract
        required_elements = [
            'Executive Summary',
            'Problem Context',
            'Solution Approach',
            'Technical Innovation',
            'Key Results',
            'Impact and Applications',
            'Academic Significance',
            'Future Development',
            'Conclusion'
        ]
        
        results = {
            'exists': True,
            'file_size': len(content),
            'word_count': len(content.split()),
            'elements_found': [],
            'missing_elements': [],
            'quality_metrics': {}
        }
        
        # Check for required elements
        for element in required_elements:
            if element.lower() in content.lower():
                results['elements_found'].append(element)
            else:
                results['missing_elements'].append(element)
        
        # Quality metrics for abstract
        results['quality_metrics'] = {
            'elements_coverage': len(results['elements_found']) / len(required_elements) * 100,
            'appropriate_length': 1000 <= results['word_count'] <= 3000,  # Typical abstract length
            'has_keywords': 'keywords' in content.lower(),
            'has_technical_specs': 'technical specifications' in content.lower(),
            'has_performance_data': any(term in content.lower() for term in ['performance', 'metrics', 'results'])
        }
        
        return results
    
    def validate_methodology_document(self) -> Dict[str, Any]:
        """
        Validate the methodology document.
        
        Returns:
            Dict containing validation results
        """
        methodology_path = self.docs_dir / 'METHODOLOGY.md'
        
        if not methodology_path.exists():
            return {
                'exists': False,
                'error': f'Methodology document not found at {methodology_path}'
            }
        
        content = methodology_path.read_text(encoding='utf-8')
        
        # Required sections for methodology
        required_sections = [
            'Research Methodology',
            'System Design Methodology',
            'Implementation Methodology',
            'Evaluation Methodology',
            'Validation and Verification',
            'Limitations and Constraints'
        ]
        
        results = {
            'exists': True,
            'file_size': len(content),
            'word_count': len(content.split()),
            'sections_found': [],
            'missing_sections': [],
            'quality_metrics': {}
        }
        
        # Check for required sections
        for section in required_sections:
            if section.lower() in content.lower():
                results['sections_found'].append(section)
            else:
                results['missing_sections'].append(section)
        
        # Quality metrics for methodology
        results['quality_metrics'] = {
            'sections_coverage': len(results['sections_found']) / len(required_sections) * 100,
            'has_design_science': 'design science' in content.lower(),
            'has_testing_strategy': 'testing' in content.lower(),
            'has_evaluation_criteria': 'evaluation' in content.lower(),
            'has_code_examples': '```' in content,  # Code blocks
            'comprehensive_length': results['word_count'] >= 3000
        }
        
        return results
    
    def validate_performance_metrics(self) -> Dict[str, Any]:
        """
        Validate that performance metrics are documented.
        
        Returns:
            Dict containing validation results
        """
        # Check multiple locations for performance data
        locations_to_check = [
            self.docs_dir / 'ACADEMIC_PROJECT_DOCUMENTATION.md',
            self.docs_dir / 'PROJECT_ABSTRACT.md',
            self.project_root / 'README.md'
        ]
        
        performance_indicators = [
            'processing time',
            'throughput',
            'memory usage',
            'performance',
            'benchmark',
            'metrics',
            'seconds',
            'milliseconds',
            'devices per minute',
            'operations per second'
        ]
        
        results = {
            'performance_data_found': False,
            'locations_checked': [],
            'indicators_found': [],
            'quantitative_data': False,
            'files_with_metrics': []
        }
        
        for location in locations_to_check:
            if location.exists():
                content = location.read_text(encoding='utf-8').lower()
                results['locations_checked'].append(str(location))
                
                found_indicators = []
                for indicator in performance_indicators:
                    if indicator in content:
                        found_indicators.append(indicator)
                        results['performance_data_found'] = True
                
                if found_indicators:
                    results['files_with_metrics'].append({
                        'file': str(location),
                        'indicators': found_indicators
                    })
                
                # Check for quantitative data (numbers with units)
                if re.search(r'\d+\.?\d*\s*(seconds?|ms|milliseconds?|minutes?|mb|gb|bytes?)', content):
                    results['quantitative_data'] = True
        
        # Flatten indicators found
        all_indicators = []
        for file_data in results['files_with_metrics']:
            all_indicators.extend(file_data['indicators'])
        results['indicators_found'] = list(set(all_indicators))
        
        return results
    
    def validate_security_analysis(self) -> Dict[str, Any]:
        """
        Validate that security analysis is documented.
        
        Returns:
            Dict containing validation results
        """
        # Check for security-related content
        locations_to_check = [
            self.docs_dir / 'ACADEMIC_PROJECT_DOCUMENTATION.md',
            self.docs_dir / 'METHODOLOGY.md',
            self.project_root / 'README.md'
        ]
        
        security_topics = [
            'nist 800-88',
            'cryptographic',
            'sha-256',
            'blockchain security',
            'data privacy',
            'access control',
            'tamper detection',
            'audit trail',
            'compliance',
            'security analysis'
        ]
        
        results = {
            'security_analysis_found': False,
            'locations_checked': [],
            'topics_covered': [],
            'files_with_security': [],
            'compliance_mentioned': False
        }
        
        for location in locations_to_check:
            if location.exists():
                content = location.read_text(encoding='utf-8').lower()
                results['locations_checked'].append(str(location))
                
                found_topics = []
                for topic in security_topics:
                    if topic in content:
                        found_topics.append(topic)
                        results['security_analysis_found'] = True
                
                if found_topics:
                    results['files_with_security'].append({
                        'file': str(location),
                        'topics': found_topics
                    })
                
                # Check for compliance mentions
                if any(term in content for term in ['compliance', 'compliant', 'standard']):
                    results['compliance_mentioned'] = True
        
        # Flatten topics found
        all_topics = []
        for file_data in results['files_with_security']:
            all_topics.extend(file_data['topics'])
        results['topics_covered'] = list(set(all_topics))
        
        return results
    
    def _analyze_section_content(self, content: str) -> Dict[str, Any]:
        """
        Analyze the quality of section content.
        
        Args:
            content: Document content to analyze
            
        Returns:
            Dict containing content analysis
        """
        analysis = {
            'has_citations': bool(re.search(r'\([A-Za-z]+.*?\d{4}\)', content)),  # Academic citations
            'has_code_examples': '```' in content,
            'has_figures_tables': any(term in content.lower() for term in ['figure', 'table', 'diagram']),
            'has_quantitative_data': bool(re.search(r'\d+\.?\d*\s*%', content)),  # Percentages
            'reference_count': len(re.findall(r'^[A-Za-z]+.*?\(\d{4}\)', content, re.MULTILINE)),
            'technical_depth': any(term in content.lower() for term in [
                'algorithm', 'implementation', 'architecture', 'methodology', 'evaluation'
            ])
        }
        
        return analysis
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """
        Run comprehensive validation of all academic deliverables.
        
        Returns:
            Dict containing complete validation results
        """
        results = {
            'academic_documentation': self.validate_academic_documentation(),
            'project_abstract': self.validate_project_abstract(),
            'methodology_document': self.validate_methodology_document(),
            'performance_metrics': self.validate_performance_metrics(),
            'security_analysis': self.validate_security_analysis()
        }
        
        # Calculate overall quality score
        quality_scores = []
        
        if results['academic_documentation']['exists']:
            quality_scores.append(results['academic_documentation']['quality_metrics']['sections_coverage'])
        
        if results['project_abstract']['exists']:
            quality_scores.append(results['project_abstract']['quality_metrics']['elements_coverage'])
        
        if results['methodology_document']['exists']:
            quality_scores.append(results['methodology_document']['quality_metrics']['sections_coverage'])
        
        results['overall_quality'] = {
            'average_coverage': sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            'all_documents_exist': all([
                results['academic_documentation']['exists'],
                results['project_abstract']['exists'],
                results['methodology_document']['exists']
            ]),
            'performance_data_available': results['performance_metrics']['performance_data_found'],
            'security_analysis_available': results['security_analysis']['security_analysis_found']
        }
        
        return results


def test_academic_documentation_exists():
    """Test that academic documentation files exist."""
    print("Testing academic documentation existence...")
    
    validator = AcademicDeliverablesValidator()
    
    required_files = [
        'docs/ACADEMIC_PROJECT_DOCUMENTATION.md',
        'docs/PROJECT_ABSTRACT.md',
        'docs/METHODOLOGY.md'
    ]
    
    results = {}
    all_exist = True
    
    for file_path in required_files:
        path = Path(file_path)
        exists = path.exists()
        results[file_path] = exists
        
        if exists:
            file_size = path.stat().st_size
            print(f"  ✓ {file_path}: EXISTS ({file_size:,} bytes)")
        else:
            print(f"  ✗ {file_path}: MISSING")
            all_exist = False
    
    return all_exist, results


def test_academic_documentation_content():
    """Test that academic documentation contains required content."""
    print("\nTesting academic documentation content...")
    
    validator = AcademicDeliverablesValidator()
    results = validator.run_comprehensive_validation()
    
    # Test academic documentation
    academic_doc = results['academic_documentation']
    if academic_doc['exists']:
        coverage = academic_doc['quality_metrics']['sections_coverage']
        print(f"  ✓ Academic Documentation: {coverage:.1f}% section coverage")
        print(f"    - Word count: {academic_doc['word_count']:,}")
        print(f"    - Sections found: {len(academic_doc['sections_found'])}")
        if academic_doc['missing_sections']:
            print(f"    - Missing sections: {', '.join(academic_doc['missing_sections'])}")
    else:
        print(f"  ✗ Academic Documentation: {academic_doc.get('error', 'Not found')}")
    
    # Test project abstract
    abstract = results['project_abstract']
    if abstract['exists']:
        coverage = abstract['quality_metrics']['elements_coverage']
        print(f"  ✓ Project Abstract: {coverage:.1f}% element coverage")
        print(f"    - Word count: {abstract['word_count']:,}")
        print(f"    - Elements found: {len(abstract['elements_found'])}")
    else:
        print(f"  ✗ Project Abstract: {abstract.get('error', 'Not found')}")
    
    # Test methodology document
    methodology = results['methodology_document']
    if methodology['exists']:
        coverage = methodology['quality_metrics']['sections_coverage']
        print(f"  ✓ Methodology Document: {coverage:.1f}% section coverage")
        print(f"    - Word count: {methodology['word_count']:,}")
        print(f"    - Has code examples: {methodology['quality_metrics']['has_code_examples']}")
    else:
        print(f"  ✗ Methodology Document: {methodology.get('error', 'Not found')}")
    
    return results


def test_performance_metrics_documentation():
    """Test that performance metrics are properly documented."""
    print("\nTesting performance metrics documentation...")
    
    validator = AcademicDeliverablesValidator()
    results = validator.validate_performance_metrics()
    
    if results['performance_data_found']:
        print(f"  ✓ Performance data found in {len(results['files_with_metrics'])} files")
        print(f"  ✓ Quantitative data present: {results['quantitative_data']}")
        print(f"  ✓ Performance indicators found: {len(results['indicators_found'])}")
        
        for file_data in results['files_with_metrics']:
            print(f"    - {Path(file_data['file']).name}: {len(file_data['indicators'])} indicators")
    else:
        print("  ✗ No performance data found in documentation")
    
    return results['performance_data_found']


def test_security_analysis_documentation():
    """Test that security analysis is properly documented."""
    print("\nTesting security analysis documentation...")
    
    validator = AcademicDeliverablesValidator()
    results = validator.validate_security_analysis()
    
    if results['security_analysis_found']:
        print(f"  ✓ Security analysis found in {len(results['files_with_security'])} files")
        print(f"  ✓ Compliance mentioned: {results['compliance_mentioned']}")
        print(f"  ✓ Security topics covered: {len(results['topics_covered'])}")
        
        for file_data in results['files_with_security']:
            print(f"    - {Path(file_data['file']).name}: {len(file_data['topics'])} topics")
    else:
        print("  ✗ No security analysis found in documentation")
    
    return results['security_analysis_found']


def test_documentation_quality_metrics():
    """Test overall documentation quality metrics."""
    print("\nTesting documentation quality metrics...")
    
    validator = AcademicDeliverablesValidator()
    results = validator.run_comprehensive_validation()
    
    overall = results['overall_quality']
    
    print(f"  ✓ Average coverage: {overall['average_coverage']:.1f}%")
    print(f"  ✓ All documents exist: {overall['all_documents_exist']}")
    print(f"  ✓ Performance data available: {overall['performance_data_available']}")
    print(f"  ✓ Security analysis available: {overall['security_analysis_available']}")
    
    # Quality thresholds
    quality_passed = (
        overall['average_coverage'] >= 80.0 and
        overall['all_documents_exist'] and
        overall['performance_data_available'] and
        overall['security_analysis_available']
    )
    
    if quality_passed:
        print("  ✓ Overall quality: PASSED")
    else:
        print("  ✗ Overall quality: NEEDS IMPROVEMENT")
    
    return quality_passed, results


def main():
    """Run all academic deliverables tests."""
    print("=== ACADEMIC DELIVERABLES VALIDATION ===")
    print("Testing academic project documentation completeness and quality\n")
    
    # Test 1: File existence
    files_exist, file_results = test_academic_documentation_exists()
    
    # Test 2: Content validation
    content_results = test_academic_documentation_content()
    
    # Test 3: Performance metrics
    performance_ok = test_performance_metrics_documentation()
    
    # Test 4: Security analysis
    security_ok = test_security_analysis_documentation()
    
    # Test 5: Overall quality
    quality_ok, quality_results = test_documentation_quality_metrics()
    
    # Summary
    print(f"\n{'='*60}")
    print("ACADEMIC DELIVERABLES VALIDATION SUMMARY")
    print(f"{'='*60}")
    
    tests = [
        ("Documentation Files Exist", files_exist),
        ("Content Quality", content_results['overall_quality']['average_coverage'] >= 80),
        ("Performance Metrics", performance_ok),
        ("Security Analysis", security_ok),
        ("Overall Quality", quality_ok)
    ]
    
    passed_tests = sum(1 for _, passed in tests if passed)
    
    for test_name, passed in tests:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed_tests}/{len(tests)} tests passed")
    
    if passed_tests == len(tests):
        print("🎉 All academic deliverables validation tests PASSED!")
        print("✓ Academic documentation is complete and meets quality standards")
        return True
    else:
        print("⚠️  Some academic deliverables tests failed. Please review and improve documentation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)