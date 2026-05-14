"""Test configuration - prevent pytest from collecting project source modules."""
collect_ignore_glob = ["../src/*", "../cli/*", "../run.py", "../agent.py", "../__init__.py"]
