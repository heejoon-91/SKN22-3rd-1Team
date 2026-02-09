"""최소 테스트 - import만 확인"""
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print("Step 1: Importing dur_client...")
try:
    from src.api.dur_client import search_dur_by_ingredient
    print("✓ dur_client imported successfully")
except Exception as e:
    print(f"✗ dur_client import failed: {e}")
    import traceback
    traceback.print_exc()

print("\nStep 2: Testing DUR search...")
try:
    results = search_dur_by_ingredient("acetaminophen")
    print(f"✓ DUR search completed: {len(results)} results")
except Exception as e:
    print(f"✗ DUR search failed: {e}")
    import traceback
    traceback.print_exc()

print("\nTest complete!")
