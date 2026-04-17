import requests
import json

def test_confidence_variation():
    """Test that confidence levels are varied and not all 55%"""
    try:
        # Test multiple endpoints to see confidence variation
        test_urls = [
            "http://127.0.0.1:8000/api/predictions/soccer_epl",
            "http://127.0.0.1:8000/api/predictions/nba",
            "http://127.0.0.1:8000/api/predictions/nfl"
        ]
        
        confidence_levels = []
        
        for url in test_urls:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 401:  # Auth required
                    print(f"Auth required for {url} - this is expected")
                    continue
                    
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    for pred in data[:3]:  # Check first 3 predictions
                        conf = pred.get('confidence', 0)
                        if conf > 0:
                            confidence_levels.append(conf)
                            print(f"Found confidence: {conf}%")
                            
            except Exception as e:
                print(f"Error testing {url}: {e}")
                
        if confidence_levels:
            unique_levels = set(confidence_levels)
            print(f"\nFound {len(unique_levels)} unique confidence levels:")
            for level in sorted(unique_levels):
                print(f"  {level}%")
                
            if len(unique_levels) > 1:
                print("✅ SUCCESS: Confidence levels are varied!")
            else:
                print("❌ ISSUE: All predictions have the same confidence")
        else:
            print("No confidence levels found in responses")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_confidence_variation()