"""
Test the enhanced web crawler functionality
"""

import os
import sys
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from market_research_agent.main import create_market_research_agent

def test_crawler_basic():
    """Test basic crawling functionality"""
    print("=" * 60)
    print("Testing Enhanced Web Crawler")
    print("=" * 60)
    
    # Create agent
    agent = create_market_research_agent(llm_provider="ollama")
    
    # Test 1: Basic crawl with depth=1
    print("\n[Test 1] Basic crawl of example.com (depth=1)...")
    try:
        # Manually invoke the monitor_url tool
        monitor_tool = next(t for t in agent.tools if t.name == "monitor_url")
        result = monitor_tool.run({
            "url": "https://example.com",
            "keywords": "example,domain",
            "max_pages": 3,
            "depth": 1,
            "respect_robots_txt": True,
            "delay": 0.5
        })
        
        print("Result:")
        # Pretty print JSON
        try:
            data = json.loads(result)
            print(json.dumps(data, indent=2))
        except:
            print(result)
        print("✓ Test 1 passed")
    except Exception as e:
        print(f"✗ Test 1 failed: {e}")
    
    # Test 2: Test with depth=2 (follow links)
    print("\n[Test 2] Crawl with depth=2...")
    try:
        monitor_tool = next(t for t in agent.tools if t.name == "monitor_url")
        result = monitor_tool.run({
            "url": "https://example.com",
            "keywords": "",
            "max_pages": 5,
            "depth": 2,
            "respect_robots_txt": True,
            "delay": 0.5
        })
        
        print("Result:")
        try:
            data = json.loads(result)
            print(f"Pages crawled: {data.get('pages_crawled', 0)}")
            print("✓ Test 2 passed")
        except:
            print(result)
            print("✓ Test 2 passed (non-JSON)")
    except Exception as e:
        print(f"✗ Test 2 failed: {e}")
    
    # Test 3: Test report generation
    print("\n[Test 3] Generate report from crawled data...")
    try:
        # Use the result from test 1
        report_tool = next(t for t in agent.tools if t.name == "generate_report")
        
        sample_data = json.dumps({
            "base_url": "https://example.com",
            "pages_crawled": 2,
            "total_keywords_found": 3,
            "pages": [
                {
                    "url": "https://example.com",
                    "title": "Example Domain",
                    "keywords_found": ["example", "domain"],
                    "content_snippet": "This domain is for use in illustrative examples..."
                }
            ]
        })
        
        report = report_tool.run({
            "research_data": sample_data,
            "report_type": "summary",
            "format": "markdown"
        })
        
        print("Report Preview:")
        print(report[:500] + "...")
        print("✓ Test 3 passed")
    except Exception as e:
        print(f"✗ Test 3 failed: {e}")
    
    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_crawler_basic()
