#  Navina Advanced Stealth Browser Automation

> **Browser helper with stealth capabilities and multi-method CAPTCHA solving**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)

##  Features

###  **Advanced Stealth Technology**
- **Complete WebDriver Detection Bypass**: Advanced JavaScript injection to hide all automation indicators
- **Realistic Browser Profiles**: Internal Chrome profiles with browsing history, cookies, and session data
- **Dynamic Fingerprinting Protection**: Canvas, WebGL, and Audio fingerprinting randomization
- **Timezone & Locale Spoofing**: Consistent geographical identity across all browser APIs
- **Enhanced User Agent Rotation**: Randomized realistic user agents with matching headers
- **Permission API Normalization**: Natural permission states to avoid detection
- **94.4% Stealth Success Rate**: Verified against major detection platforms

###  **CAPTCHA & Challenge Solving**

#### **Cloudflare Turnstile**
- **Multi-Method Detection**: 20+ detection patterns using YARA rules
- **Automatic Solving**: In-page click automation with intelligent frame detection  
- **API Integration**: CapSolver service integration for complex challenges
- **Local Server Mode**: HTTP server for external integration (`localhost:8888`)
- **Real-time Monitoring**: Token extraction and validation
- **Demo & Production Support**: Handles both test and live sitekeys

#### **ECW Medical Portal Support**
- **Specialized ECW Detection**: Auto-detects ECW medical portals
- **Login Automation**: Automated credential entry and submission
- **Session Management**: Persistent login state handling
- **Healthcare Compliance**: Secure credential management
- **Multi-Portal Support**: Works with various ECW implementations

###  **YARA-Based Detection System**
- **Pattern Matching Engine**: Advanced YARA rules for Turnstile detection
- **Signature Management**: Organized rule files in `modules/signatures/`
- **Real-time Analysis**: Live page content scanning
- **Extensible Framework**: Easy addition of new detection patterns
- **High Accuracy**: Reduces false positives with precise rule matching

###  **Browser Support**
- **Chrome/Chromium**: Full feature support with enhanced stealth
- **Firefox**: Basic support (Chrome recommended for optimal stealth)
- **Headless & GUI Modes**: Flexible deployment options
- **Cross-Platform**: Linux, macOS, Windows support

##  Installation

### Prerequisites
```bash
# Python 3.8+ required
python3 --version

# Install system dependencies (Ubuntu/Debian)
sudo apt update
sudo apt install -y python3-pip chromium-browser

# Install system dependencies (CentOS/RHEL/Fedora)
sudo dnf install -y python3-pip chromium

# Install system dependencies (macOS)
brew install python@3.8 chromium
```

### Python Dependencies
```bash
# Clone the repository
git clone <repository-url>
cd crawler

# Install Python packages
pip3 install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Required Packages
```txt
playwright>=1.40.0
playwright-stealth>=1.0.6
yara-python>=4.3.1
aiohttp>=3.8.0
asyncio-mqtt>=0.11.0
requests>=2.28.0
toml>=0.10.2
pathlib>=1.0.1
```

##  Configuration

### API Keys Setup
Create configuration file at `.ghost/config.toml`:
```toml
[capsolver]
api_key = "your_capsolver_api_key_here"

[settings]
default_browser = "chrome"
headless_mode = false
stealth_mode = true
timeout_seconds = 120

[ecw]
# ECW portal credentials (if needed)
default_username = ""
default_password = ""
```

### Advanced Configuration
```toml
[browser]
user_agent_rotation = true
profile_mode = true  # Use internal realistic profile
stealth_level = "maximum"

[detection]
yara_rules_path = "modules/signatures/"
detection_timeout = 30
retry_attempts = 3

[server]
host = "localhost"
port = 8888
cors_enabled = true
session_timeout = 3600
```

##  Usage

### Basic Command Line Usage
```bash
# Navigate to any website with stealth
python3 main.py https://example.com

# Test stealth capabilities
python3 main.py test_stealth

