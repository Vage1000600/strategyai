"""
Vercel Serverless Function Wrapper for Streamlit
This allows Streamlit to run on Vercel's serverless infrastructure
"""

import subprocess
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time

# Install streamlit if not already installed
def install_streamlit():
    try:
        import streamlit
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'streamlit'])

# Start Streamlit server
def start_streamlit():
    install_streamlit()
    
    # Get port from Vercel or use default
    port = int(os.environ.get('PORT', 8501))
    
    # Run Streamlit
    cmd = [
        sys.executable, '-m', 'streamlit', 'run',
        'app.py',
        '--server.port', str(port),
        '--server.address', '0.0.0.0',
        '--server.headless', 'true',
        '--browser.gatherUsageStats', 'false'
    ]
    
    subprocess.run(cmd)

# Vercel handler
def handler(request):
    """Vercel serverless handler"""
    start_streamlit()
    
    return {
        'statusCode': 200,
        'body': 'Streamlit app started'
    }

# For local testing
if __name__ == '__main__':
    start_streamlit()
