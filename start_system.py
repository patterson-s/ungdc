#!/usr/bin/env python
"""
Simple script to start the UNGDC system
"""
import subprocess
import sys
import os
import time

def main():
    print("Starting UNGDC System")
    print("=" * 50)
    
    # Change to the ungdc_web directory
    os.chdir("C:\\Users\\spatt\\Desktop\\ungdc\\ungdc_web")
    
    print("Starting API server...")
    # Start the API server
    api_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for API to start
    time.sleep(3)
    
    print("Starting web server...")
    # Start the web server
    web_process = subprocess.Popen(
        [sys.executable, "-m", "http.server", "8080", "--directory", "web"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    print("\n" + "=" * 50)
    print("System is running!")
    print("- API: http://localhost:8000")
    print("- Web Interface: http://localhost:8080")
    print("- API Docs: http://localhost:8000/docs")
    print("\nPress Enter to stop the system...")
    
    try:
        input()
    except KeyboardInterrupt:
        pass
    
    print("\nStopping system...")
    api_process.terminate()
    web_process.terminate()
    api_process.wait()
    web_process.wait()
    print("System stopped.")

if __name__ == "__main__":
    main()