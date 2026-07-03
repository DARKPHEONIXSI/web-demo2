#!/usr/bin/env python3
"""
Simple Flask server test script to verify the On Ice application is running.
This script checks if the Flask server is accessible and returns basic status.
"""
import sys
import os
from flask import Flask

# Add the current directory to the path so we can import app

if __name__ == "__main__":
    try:
        # Try to import and run the app
        from app import create_app
        
        # Create the Flask app
        app = create_app()
        
        # Try to get a test client to verify the app works
        with app.test_client() as client:
            # Try to access the home page
            response = client.get('/')
            
            if response.status_code == 200:
                print("✅ Flask server is running successfully!")
                print(f"Status code: {response.status_code}")
                
                # Check if we got actual content
                content = response.get_data(as_text=True)
                if len(content) > 100:
                    print(f"Content length: {len(content)} characters")
                    print("Content preview (first 100 chars):")
                    print(content[:100] + "...")
                else:
                    print(f"Content length: {len(content)} characters (too short, may be an error page)")
                
                # Try to access an API endpoint
                api_response = client.get('/api/get_posts')
                if api_response.status_code == 200:
                    print("✅ API endpoint /api/get_posts is working")
                else:
                    print(f"⚠️ API endpoint /api/get_posts returned status: {api_response.status_code}")
                
                sys.exit(0)
            else:
                print(f"❌ Server returned status code: {response.status_code}")
                sys.exit(1)
                
    except Exception as e:
        print(f"❌ Error starting Flask server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)