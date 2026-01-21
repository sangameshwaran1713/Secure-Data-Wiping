#!/usr/bin/env python3
"""
Demo Runner - Central Hub for All Demonstrations

This script provides a central interface to run different types of demonstrations
for the secure data wiping system.
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))


def print_banner():
    """Print the demo runner banner."""
    print("🎯 SECURE DATA WIPING SYSTEM - DEMO RUNNER")
    print("=" * 80)
    print("Final Year Project - Computer Science")
    print("Blockchain-Based Audit Trail for IT Asset Recycling")
    print("=" * 80)
    print()


def print_demo_menu():
    """Print the available demonstration options."""
    print("📋 AVAILABLE DEMONSTRATIONS:")
    print()
    print("1. 🚀 Quick Demo")
    print("   - Fast overview of key system features")
    print("   - Duration: ~2 minutes")
    print("   - Best for: Initial testing and validation")
    print()
    print("2. 🎓 Viva Presentation Demo")
    print("   - Interactive step-by-step demonstration")
    print("   - Duration: ~15-20 minutes")
    print("   - Best for: Academic viva presentation")
    print()
    print("3. 🤖 Automated Complete Demo")
    print("   - Fully automated comprehensive demonstration")
    print("   - Duration: ~5-10 minutes")
    print("   - Best for: System validation and testing")
    print()
    print("4. 🎭 Complete System Demo")
    print("   - Detailed technical demonstration")
    print("   - Duration: ~10-15 minutes")
    print("   - Best for: Technical evaluation")
    print()
    print("5. 🔧 Generate Sample Assets")
    print("   - Create sample IT assets for testing")
    print("   - Duration: ~1 minute")
    print("   - Best for: Demo preparation")
    print()
    print("6. 📊 Run All Demos")
    print("   - Execute all demonstrations in sequence")
    print("   - Duration: ~30-40 minutes")
    print("   - Best for: Comprehensive evaluation")
    print()


def run_quick_demo():
    """Run the quick demonstration."""
    print("🚀 Starting Quick Demo...")
    try:
        from demo.quick_demo import quick_demo
        success = quick_demo()
        return success
    except Exception as e:
        print(f"❌ Quick demo failed: {e}")
        return False


def run_viva_presentation():
    """Run the viva presentation demonstration."""
    print("🎓 Starting Viva Presentation Demo...")
    try:
        from demo.viva_presentation_demo import VivaPresentationDemo
        demo = VivaPresentationDemo()
        results = demo.run_viva_presentation()
        return results['success']
    except Exception as e:
        print(f"❌ Viva presentation failed: {e}")
        return False


def run_automated_demo():
    """Run the automated complete demonstration."""
    print("🤖 Starting Automated Complete Demo...")
    try:
        from demo.automated_demo import AutomatedDemonstrator
        demonstrator = AutomatedDemonstrator(verbose=True)
        results = demonstrator.run_complete_automated_demo()
        return results['success']
    except Exception as e:
        print(f"❌ Automated demo failed: {e}")
        return False


def run_complete_system_demo():
    """Run the complete system demonstration."""
    print("🎭 Starting Complete System Demo...")
    try:
        from demo.demo_complete_system import SystemDemonstrator
        demonstrator = SystemDemonstrator()
        success = demonstrator.run_complete_demonstration()
        return success
    except Exception as e:
        print(f"❌ Complete system demo failed: {e}")
        return False


def generate_sample_assets():
    """Generate sample IT assets."""
    print("🔧 Generating Sample Assets...")
    try:
        from demo.sample_it_assets import SampleITAssetsGenerator
        generator = SampleITAssetsGenerator()
        demo_env = generator.generate_complete_demo_environment()
        print(f"✅ Generated {demo_env['total_devices']} sample assets")
        return True
    except Exception as e:
        print(f"❌ Sample asset generation failed: {e}")
        return False


def run_all_demos():
    """Run all demonstrations in sequence."""
    print("📊 Starting All Demonstrations...")
    
    demos = [
        ("Sample Assets Generation", generate_sample_assets),
        ("Quick Demo", run_quick_demo),
        ("Complete System Demo", run_complete_system_demo),
        ("Automated Demo", run_automated_demo),
    ]
    
    results = {}
    total_start = datetime.now()
    
    for demo_name, demo_func in demos:
        print(f"\n{'='*60}")
        print(f"Running: {demo_name}")
        print(f"{'='*60}")
        
        start_time = datetime.now()
        success = demo_func()
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        results[demo_name] = {
            'success': success,
            'duration': duration,
            'start_time': start_time,
            'end_time': end_time
        }
        
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"\n{status} {demo_name} ({duration:.2f}s)")
        
        if not success:
            print(f"⚠️ Stopping demo sequence due to failure in {demo_name}")
            break
    
    total_duration = (datetime.now() - total_start).total_seconds()
    
    # Print summary
    print(f"\n{'='*80}")
    print("DEMONSTRATION SEQUENCE SUMMARY")
    print(f"{'='*80}")
    
    passed = sum(1 for r in results.values() if r['success'])
    total = len(results)
    
    print(f"Total time: {total_duration:.2f} seconds")
    print(f"Demos completed: {total}")
    print(f"Demos passed: {passed}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    print(f"\nDetailed Results:")
    for demo_name, result in results.items():
        status = "✅ PASSED" if result['success'] else "❌ FAILED"
        print(f"  {status} {demo_name}: {result['duration']:.2f}s")
    
    all_passed = all(r['success'] for r in results.values())
    
    if all_passed:
        print(f"\n🎉 ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
        print(f"System is fully validated and ready for academic evaluation.")
    else:
        print(f"\n⚠️ Some demonstrations failed. Please review and fix issues.")
    
    return all_passed


def interactive_menu():
    """Run interactive menu for demo selection."""
    while True:
        print_banner()
        print_demo_menu()
        
        try:
            choice = input("Select demonstration (1-6) or 'q' to quit: ").strip().lower()
            
            if choice == 'q' or choice == 'quit':
                print("👋 Goodbye!")
                return True
            
            if choice == '1':
                success = run_quick_demo()
            elif choice == '2':
                success = run_viva_presentation()
            elif choice == '3':
                success = run_automated_demo()
            elif choice == '4':
                success = run_complete_system_demo()
            elif choice == '5':
                success = generate_sample_assets()
            elif choice == '6':
                success = run_all_demos()
            else:
                print("❌ Invalid choice. Please select 1-6 or 'q' to quit.")
                input("Press Enter to continue...")
                continue
            
            # Show result
            if success:
                print(f"\n✅ Demonstration completed successfully!")
            else:
                print(f"\n❌ Demonstration failed!")
            
            input("\nPress Enter to return to menu...")
            
        except KeyboardInterrupt:
            print(f"\n\n👋 Goodbye!")
            return True
        except Exception as e:
            print(f"\n❌ Error: {e}")
            input("Press Enter to continue...")


def main():
    """Main function for demo runner."""
    parser = argparse.ArgumentParser(
        description="Demo Runner for Secure Data Wiping System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python demo_runner.py                    # Interactive menu
  python demo_runner.py --quick           # Quick demo
  python demo_runner.py --viva            # Viva presentation
  python demo_runner.py --automated       # Automated demo
  python demo_runner.py --complete        # Complete system demo
  python demo_runner.py --assets          # Generate sample assets
  python demo_runner.py --all             # Run all demos
        """
    )
    
    parser.add_argument('--quick', action='store_true',
                       help='Run quick demonstration')
    parser.add_argument('--viva', action='store_true',
                       help='Run viva presentation demonstration')
    parser.add_argument('--automated', action='store_true',
                       help='Run automated complete demonstration')
    parser.add_argument('--complete', action='store_true',
                       help='Run complete system demonstration')
    parser.add_argument('--assets', action='store_true',
                       help='Generate sample IT assets')
    parser.add_argument('--all', action='store_true',
                       help='Run all demonstrations')
    
    args = parser.parse_args()
    
    # Check if any specific demo was requested
    if args.quick:
        return 0 if run_quick_demo() else 1
    elif args.viva:
        return 0 if run_viva_presentation() else 1
    elif args.automated:
        return 0 if run_automated_demo() else 1
    elif args.complete:
        return 0 if run_complete_system_demo() else 1
    elif args.assets:
        return 0 if generate_sample_assets() else 1
    elif args.all:
        return 0 if run_all_demos() else 1
    else:
        # No specific demo requested, run interactive menu
        return 0 if interactive_menu() else 1


if __name__ == "__main__":
    sys.exit(main())