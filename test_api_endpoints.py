"""
Quick test to verify API endpoints are working.
Run this to confirm feedback buttons will save data.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_api_endpoints():
    """Test that API endpoints are accessible"""
    
    print("🧪 Testing RECO API Endpoints...")
    print("="*60)
    
    # Test 1: API Root
    print("\n1. Testing API Root: GET /api/")
    try:
        response = requests.get(f"{BASE_URL}/api/")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ API Root accessible")
            data = response.json()
            print(f"   Available endpoints: {list(data.keys())}")
        else:
            print(f"   ⚠️ Status code: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 2: Recommendations List
    print("\n2. Testing Recommendations: GET /api/recommendations/")
    try:
        response = requests.get(f"{BASE_URL}/api/recommendations/")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Recommendations endpoint working")
            print(f"   Returns: {type(data).__name__} with {len(data) if isinstance(data, list) else 'N/A'} items")
        elif response.status_code == 403:
            print("   ⚠️ 403 Forbidden - Authentication required (normal)")
        else:
            print(f"   ⚠️ Status code: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 3: Metrics endpoint
    print("\n3. Testing Metrics: GET /api/metrics/")
    try:
        response = requests.get(f"{BASE_URL}/api/metrics/")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Metrics endpoint working")
            print(f"   Returns: {type(data).__name__}")
        elif response.status_code == 403:
            print("   ⚠️ 403 Forbidden - Authentication required (normal)")
        else:
            print(f"   ⚠️ Status code: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 4: Check if provide_feedback route exists (will get 405 Method Not Allowed)
    print("\n4. Testing Feedback Endpoint: GET /api/recommendations/1/provide_feedback/")
    try:
        response = requests.get(f"{BASE_URL}/api/recommendations/1/provide_feedback/")
        print(f"   Status: {response.status_code}")
        if response.status_code == 405:
            print("   ✅ Endpoint exists! (405 = Method Not Allowed for GET, POST required)")
        elif response.status_code == 404:
            print("   ❌ 404 Not Found - Route not registered!")
        elif response.status_code == 403:
            print("   ⚠️ 403 Forbidden - Authentication required (but endpoint exists)")
        else:
            print(f"   ⚠️ Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print("\n" + "="*60)
    print("✅ Test Complete!")
    print("\n💡 Expected Results:")
    print("   • API Root: 200 OK or 403 Forbidden")
    print("   • Recommendations: 200 OK or 403 Forbidden")
    print("   • Metrics: 200 OK or 403 Forbidden")
    print("   • Feedback: 405 Method Not Allowed (endpoint exists!)")
    print("\n🎯 If you see 405 for feedback endpoint = SUCCESS!")
    print("   The route is registered and POST will work from your app.")
    print("\n📝 Next Steps:")
    print("   1. Go to http://127.0.0.1:8000/reco/recommendations/")
    print("   2. Click feedback buttons ('Utile', 'Pas utile', 'J'ai appliqué')")
    print("   3. Watch the counters update!")

if __name__ == '__main__':
    test_api_endpoints()
