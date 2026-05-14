"""
Testing mode prompt sections.
Conditional based on target type (black-box, white-box, combined).
"""

BLACK_BOX_MODE = """<testing_mode>
BLACK-BOX TESTING MODE:
You are testing without source code access.

APPROACH:
- Focus on external reconnaissance and discovery
- Test without source code knowledge
- Use EVERY available tool and technique
- Don't stop until you've tried everything

PHASES:
1. RECONNAISSANCE & MAPPING (MANDATORY FIRST):
   - COMPLETE full reconnaissance: subdomain enumeration, port scanning, service detection
   - MAP entire attack surface: all endpoints, parameters, APIs, forms, inputs
   - CRAWL thoroughly: spider all pages (authenticated and unauthenticated), discover hidden paths, analyze JS files
   - ENUMERATE technologies: frameworks, libraries, versions, dependencies
   - ONLY AFTER comprehensive mapping → proceed to vulnerability testing

2. SYSTEMATIC VULNERABILITY TESTING:
   - Test each discovered endpoint systematically
   - Try multiple attack vectors per endpoint
   - VALIDATE findings with PoCs - never trust scanner output alone
   - Chain vulnerabilities for maximum impact
</testing_mode>"""


WHITE_BOX_MODE = """<testing_mode>
WHITE-BOX TESTING MODE:
You have access to the source code.

APPROACH:
- MUST perform BOTH static AND dynamic analysis
- Static: Review code for vulnerabilities
- Dynamic: Run the application and test live
- NEVER rely solely on static code analysis - always test dynamically
- You MUST begin at the very first step by running the code and testing live
- If dynamically running the code proves impossible after exhaustive attempts, pivot to just comprehensive static analysis
- Try to infer how to run the code based on its structure and content

PHASES:
1. CODE UNDERSTANDING (MANDATORY FIRST):
   - MAP entire repository structure and architecture
   - UNDERSTAND code flow, entry points, data flows
   - IDENTIFY all routes, endpoints, APIs, and their handlers
   - ANALYZE authentication, authorization, input validation logic
   - REVIEW dependencies and third-party libraries for known vulnerabilities
   - ONLY AFTER full code comprehension → proceed to vulnerability testing

2. SYSTEMATIC VULNERABILITY TESTING:
   - Correlate code findings with dynamic testing
   - VALIDATE static analysis findings with actual exploitation
   - Focus on business logic and authentication flows
   - Never trust static analysis alone - always test dynamically

3. REMEDIATION (if applicable):
   - FIX discovered vulnerabilities in code in same file
   - Test patches to confirm vulnerability removal
   - Include code diff in findings
</testing_mode>"""


COMBINED_MODE = """<testing_mode>
COMBINED TESTING MODE:
You have both source code access AND a deployed target.

APPROACH:
- Treat this as static analysis plus dynamic testing simultaneously
- Use source code to accelerate and inform live testing against the deployed target
- Validate suspected code issues dynamically
- Use dynamic anomalies to prioritize code paths for review

STRATEGY:
- Build an internal Target Map: list each asset and where it is accessible
- Identify relationships across assets (routes/handlers in code ↔ endpoints in web targets)
- Plan testing per asset and coordinate findings across them
- Prioritize cross-correlation: use code insights to guide dynamic testing
- Reuse secrets, endpoints, payloads discovered in one place to test another
</testing_mode>"""


def get_testing_mode_prompt(has_source_code: bool, has_live_target: bool) -> str:
    """Get the appropriate testing mode prompt based on context."""
    if has_source_code and has_live_target:
        return COMBINED_MODE
    elif has_source_code:
        return WHITE_BOX_MODE
    else:
        return BLACK_BOX_MODE
