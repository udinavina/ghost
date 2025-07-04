#!/usr/bin/python3

"""
Local Turnstile Server Module
Navina Inc (c) 2025. All rights reserved.

Local HTTP server for serving clean Turnstile solving pages.
Inspired by Theyka's API approach but simplified for direct integration.
"""

import asyncio
import json
import uuid
import time
from typing import Dict, Optional, Any
from urllib.parse import urlparse, parse_qs
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver

class TurnstileRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Turnstile solving pages"""
    
    # Store active solving sessions
    sessions: Dict[str, Dict[str, Any]] = {}
    
    # Enhanced HTML template with better styling and functionality
    HTML_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Turnstile Verification</title>
        <script src="https://challenges.cloudflare.com/turnstile/v0/api.js?onload=onTurnstileLoad" async defer></script>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                color: #333;
            }
            
            .container {
                background: white;
                padding: 40px;
                border-radius: 16px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                text-align: center;
                max-width: 500px;
                width: 90%;
                position: relative;
                overflow: hidden;
            }
            
            .container::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, #667eea, #764ba2);
            }
            
            h1 {
                color: #2d3748;
                margin-bottom: 8px;
                font-size: 28px;
                font-weight: 600;
            }
            
            .subtitle {
                color: #718096;
                margin-bottom: 32px;
                font-size: 16px;
                line-height: 1.5;
            }
            
            .verification-area {
                background: #f8fafc;
                padding: 24px;
                border-radius: 12px;
                margin: 24px 0;
                border: 2px dashed #e2e8f0;
                transition: all 0.3s ease;
            }
            
            .verification-area:hover {
                border-color: #667eea;
                background: #f0f4ff;
            }
            
            .cf-turnstile {
                margin: 0 auto;
                display: inline-block;
            }
            
            .status {
                margin-top: 16px;
                padding: 12px;
                border-radius: 8px;
                font-weight: 500;
                transition: all 0.3s ease;
            }
            
            .status.waiting {
                background: #fef5e7;
                color: #d69e2e;
                border: 1px solid #f6e05e;
            }
            
            .status.success {
                background: #f0fff4;
                color: #38a169;
                border: 1px solid #68d391;
            }
            
            .status.error {
                background: #fed7d7;
                color: #e53e3e;
                border: 1px solid #fc8181;
            }
            
            .token-display {
                margin-top: 16px;
                padding: 12px;
                background: #edf2f7;
                border-radius: 8px;
                font-family: 'Monaco', 'Menlo', monospace;
                font-size: 12px;
                word-break: break-all;
                display: none;
            }
            
            .footer {
                margin-top: 24px;
                color: #a0aec0;
                font-size: 14px;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }
            
            .loading {
                animation: pulse 2s infinite;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1> Security Verification</h1>
            <p class="subtitle">Please complete the security check below to continue</p>
            
            <div class="verification-area">
                <!-- TURNSTILE_WIDGET -->
            </div>
            
            <div id="status" class="status waiting">
                <span id="status-text">Waiting for verification...</span>
            </div>
            
            <div id="token-display" class="token-display"></div>
            
            <div class="footer">
                <p>Powered by Cloudflare Turnstile</p>
            </div>
        </div>
        
        <script>
            let checkInterval;
            const statusEl = document.getElementById('status');
            const statusTextEl = document.getElementById('status-text');
            const tokenDisplayEl = document.getElementById('token-display');
            
            // Turnstile initialization
            window.onTurnstileLoad = function() {
                console.log('Turnstile API loaded');
                // Check if widget exists
                const widget = document.querySelector('.cf-turnstile');
                if (widget) {
                    console.log('Turnstile widget found, sitekey:', widget.dataset.sitekey);
                    
                    // Validate sitekey format
                    const sitekey = widget.dataset.sitekey;
                    if (!sitekey || sitekey.length < 10) {
                        updateStatus('error', 'Invalid sitekey format');
                        return;
                    }
                    
                    // For demo/test sitekeys
                    if (sitekey === '1x00000000000000000000AA' || sitekey === '3x00000000000000000000FF') {
                        console.log('Using demo/test sitekey - automatic pass expected');
                    } else if (sitekey.startsWith('0x4AAA')) {
                        console.log('Warning: This appears to be a placeholder sitekey');
                        updateStatus('error', 'Invalid sitekey - use a real sitekey or test with /test endpoint');
                    }
                }
            };
            
            // Turnstile callback functions
            window.turnstileCallback = function(token) {
                console.log('Turnstile token received:', token);
                updateStatus('success', 'Verification completed successfully!');
                showToken(token);
                
                // Send token to server
                fetch('/token', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        token: token, 
                        sessionId: getSessionId(),
                        timestamp: Date.now()
                    })
                }).then(response => response.json())
                  .then(data => console.log('Token sent to server:', data))
                  .catch(console.error);
                
                clearInterval(checkInterval);
            };
            
            window.turnstileError = function(error) {
                console.error('Turnstile error:', error);
                
                // Provide specific error feedback
                let errorMsg = 'Verification failed. ';
                if (error === 'invalid_sitekey') {
                    errorMsg += 'Invalid sitekey - this sitekey may not be valid for this domain.';
                } else if (error === 'network_error') {
                    errorMsg += 'Network error - check internet connection.';
                } else if (error === 'domain_mismatch') {
                    errorMsg += 'Domain mismatch - sitekey not valid for this domain.';
                } else {
                    errorMsg += `Error: ${error}`;
                }
                
                updateStatus('error', errorMsg);
            };
            
            window.turnstileExpired = function() {
                console.log('Turnstile expired');
                updateStatus('waiting', 'Verification expired. Please try again.');
            };
            
            window.turnstileTimeout = function() {
                console.log('Turnstile timeout');
                updateStatus('error', 'Verification timed out. Please refresh and try again.');
            };
            
            function updateStatus(type, message) {
                statusEl.className = `status ${type}`;
                statusTextEl.textContent = message;
            }
            
            function showToken(token) {
                tokenDisplayEl.textContent = `Token: ${token}`;
                tokenDisplayEl.style.display = 'block';
            }
            
            function getSessionId() {
                return '{{SESSION_ID}}';
            }
            
            // Monitor for token changes
            function monitorToken() {
                const tokenInput = document.querySelector('input[name="cf-turnstile-response"]');
                if (tokenInput && tokenInput.value) {
                    const token = tokenInput.value;
                    if (token && token.length > 10) {
                        turnstileCallback(token);
                        return;
                    }
                }
                
                // Check for invisible Turnstile completion
                const turnstileDiv = document.querySelector('.cf-turnstile');
                if (turnstileDiv) {
                    const iframe = turnstileDiv.querySelector('iframe');
                    if (iframe) {
                        // Turnstile is loaded, wait for completion
                        updateStatus('waiting', 'Processing verification...');
                    }
                }
            }
            
            // Start monitoring after page load
            window.addEventListener('load', function() {
                setTimeout(() => {
                    checkInterval = setInterval(monitorToken, 500);
                }, 1000);
            });
            
            // Monitor Turnstile widget loading
            document.addEventListener('DOMContentLoaded', function() {
                console.log('DOM loaded, monitoring Turnstile widget...');
                
                // Debug info
                const turnstileDiv = document.querySelector('.cf-turnstile');
                if (turnstileDiv) {
                    console.log('Turnstile div found with sitekey:', turnstileDiv.dataset.sitekey);
                } else {
                    console.error('No .cf-turnstile div found!');
                }
                
                // Check if Turnstile API is available
                setTimeout(() => {
                    if (window.turnstile) {
                        console.log('Turnstile API object available:', window.turnstile);
                    } else {
                        console.error('Turnstile API not loaded!');
                    }
                }, 3000);
                
                // Check widget status periodically
                let loadCheckCount = 0;
                const checkWidget = setInterval(() => {
                    loadCheckCount++;
                    const turnstileDiv = document.querySelector('.cf-turnstile');
                    const iframe = turnstileDiv ? turnstileDiv.querySelector('iframe') : null;
                    
                    if (iframe) {
                        console.log('Turnstile iframe detected');
                        clearInterval(checkWidget);
                        
                        // Check if it's invisible mode
                        const style = window.getComputedStyle(turnstileDiv);
                        if (style.width === '0px' || style.height === '0px') {
                            console.log('Invisible Turnstile detected');
                            updateStatus('waiting', 'Processing invisible verification...');
                        } else {
                            updateStatus('waiting', 'Please complete the verification');
                        }
                    } else if (loadCheckCount > 20) {
                        console.error('Turnstile widget failed to load after 10 seconds');
                        // Check for common issues
                        if (!window.turnstile) {
                            updateStatus('error', 'Turnstile API failed to load - check internet connection');
                        } else if (!turnstileDiv) {
                            updateStatus('error', 'Turnstile container not found');
                        } else {
                            updateStatus('error', 'Turnstile widget failed to render - invalid sitekey?');
                        }
                        clearInterval(checkWidget);
                    } else {
                        console.log(`Check ${loadCheckCount}: Widget not loaded yet...`);
                    }
                }, 500);
            });
        </script>
    </body>
    </html>
    """
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query_params = parse_qs(parsed_url.query)
            
            if path == '/':
                self._serve_index()
            elif path == '/solve':
                self._serve_solve_page(query_params)
            elif path == '/test':
                self._serve_test_page()
            elif path == '/status':
                self._serve_status(query_params)
            elif path.startswith('/session/'):
                session_id = path.split('/')[-1]
                self._serve_session_status(session_id)
            else:
                self._send_404()
                
        except Exception as e:
            print(f"Error handling GET request: {e}")
            self._send_error(500, str(e))
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            if path == '/token':
                self._handle_token_submission()
            else:
                self._send_404()
                
        except Exception as e:
            print(f"Error handling POST request: {e}")
            self._send_error(500, str(e))
    
    def _serve_index(self):
        """Serve index page from index.html file or fallback"""
        try:
            import os
            from pathlib import Path
            
            # Try to serve the server_index_simple.html file
            index_path = Path(__file__).parent.parent / 'server_index_simple.html'
            
            if index_path.exists():
                try:
                    with open(index_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    self._send_response(200, html_content, 'text/html')
                    return
                except Exception as e:
                    print(f"Error reading server_index.html: {e}")
        except Exception as e:
            print(f"Error in _serve_index: {e}")
        
        # Fallback to the original simple page
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Turnstile Solver Server</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                .endpoint { background: #f4f4f4; padding: 10px; margin: 10px 0; border-radius: 4px; }
                code { background: #eee; padding: 2px 4px; border-radius: 2px; }
            </style>
        </head>
        <body>
            <h1> Turnstile Solver Server</h1>
            <p>Local server for solving Cloudflare Turnstile challenges</p>
            
            <h2>Endpoints:</h2>
            <div class="endpoint">
                <strong>GET /solve?sitekey=&lt;key&gt;&amp;url=&lt;url&gt;</strong><br>
                Create a solving session and serve the Turnstile page
            </div>
            <div class="endpoint">
                <strong>GET /status?session=&lt;id&gt;</strong><br>
                Get the status of a solving session
            </div>
            <div class="endpoint">
                <strong>POST /token</strong><br>
                Receive solved tokens (internal)
            </div>
            
            <h2>Usage Example:</h2>
            <code>http://localhost:8888/solve?sitekey=0x4AAAAAAA&url=https://example.com</code>
            
            <h2>Active Sessions:</h2>
            <p>Total: {session_count}</p>
        </body>
        </html>
        """.format(session_count=len(self.sessions))
        
        self._send_response(200, html, 'text/html')
    
    def _serve_test_page(self):
        """Serve a test page with a known working Turnstile"""
        test_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Turnstile Test Page</title>
            <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; text-align: center; }
                .container { max-width: 600px; margin: 0 auto; }
                .status { margin: 20px 0; padding: 10px; background: #f0f0f0; border-radius: 4px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Turnstile Test Page</h1>
                <p>This page uses the Cloudflare demo sitekey for testing</p>
                
                <div class="cf-turnstile" 
                     data-sitekey="1x00000000000000000000AA"
                     data-callback="onSuccess"
                     data-error-callback="onError"
                     data-theme="light"></div>
                
                <div id="status" class="status">Waiting for Turnstile...</div>
            </div>
            
            <script>
                function onSuccess(token) {
                    document.getElementById('status').innerHTML = ' Success! Token: ' + token.substring(0, 50) + '...';
                }
                
                function onError(error) {
                    document.getElementById('status').innerHTML = ' Error: ' + error;
                }
                
                // Log when Turnstile loads
                window.addEventListener('load', function() {
                    console.log('Page loaded');
                    setTimeout(() => {
                        const widget = document.querySelector('.cf-turnstile iframe');
                        if (widget) {
                            console.log('Turnstile widget loaded successfully');
                        } else {
                            console.log('Turnstile widget not found');
                        }
                    }, 2000);
                });
            </script>
        </body>
        </html>
        """
        self._send_response(200, test_html, 'text/html')
    
    def _serve_solve_page(self, query_params):
        """Serve Turnstile solving page"""
        sitekey = query_params.get('sitekey', [''])[0]
        url = query_params.get('url', [''])[0]
        action = query_params.get('action', [''])[0]
        cdata = query_params.get('cdata', [''])[0]
        
        if not sitekey:
            self._send_error(400, "Missing required parameter: sitekey")
            return
        
        # Only allow real, solveable sitekeys - reject demo/test keys
        invalid_sitekeys = [
            '1x00000000000000000000AA',  # Demo key
            '2x00000000000000000000AB',  # Demo key  
            '3x00000000000000000000FF',  # Demo key
            '0x4AAAAAAA',                # Placeholder
            'YOUR_SITE_KEY',             # Placeholder
        ]
        
        # Validate sitekey
        if sitekey in invalid_sitekeys:
            error_msg = {
                "error": "Invalid sitekey - Demo/Test key not supported",
                "message": f"Sitekey '{sitekey}' is a demo/test key that won't work for real solving",
                "reason": "Demo keys are domain-restricted and don't require real solving",
                "solution": "Extract a real sitekey from a live Turnstile-protected site",
                "example": "python main.py https://real-site.com --extract-sitekey"
            }
            self._send_error(400, error_msg)
            return
        
        # Validate real sitekey format
        if not (len(sitekey) >= 20 and sitekey.startswith(('1x', '0x'))):
            error_msg = {
                "error": "Invalid sitekey format",
                "message": f"Sitekey '{sitekey}' does not match Cloudflare Turnstile format",
                "expected_format": "Real Turnstile sitekeys start with '1x' or '0x' and are 20+ characters",
                "solution": "Use a real sitekey from an actual Turnstile-protected website"
            }
            self._send_error(400, error_msg)
            return
        
        # Validate URL is provided for domain context
        if not url:
            error_msg = {
                "error": "Missing URL parameter",
                "message": "URL parameter is required for proper Turnstile domain validation",
                "solution": "Provide the original URL where this sitekey was found"
            }
            self._send_error(400, error_msg)
            return
        
        # Create session
        session_id = str(uuid.uuid4())
        session_data = {
            'id': session_id,
            'sitekey': sitekey,
            'url': url,
            'action': action,
            'cdata': cdata,
            'created_at': time.time(),
            'status': 'waiting',
            'token': None,
            'attempts': 0
        }
        
        self.sessions[session_id] = session_data
        
        # Extract domain from URL for proper origin handling
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        origin_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Build Turnstile widget HTML with proper domain context
        widget_attrs = [
            f'data-sitekey="{sitekey}"',
            f'data-theme="light"',
            f'data-size="normal"'
        ]
        
        if action:
            widget_attrs.append(f'data-action="{action}"')
        if cdata:
            widget_attrs.append(f'data-cdata="{cdata}"')
        
        # Add callbacks for comprehensive handling
        widget_attrs.extend([
            'data-callback="turnstileCallback"',
            'data-error-callback="turnstileError"',
            'data-expired-callback="turnstileExpired"',
            'data-timeout-callback="turnstileTimeout"'
        ])
        
        turnstile_html = f'<div class="cf-turnstile" {" ".join(widget_attrs)}></div>'
        
        # Replace placeholder in template
        page_html = self.HTML_TEMPLATE.replace('<!-- TURNSTILE_WIDGET -->', turnstile_html)
        
        # Add session ID to template
        page_html = page_html.replace('{{SESSION_ID}}', session_id)
        
        self._send_response(200, page_html, 'text/html')
        print(f" Created solving session: {session_id} for sitekey: {sitekey[:20]}...")
    
    def _serve_status(self, query_params):
        """Serve session status"""
        session_id = query_params.get('session', [''])[0]
        if not session_id or session_id not in self.sessions:
            self._send_error(404, "Session not found")
            return
        
        session_data = self.sessions[session_id]
        self._send_json_response(session_data)
    
    def _serve_session_status(self, session_id):
        """Serve specific session status"""
        if session_id not in self.sessions:
            self._send_error(404, "Session not found")
            return
        
        session_data = self.sessions[session_id]
        self._send_json_response(session_data)
    
    def _handle_token_submission(self):
        """Handle token submission from solved Turnstile"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            session_id = data.get('sessionId')
            token = data.get('token')
            
            if session_id in self.sessions:
                self.sessions[session_id]['token'] = token
                self.sessions[session_id]['status'] = 'completed'
                self.sessions[session_id]['completed_at'] = time.time()
                
                print(f" Token received for session {session_id}: {token[:20]}...")
                
                self._send_json_response({'success': True, 'message': 'Token received'})
            else:
                self._send_error(404, "Session not found")
                
        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON data")
    
    def _send_response(self, status_code, content, content_type='text/plain'):
        """Send HTTP response"""
        try:
            self.send_response(status_code)
            self.send_header('Content-type', content_type)
            self.send_header('Content-Length', str(len(content.encode('utf-8'))))
            # Add CORS headers for better compatibility
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except BrokenPipeError:
            # Client disconnected, ignore silently
            pass
        except ConnectionResetError:
            # Client reset connection, ignore silently
            pass
        except Exception as e:
            # Only log unexpected errors
            error_str = str(e)
            if "Broken pipe" not in error_str and "Connection reset" not in error_str:
                print(f"Error sending response: {e}")
            # Don't try to send error response as connection may be broken
    
    def _send_json_response(self, data):
        """Send JSON response"""
        json_data = json.dumps(data, indent=2)
        self._send_response(200, json_data, 'application/json')
    
    def _send_error(self, status_code, message):
        """Send error response"""
        if isinstance(message, dict):
            error_data = message
            error_data['status'] = status_code
        else:
            error_data = {'error': message, 'status': status_code}
        
        json_data = json.dumps(error_data, indent=2)
        self._send_response(status_code, json_data, 'application/json')
    
    def _send_404(self):
        """Send 404 response"""
        self._send_error(404, "Not found")
    
    def log_message(self, format, *args):
        """Override to reduce logging noise"""
        # Only log errors and important events
        message = format % args
        if any(x in message.lower() for x in ['error', 'exception', 'solve', 'token']):
            print(f"Server: {message}")
        # Suppress routine GET/POST requests

class TurnstileServer:
    """Local Turnstile solving server"""
    
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
        self.running = False
    
    def start(self):
        """Start the server in a background thread"""
        if self.running:
            return
        
        try:
            # Create server
            self.server = HTTPServer((self.host, self.port), TurnstileRequestHandler)
            
            # Start in background thread
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            
            self.running = True
            print(f" Turnstile server started at http://{self.host}:{self.port}")
            return True
            
        except Exception as e:
            print(f" Failed to start Turnstile server: {e}")
            return False
    
    def stop(self):
        """Stop the server"""
        if not self.running:
            return
        
        try:
            if self.server:
                self.server.shutdown()
                self.server.server_close()
            
            if self.server_thread:
                self.server_thread.join(timeout=5)
            
            self.running = False
            print(" Turnstile server stopped")
            
        except Exception as e:
            print(f" Error stopping server: {e}")
    
    def get_solve_url(self, sitekey: str, url: str, action: str = None, cdata: str = None) -> str:
        """Generate solving URL for given parameters"""
        params = [f"sitekey={sitekey}", f"url={url}"]
        if action:
            params.append(f"action={action}")
        if cdata:
            params.append(f"cdata={cdata}")
        
        return f"http://{self.host}:{self.port}/solve?{'&'.join(params)}"
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a solving session"""
        if hasattr(TurnstileRequestHandler, 'sessions'):
            return TurnstileRequestHandler.sessions.get(session_id)
        return None
    
    def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get all active sessions"""
        if hasattr(TurnstileRequestHandler, 'sessions'):
            return TurnstileRequestHandler.sessions.copy()
        return {}
    
    def cleanup_old_sessions(self, max_age_seconds: int = 3600):
        """Clean up old sessions"""
        if not hasattr(TurnstileRequestHandler, 'sessions'):
            return
        
        current_time = time.time()
        to_remove = []
        
        for session_id, session_data in TurnstileRequestHandler.sessions.items():
            if current_time - session_data['created_at'] > max_age_seconds:
                to_remove.append(session_id)
        
        for session_id in to_remove:
            del TurnstileRequestHandler.sessions[session_id]
        
        if to_remove:
            print(f" Cleaned up {len(to_remove)} old sessions")

# Global server instance
_global_server = None

def get_turnstile_server(host='localhost', port=8888) -> TurnstileServer:
    """Get or create global Turnstile server instance"""
    global _global_server
    
    if _global_server is None:
        _global_server = TurnstileServer(host, port)
    
    return _global_server

def start_turnstile_server(host='localhost', port=8888) -> TurnstileServer:
    """Start the global Turnstile server"""
    server = get_turnstile_server(host, port)
    server.start()
    return server

if __name__ == "__main__":
    # Test the server
    server = TurnstileServer()
    try:
        server.start()
        print("Server running. Press Ctrl+C to stop.")
        print("Visit: http://localhost:8888")
        print("Test: http://localhost:8888/solve?sitekey=0x4AAAAAAA&url=https://example.com")
        
        # Keep running
        import signal
        import sys
        
        def signal_handler(sig, frame):
            print("\nShutting down server...")
            server.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        server.stop()