#!/usr/bin/env python3
"""
Build the index of all crawled results for GitHub Pages.
Used by GitHub Actions workflow.
"""
import os
import json
import glob
from datetime import datetime

def main():
    """Main function to build the index."""
    print("Building index of crawled results...")
    
    # Ensure docs directory exists
    os.makedirs('docs', exist_ok=True)
    
    # Find all JSON files in the data directory
    json_files = glob.glob('data/**/*.json', recursive=True)
    print(f"Found {len(json_files)} JSON files in data directory")
    
    # Read each file and extract basic info
    results = []
    for file_path in json_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
                # Handle both single objects and lists
                if isinstance(data, list):
                    results.extend(data)
                else:
                    results.append(data)
        except Exception as e:
            print(f"Error reading {file_path}: {str(e)}")
    
    print(f"Processed {len(results)} total results")
    
    # Sort by crawl time if available
    results.sort(key=lambda x: x.get('crawl_time', ''), reverse=True)
    
    # Limit to 1000 results to keep file size reasonable
    if len(results) > 1000:
        results = results[:1000]
        print(f"Limited to 1000 most recent results")
    
    # Add timestamp for the index
    index_data = {
        "last_updated": datetime.now().isoformat(),
        "total_results": len(results),
        "results": results
    }
    
    # Write index file
    try:
        with open('docs/index.json', 'w') as f:
            json.dump(index_data, f)
        print(f"Successfully created index with {len(results)} results")
    except Exception as e:
        print(f"Error writing index file: {str(e)}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code) 