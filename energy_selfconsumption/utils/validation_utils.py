"""
Validation utilities for energy self-consumption module

This module contains common validation functions used across
the energy self-consumption module to ensure data integrity
and compliance with business rules.
"""

from stdnum.es import cups, referenciacatastral
from stdnum.exceptions import (
    InvalidChecksum,
    InvalidComponent,
    InvalidFormat,
    InvalidLength,
)

from odoo import _
from odoo.exceptions import ValidationError

from ..config import (
    CAU_LENGTH_24,
    CAU_LENGTH_26,
    CAU_SEPARATOR,
    CIL_LENGTH_23,
    CIL_LENGTH_25,
    CUPS_LENGTH_20,
    CUPS_LENGTH_22,
    LAST_DIGITS_COUNT,
)


def validate_cups_code(code, code_type, cups_length):
    """
    Validate CUPS (Universal Supply Point Code) format

    Args:
        code (str): The code to validate
        code_type (str): Type of code ('CAU' or 'CIL') for error messages
        cups_length (int): Expected CUPS length (20 or 22)

    Returns:
        str: The remaining digits after CUPS validation

    Raises:
        ValidationError: If CUPS validation fails
    """
    try:
        cups.validate(code[:cups_length])
    except InvalidLength:
        error_message = _(
            "Invalid {code_type}: The first characters related to CUPS are incorrect. The length is incorrect."
        ).format(code_type=code_type)
        raise ValidationError(error_message)
    except InvalidComponent:
        error_message = _(
            "Invalid {code_type}: The CUPS does not start with 'ES'."
        ).format(code_type=code_type)
        raise ValidationError(error_message)
    except InvalidFormat:
        error_message = _(
            "Invalid {code_type}: The CUPS has an incorrect format."
        ).format(code_type=code_type)
        raise ValidationError(error_message)
    except InvalidChecksum:
        error_message = _(
            "Invalid {code_type}: The checksum of the CUPS is incorrect."
        ).format(code_type=code_type)
        raise ValidationError(error_message)

    return code[cups_length:]


def validate_cau_format(code):
    """
    Validate CAU (Self-consumption Authorization Code) format

    Args:
        code (str): CAU code to validate

    Raises:
        ValidationError: If CAU format is invalid
    """
    if not code:
        return

    # Constants for CAU validation
    code_length = len(code)

    # Determine CUPS length based on total code length
    if code_length == CAU_LENGTH_24:
        cups_length = CUPS_LENGTH_20
    elif code_length == CAU_LENGTH_26:
        cups_length = CUPS_LENGTH_22
    else:
        error_message = _("Invalid CAU: The length is not correct")
        raise ValidationError(error_message)

    # Validate CUPS portion and get remaining digits
    last_digits = validate_cups_code(code, "CAU", cups_length)

    # Check if the character after CUPS is 'A'
    if not last_digits.startswith(CAU_SEPARATOR):
        error_message = _("Invalid CAU: The character after CUPS is not A")
        raise ValidationError(error_message)

    # Check if the last 3 characters are numbers
    if not last_digits[-LAST_DIGITS_COUNT:].isdigit():
        error_message = _("Invalid CAU: Last 3 digits are not numbers")
        raise ValidationError(error_message)


def validate_cil_format(code):
    """
    Validate CIL (Production facility code for liquidation) format

    Args:
        code (str): CIL code to validate

    Raises:
        ValidationError: If CIL format is invalid
    """
    if not code:
        return

    # Constants for CIL validation
    code_length = len(code)

    # Determine CUPS length based on total code length
    if code_length == CIL_LENGTH_23:
        cups_length = CUPS_LENGTH_20
    elif code_length == CIL_LENGTH_25:
        cups_length = CUPS_LENGTH_22
    else:
        error_message = _("Invalid CIL: The length is not correct")
        raise ValidationError(error_message)

    # Validate CUPS portion and get remaining digits
    last_digits = validate_cups_code(code, "CIL", cups_length)

    # Check if the last 3 characters are numbers
    if not last_digits[-LAST_DIGITS_COUNT:].isdigit():
        error_message = _("Invalid CIL: Last 3 digits are not numbers")
        raise ValidationError(error_message)


def validate_cadastral_reference(reference):
    """
    Validate Spanish cadastral reference format

    Args:
        reference (str): Cadastral reference to validate

    Raises:
        ValidationError: If cadastral reference is invalid
    """
    if not reference:
        return

    try:
        referenciacatastral.validate(reference)
    except Exception as e:
        error_message = _("Invalid Cadastral Reference: {error}").format(error=e)
        raise ValidationError(error_message)


def validate_power_value(power, min_value=0, max_value=None):
    """
    Validate power value is within acceptable range

    Args:
        power (float): Power value to validate
        min_value (float): Minimum acceptable value
        max_value (float): Maximum acceptable value (optional)

    Raises:
        ValidationError: If power value is invalid
    """
    if power is None:
        return

    if power < min_value:
        error_message = _("Power value cannot be less than {min_value} kW").format(
            min_value=min_value
        )
        raise ValidationError(error_message)

    if max_value is not None and power > max_value:
        error_message = _("Power value cannot exceed {max_value} kW").format(
            max_value=max_value
        )
        raise ValidationError(error_message)


def validate_required_fields(values, required_fields):
    """
    Validate that all required fields are present and not empty

    Args:
        values (dict): Dictionary of field values
        required_fields (list): List of required field names

    Raises:
        ValidationError: If any required field is missing or empty
    """
    missing_fields = []

    for field in required_fields:
        if field not in values or not values[field]:
            missing_fields.append(field)

    if missing_fields:
        error_message = _("The following required fields are missing: {fields}").format(
            fields=", ".join(missing_fields)
        )
        raise ValidationError(error_message)
