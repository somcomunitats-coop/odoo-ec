"""
Energy Self-consumption Controllers

This package contains all HTTP controllers for the energy self-consumption module:
- Report download controllers for coefficient reports
- Website form controllers for public inscription forms
- API endpoints for external integrations

All controllers follow security best practices and include comprehensive
validation and error handling.
"""

from . import controllers
from . import inscriptions_form_controllers
