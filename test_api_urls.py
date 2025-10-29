"""
Test script to check API URL patterns and test the provide_feedback endpoint.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projetPython.settings')
django.setup()

from django.urls import get_resolver
from django.contrib.auth import get_user_model

def list_api_urls():
    """List all API URL patterns."""
    print("\n" + "="*80)
    print("CHECKING API URL PATTERNS")
    print("="*80)
    
    resolver = get_resolver()
    api_patterns = []
    
    def extract_patterns(url_patterns, prefix=''):
        for pattern in url_patterns:
            if hasattr(pattern, 'url_patterns'):
                # This is an included URLconf
                new_prefix = prefix + str(pattern.pattern)
                extract_patterns(pattern.url_patterns, new_prefix)
            else:
                # This is a URL pattern
                full_pattern = prefix + str(pattern.pattern)
                if 'api' in full_pattern:
                    api_patterns.append({
                        'pattern': full_pattern,
                        'name': pattern.name if hasattr(pattern, 'name') else None,
                        'callback': pattern.callback if hasattr(pattern, 'callback') else None
                    })
    
    extract_patterns(resolver.url_patterns)
    
    if api_patterns:
        print(f"\n✅ Found {len(api_patterns)} API URL patterns:")
        for i, p in enumerate(api_patterns, 1):
            print(f"  {i}. {p['pattern']}")
            if p['name']:
                print(f"     Name: {p['name']}")
    else:
        print("\n❌ No API URL patterns found!")
    
    # Check specifically for recommendations endpoints
    print("\n" + "-"*80)
    print("RECOMMENDATIONS ENDPOINTS:")
    print("-"*80)
    reco_patterns = [p for p in api_patterns if 'recommendation' in p['pattern']]
    if reco_patterns:
        for p in reco_patterns:
            print(f"  ✓ {p['pattern']}")
    else:
        print("  ❌ No recommendation endpoints found!")
    
    return api_patterns

def test_recommendation_exists():
    """Check if we have recommendations in the database."""
    from reco.models import Recommendation
    
    print("\n" + "="*80)
    print("CHECKING RECOMMENDATIONS IN DATABASE")
    print("="*80)
    
    recos = Recommendation.objects.all().order_by('-created_at')[:5]
    print(f"\n✅ Found {recos.count()} recommendations (showing first 5):")
    for reco in recos:
        print(f"  • ID: {reco.id} | User: {reco.user.username} | Category: {reco.category}")
        print(f"    Text: {reco.text[:60]}...")
    
    return list(recos)

def test_user_authentication():
    """Check if we have authenticated users."""
    User = get_user_model()
    
    print("\n" + "="*80)
    print("CHECKING USERS")
    print("="*80)
    
    users = User.objects.all()[:5]
    print(f"\n✅ Found {users.count()} users (showing first 5):")
    for user in users:
        reco_count = user.recommendation_set.count() if hasattr(user, 'recommendation_set') else 0
        print(f"  • Username: {user.username} | Recommendations: {reco_count}")
    
    return list(users)

if __name__ == '__main__':
    print("\n" + "="*80)
    print(" API DIAGNOSTICS FOR RECO SYSTEM")
    print("="*80)
    
    # List all API URLs
    urls = list_api_urls()
    
    # Check recommendations
    recos = test_recommendation_exists()
    
    # Check users
    users = test_user_authentication()
    
    print("\n" + "="*80)
    print("DIAGNOSIS COMPLETE")
    print("="*80)
    
    # Final summary
    print("\n📋 SUMMARY:")
    print(f"  • API URLs found: {len(urls)}")
    print(f"  • Recommendations in DB: {len(recos)}")
    print(f"  • Users in DB: {len(users)}")
    
    # Check for the specific endpoint
    provide_feedback_urls = [u for u in urls if 'provide_feedback' in u['pattern']]
    if provide_feedback_urls:
        print(f"\n  ✅ provide_feedback endpoint found:")
        for u in provide_feedback_urls:
            print(f"     {u['pattern']}")
    else:
        print(f"\n  ❌ provide_feedback endpoint NOT found in URL patterns!")
        print(f"     This means the @action decorator might not be working properly.")
    
    print("\n" + "="*80)