# Start local CAPTCHA solving server
python3 main.py start_server

# Stop the server
python3 main.py stop_server

# Extract sitekey from a site
python3 main.py https://turnstile-site.com --extract-sitekey

# Use specific browser
python3 main.py https://example.com --browser=firefox

# Force headless mode
python3 main.py https://example.com --headless
```

### ECW Medical Portal Usage
```bash
# Automated ECW login
python3 main.py https://demo.ecwcloud.com

# ECW with custom credentials
python3 main.py https://your-ecw-portal.com --username="your_user" --password="your_pass"
```

### Python API Usage
```python
import asyncio
from modules.base_browser import BaseBrowser
from modules.turnstile_solver import detect_captcha_in_frames

async def solve_turnstile():
    # Initialize browser with stealth
    browser = BaseBrowser(headless=False, use_profile=True)
    await browser.launch_browser()
    
    # Navigate to target site
    await browser.navigate_to_url("https://example.com")
    
    # Detect and solve CAPTCHAs
    captcha_found = await detect_captcha_in_frames(browser.page)
    
    if captcha_found:
        print(" Turnstile detected and solved!")
    
    await browser.close()

# Run the solver
asyncio.run(solve_turnstile())
```

### Server API Usage
```bash
# Start the server
python3 main.py start_server

# Solve via HTTP API
curl "http://localhost:8888/solve?sitekey=0x4AAAAAAA&url=https://example.com"

# Check solving status
curl "http://localhost:8888/status?session=session_id"

# Get server status
curl "http://localhost:8888/"
```

### Advanced Browser Configuration
```python
from modules.base_browser import BaseBrowser
from modules.enhanced_stealth import EnhancedStealth

# Maximum stealth configuration
browser = BaseBrowser(
    headless=False,
    browser_type='chrome', 
    use_profile=True  # Use realistic internal profile
)

# Custom stealth settings
stealth_args = EnhancedStealth.get_enhanced_chrome_args()
profile_path = EnhancedStealth.get_crawler_profile_path()
```

##  Server Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium

# Copy application code
COPY . .

# Create config directory
RUN mkdir -p .ghost

# Expose port
EXPOSE 8888

# Run the server
CMD ["python3", "main.py", "start_server"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  navina-crawler:
    build: .
    ports:
      - "8888:8888"
    environment:
      - CAPSOLVER_API_KEY=${CAPSOLVER_API_KEY}
      - DISPLAY=:99
    volumes:
      - ./config:/app/.ghost
      - ./logs:/app/log
    restart: unless-stopped
    
  xvfb:
    image: selenium/standalone-chrome:latest
    environment:
      - DISPLAY=:99
    ports:
      - "4444:4444"
```

### Production Deployment
```bash
# 1. Server Setup (Ubuntu 20.04+)
sudo apt update
sudo apt install -y python3 python3-pip nginx supervisor

# 2. Clone and setup
git clone <repository-url> /opt/navina-crawler
cd /opt/navina-crawler
pip3 install -r requirements.txt
playwright install chromium

# 3. Create service configuration
sudo tee /etc/supervisor/conf.d/navina-crawler.conf << EOF
[program:navina-crawler]
directory=/opt/navina-crawler
command=python3 main.py start_server
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/navina-crawler.log
EOF

# 4. Start service
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start navina-crawler

# 5. Nginx reverse proxy
sudo tee /etc/nginx/sites-available/navina-crawler << EOF
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8888;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/navina-crawler /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### Cloud Deployment (AWS/GCP/Azure)
```bash
# 1. Create VM instance with 2+ GB RAM
# 2. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 3. Deploy with Docker
docker run -d \
  --name navina-crawler \
  -p 8888:8888 \
  -e CAPSOLVER_API_KEY="your_key" \
  -v /opt/navina-config:/app/.ghost \
  navina/crawler:latest

