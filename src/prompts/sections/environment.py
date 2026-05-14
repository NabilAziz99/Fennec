"""
Environment prompt section.
Describes available tools and environment setup.
"""

ENVIRONMENT = """<environment>
Docker container with Kali Linux and comprehensive security tools:

RECONNAISSANCE & SCANNING:
- nmap, ncat - Network mapping and port scanning
- subfinder - Subdomain enumeration
- naabu - Fast port scanner
- httpx - HTTP probing and validation
- gospider - Web spider/crawler
- whatweb - Web fingerprinting
- wafw00f - WAF detection

VULNERABILITY ASSESSMENT:
- nuclei - Template-based vulnerability scanner
- sqlmap - SQL injection detection/exploitation
- nikto - Web server scanner
- commix - Command injection testing
- `wpscan --url <url> --enumerate p --plugins-detection aggressive --no-banner --force` — WordPress scanning

WEB FUZZING & DISCOVERY:
- ffuf - Fast web fuzzer
- gobuster - Directory/file brute-forcing
- dirsearch - Directory/file discovery
- katana - Advanced web crawler
- arjun - HTTP parameter discovery
- wfuzz - Web fuzzer

JAVASCRIPT ANALYSIS:
- retire - Vulnerable JS library detection
- js-beautify - JS beautifier/deobfuscator
 
SPECIALIZED TOOLS:
- jwt_tool - JWT token manipulation
- interactsh-client - OOB interaction testing
- hydra - Login brute-forcing
- john, hashcat - Password cracking
- metasploit-framework - Exploitation framework

WEB SEARCH (LangChain tool):
- web_search - Search the web for CVEs, exploits, tool usage, and security research

WORDLISTS:
- seclists - Comprehensive wordlist collection (/usr/share/seclists/)
- wfuzz wordlists (/usr/share/wfuzz/wordlist/)

PROGRAMMING:
- Python 3, Go, Node.js/npm
- Full development environment
- You can install any additional tools/packages needed using package managers (apt, pip, npm, go install, etc.)

Directories:
- /work - Primary working directory
- /usr/share/seclists - SecLists wordlists
- Store downloaded tools and wordlists as needed

Default user: root (sudo available)
</environment>"""
