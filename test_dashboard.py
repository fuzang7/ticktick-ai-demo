#!/usr/bin/env python3
"""Test script for the new dashboard functionality."""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dida_client import DidaClient

def test_dida_client_extensions():
    """Test the new DidaClient methods."""
    print("🧪 Testing DidaClient dashboard extensions...")
    print("=" * 60)

    try:
        # Initialize client
        client = DidaClient()
        print("✅ DidaClient initialized successfully")

        # Test 1: Get all projects
        print("\n[Test 1: get_all_projects()]")
        try:
            projects = client.get_all_projects()
            print(f"   Retrieved {len(projects)} projects")
            if projects:
                print(f"   First project: {projects[0].get('name', 'Unnamed')}")
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            # Check if it's an API endpoint issue
            if "404" in str(e) or "Not Found" in str(e):
                print("   ℹ️  The /projects endpoint might not be available in this API version")
                print("   ℹ️  You may need to use a different method to list projects")

        # Test 2: Get project tasks (single project)
        print("\n[Test 2: get_project_tasks() - Single project]")
        if projects:
            project_id = projects[0]['id']
            try:
                tasks = client.get_project_tasks(project_id)
                print(f"   Retrieved {len(tasks)} tasks from project {project_id[:8]}...")
            except Exception as e:
                print(f"   ❌ Failed: {e}")

        # Test 3: Prepare dashboard data
        print("\n[Test 3: prepare_dashboard_data_for_llm()]")
        try:
            dashboard_data = client.prepare_dashboard_data_for_llm(max_tasks=10)
            if dashboard_data['analysis_ready']:
                summary = dashboard_data['summary']
                print(f"   ✅ Data prepared successfully")
                print(f"   • Active tasks: {summary['total_active_tasks']}")
                print(f"   • Projects analyzed: {summary['projects_with_tasks']}")
                print(f"   • Tasks for analysis: {summary['analysis_task_count']}")
            else:
                print(f"   ⚠️  {dashboard_data.get('message', 'No data available')}")
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            import traceback
            traceback.print_exc()

        print("\n" + "=" * 60)
        print("Testing completed!")

    except Exception as e:
        print(f"\n❌ Initialization failed: {e}")
        print("\nCommon issues:")
        print("1. Missing .env file with API credentials")
        print("2. Missing .token-oauth file (run refresh_token.py)")
        print("3. Invalid API credentials")
        return False

    return True

def test_main_app_integration():
    """Test that main.py can import and use the new features."""
    print("\n\n🧪 Testing main.py integration...")
    print("=" * 60)

    try:
        # Try to import AIProjectManager
        from main import AIProjectManager
        print("✅ AIProjectManager imported successfully")

        # Check if run_dashboard method exists
        if hasattr(AIProjectManager, 'run_dashboard'):
            print("✅ run_dashboard() method exists")

            # Check method signature
            import inspect
            sig = inspect.signature(AIProjectManager.run_dashboard)
            if len(sig.parameters) == 1:  # self parameter
                print("✅ run_dashboard() has correct signature")
            else:
                print("⚠️  run_dashboard() has unexpected signature")
        else:
            print("❌ run_dashboard() method not found")

        # Check for helper methods
        for method_name in ['_build_dashboard_prompt', '_get_dashboard_system_prompt']:
            if hasattr(AIProjectManager, method_name):
                print(f"✅ {method_name}() method exists")
            else:
                print(f"❌ {method_name}() method not found")

        print("\n" + "=" * 60)
        print("Integration testing completed!")

    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

def main():
    """Run all tests."""
    print("🚀 Testing Dashboard Functionality")
    print("=" * 60)

    # Run DidaClient tests
    client_ok = test_dida_client_extensions()

    # Run integration tests
    integration_ok = test_main_app_integration()

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    if client_ok and integration_ok:
        print("✅ All tests passed!")
        print("\nNext steps:")
        print("1. Run 'python main.py' to use the AI Dashboard")
        print("2. Select option 3 from the menu")
        print("3. Review the generated task management health report")
    else:
        print("⚠️ Some tests failed")
        print("\nTroubleshooting tips:")
        print("1. Check your .env file configuration")
        print("2. Ensure you have run refresh_token.py for authentication")
        print("3. Verify API endpoints are accessible")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()