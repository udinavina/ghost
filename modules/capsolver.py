#!/usr/bin/python3

"""
CapsSolver API Integration Module
Navina Inc (c) 2025. All rights reserved.
"""

import time
import requests
import toml
from pathlib import Path

class CapsSolver:
    """CapsSolver API integration for CAPTCHA solving"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or self._load_api_key()
        self.base_url = "https://api.capsolver.com"
        self.session = requests.Session()
        
    def _load_api_key(self):
        """Load API key from config file"""
        try:
            config_path = Path(".ghost/config.toml")
            if config_path.exists():
                config = toml.load(config_path)
                return config.get('capsolver', {}).get('api_key')
        except Exception as e:
            print(f"Error loading CapsSolver config: {e}")
        return None
        
    def create_task(self, task_data):
        """Create a new task"""
        url = f"{self.base_url}/createTask"
        data = {
            "clientKey": self.api_key,
            "task": task_data
        }
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def get_task_result(self, task_id):
        """Get task result"""
        url = f"{self.base_url}/getTaskResult"
        data = {
            "clientKey": self.api_key,
            "taskId": task_id
        }
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def solve_turnstile(self, website_url, website_key, action=None, cdata=None, page_data=None):
        """Solve Cloudflare Turnstile CAPTCHA"""
        if not self.api_key:
            print("No CapsSolver API key available")
            return None
            
        print(f"CapsSolver: Starting Turnstile solve...")
        print(f"  Website: {website_url}")
        print(f"  Site Key: {website_key}")
        
        task_data = {
            "type": "AntiTurnstileTaskProxyLess",
            "websiteURL": website_url,
            "websiteKey": website_key,
            "metadata": {}
        }
        
        # Add optional parameters to metadata
        if action:
            task_data["metadata"]["action"] = action
        if cdata:
            task_data["metadata"]["cdata"] = cdata
        if page_data:
            task_data["metadata"]["pageData"] = page_data
        
        try:
            # Create task
            create_result = self.create_task(task_data)
            
            if create_result.get('errorId') != 0:
                print(f"  Error creating task: {create_result.get('errorDescription')}")
                return None
            
            task_id = create_result['taskId']
            print(f"  Task created with ID: {task_id}")
            
            # Poll for result
            max_attempts = 60  # 5 minutes max
            for attempt in range(max_attempts):
                time.sleep(5)  # Wait 5 seconds between polls
                
                result = self.get_task_result(task_id)
                
                if result.get('errorId') != 0:
                    print(f"  Error getting result: {result.get('errorDescription')}")
                    return None
                
                status = result.get('status')
                print(f"  Attempt {attempt + 1}: Status = {status}")
                
                if status == 'ready':
                    token = result['solution']['token']
                    print(f"  Success! Token received: {token[:50]}...")
                    return token
                elif status == 'failed':
                    print(f"  Task failed: {result.get('errorDescription', 'Unknown error')}")
                    return None
                # Continue polling if status is 'processing'
            
            print("  Timeout: Task did not complete within 5 minutes")
            return None
            
        except Exception as e:
            print(f"  Exception during solving: {e}")
            return None