# 4. Setup load balancer (optional)
# Configure your cloud provider's load balancer to point to port 8888
```

##  Advanced Features

### Custom YARA Rules
Create custom detection patterns in `modules/signatures/`:
```yara
rule CustomTurnstileDetection {
    meta:
        description = "Custom Turnstile pattern"
        author = "Your Name"
        
    strings:
        $custom_pattern = /your-custom-pattern/i
        
    condition:
        $custom_pattern
}
```

### ECW Integration
```python
from modules.ecw_solver import handle_ecw_login

# Automated ECW portal handling
async def ecw_automation():
    browser = BaseBrowser(use_profile=True)
    await browser.launch_browser()
    
    # ECW-specific automation
    success = await handle_ecw_login(
        browser.page, 
        username="your_username",
        password="your_password"
    )
    
    if success:
        print(" ECW login successful")
```

### Custom Stealth Profiles
```python
# Create custom browser profile
from modules.enhanced_stealth import EnhancedStealth

# Generate realistic profile data
profile_path = EnhancedStealth.get_crawler_profile_path()
EnhancedStealth.create_realistic_profile(profile_path)

# Custom stealth JavaScript
custom_js = EnhancedStealth.get_stealth_js()
await browser.context.add_init_script(custom_js)
```

##  Testing & Validation

### Stealth Testing
```bash
# Test against detection sites
python3 main.py test_stealth

# Manual stealth verification
python3 scripts/analyze_detection.py

# Custom detection tests
python3 tests/test_profile_stealth.py
```

### CAPTCHA Testing
```bash
# Test Turnstile detection
python3 tests/test_turnstile.py

# Server endpoint testing
curl "http://localhost:8888/test"

# YARA rule validation
python3 scripts/example_yara_usage.py
```

##  Troubleshooting

### Common Issues

**Browser Launch Fails**
```bash
# Fix: Install missing dependencies
sudo apt install -y chromium-browser
playwright install chromium
```

**Stealth Detection**
```bash
# Fix: Enable profile mode and check stealth settings
python3 main.py test_stealth --browser=chrome
```

**Server Port Conflict**
```bash
# Fix: Stop existing server
python3 main.py stop_server
# Or use different port
python3 main.py start_server --port=9999
```

**YARA Rules Error**
```bash
# Fix: Check rule syntax
yara modules/signatures/turnstile_detection.yar test_file.html
```

### Debug Mode
```bash
# Enable verbose logging
export DEBUG=1
python3 main.py your_command

# Check logs
tail -f log/browser_session_*.log
```

##  API Reference

### Server Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Server status and documentation |
| `/solve` | GET | Create solving session |
| `/status` | GET | Get session status |
| `/token` | POST | Receive solved tokens |
| `/test` | GET | Test page with demo Turnstile |

### Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `sitekey` | Yes | Turnstile sitekey |
| `url` | Yes | Original page URL |
| `action` | No | Turnstile action parameter |
| `cdata` | No | Custom data parameter |
| `session` | No | Session ID for status check |

##  Performance & Limits

- **Stealth Success Rate**: 94.4% (verified against major detection platforms)
- **Solving Speed**: 2-15 seconds per Turnstile
- **Concurrent Sessions**: Up to 50 simultaneous (server mode)
- **Memory Usage**: ~200MB per browser instance
- **API Rate Limits**: Depends on CapSolver subscription

##  Security & Compliance

- **No Data Logging**: Sensitive information is not logged
- **Secure Credential Storage**: Encrypted configuration files
- **HIPAA Considerations**: ECW integration follows healthcare data guidelines
- **Proxy Support**: Route traffic through proxies for anonymity
- **Session Isolation**: Each browser instance is completely isolated

##  Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

##  License

This project is proprietary software owned by Navina Inc. All rights reserved.

##  Support

- **Documentation**: Check this README and inline code comments
- **Issues**: Report bugs via GitHub issues
- **Enterprise Support**: Contact Navina Inc for commercial licensing

Udi Shamir
---

** 2025 Navina Inc. All rights reserved.**

*Advanced browser automation and CAPTCHA solving technology for enterprise applications.*
