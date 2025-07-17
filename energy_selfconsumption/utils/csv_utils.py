"""
CSV utilities for energy self-consumption module

This module contains common CSV file handling functions used across
multiple wizards to ensure consistent file processing and validation.
"""

import base64
import logging
from csv import DictReader
from io import StringIO

import chardet
import pandas as pd

from odoo import _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

from ..config import (
    CSV_DELIMITER,
    CSV_FILE_EXTENSION,
    CSV_QUOTE_CHAR,
    DEFAULT_ENCODING,
)

# Constants for file processing
SUPPORTED_FILE_EXTENSIONS = [".{}".format(CSV_FILE_EXTENSION)]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


class CSVProcessor:
    """
    CSV file processor with common validation and parsing functionality
    """

    def __init__(
        self,
        file_data,
        encoding=DEFAULT_ENCODING,
        delimiter=CSV_DELIMITER,
        quotechar=CSV_QUOTE_CHAR,
    ):
        """
        Initialize CSV processor

        Args:
            file_data (bytes): Raw file data
            encoding (str): File encoding
            delimiter (str): CSV delimiter
            quotechar (str): CSV quote character
        """
        self.file_data = file_data
        self.encoding = encoding
        self.delimiter = delimiter
        self.quotechar = quotechar
        self._decoded_content = None

    def validate_file_size(self):
        """
        Validate file size is within acceptable limits

        Raises:
            ValidationError: If file is too large
        """
        if len(self.file_data) > MAX_FILE_SIZE:
            raise ValidationError(
                _("File size exceeds maximum allowed size of {max_size} MB").format(
                    max_size=MAX_FILE_SIZE // (1024 * 1024)
                )
            )

    def detect_encoding(self):
        """
        Detect file encoding if not specified or if decoding fails

        Returns:
            str: Detected encoding

        Raises:
            ValidationError: If no valid encoding is found
        """
        try:
            # Try with specified encoding first
            self.file_data.decode(self.encoding)
            return self.encoding
        except UnicodeDecodeError:
            # Try to detect encoding
            detected = chardet.detect(self.file_data)
            detected_encoding = detected.get("encoding")

            if not detected_encoding:
                raise ValidationError(
                    _("No valid encoding was found for the uploaded file")
                )

            try:
                self.file_data.decode(detected_encoding)
                return detected_encoding
            except UnicodeDecodeError:
                raise ValidationError(
                    _(
                        "File encoding could not be determined. Please ensure the file is properly encoded."
                    )
                )

    def decode_file(self):
        """
        Decode file content with proper encoding detection

        Returns:
            str: Decoded file content
        """
        if self._decoded_content is not None:
            return self._decoded_content

        self.validate_file_size()
        encoding = self.detect_encoding()

        try:
            self._decoded_content = self.file_data.decode(encoding)
            return self._decoded_content
        except Exception as e:
            raise ValidationError(
                _("Error decoding file: {error}").format(error=str(e))
            )

    def parse_as_dict_reader(self):
        """
        Parse CSV file using DictReader

        Returns:
            list: List of dictionaries representing CSV rows

        Raises:
            ValidationError: If parsing fails
        """
        try:
            decoded_content = self.decode_file()
            csv_reader = DictReader(
                StringIO(decoded_content),
                delimiter=self.delimiter,
                quotechar=self.quotechar,
            )
            return list(csv_reader)
        except Exception as e:
            raise ValidationError(
                _("Error parsing CSV file: {error}").format(error=str(e))
            )

    def parse_as_dataframe(self):
        """
        Parse CSV file using pandas DataFrame

        Returns:
            pandas.DataFrame: DataFrame containing CSV data

        Raises:
            ValidationError: If parsing fails
        """
        try:
            decoded_content = self.decode_file()
            df = pd.read_csv(
                StringIO(decoded_content),
                delimiter=self.delimiter,
                quotechar=self.quotechar,
            )
            return df
        except Exception as e:
            raise ValidationError(
                _("Error parsing CSV file with pandas: {error}").format(error=str(e))
            )

    def validate_column_count(self, expected_columns):
        """
        Validate that CSV has expected number of columns

        Args:
            expected_columns (int): Expected number of columns

        Raises:
            ValidationError: If column count doesn't match
        """
        data = self.parse_as_dict_reader()
        if not data:
            raise ValidationError(_("CSV file is empty"))

        actual_columns = len(data[0].keys())
        if actual_columns != expected_columns:
            raise ValidationError(
                _(
                    "CSV file should contain {expected} columns but has {actual} columns"
                ).format(expected=expected_columns, actual=actual_columns)
            )

    def validate_required_columns(self, required_columns):
        """
        Validate that CSV contains all required columns

        Args:
            required_columns (list): List of required column names

        Raises:
            ValidationError: If required columns are missing
        """
        data = self.parse_as_dict_reader()
        if not data:
            raise ValidationError(_("CSV file is empty"))

        actual_columns = set(data[0].keys())
        missing_columns = set(required_columns) - actual_columns

        if missing_columns:
            raise ValidationError(
                _("CSV file is missing required columns: {columns}").format(
                    columns=", ".join(missing_columns)
                )
            )


def validate_csv_file_extension(filename):
    """
    Validate that file has a supported CSV extension

    Args:
        filename (str): Name of the uploaded file

    Raises:
        ValidationError: If file extension is not supported
    """
    if not filename:
        return

    file_extension = "." + filename.split(".")[-1].lower()

    if file_extension not in SUPPORTED_FILE_EXTENSIONS:
        raise ValidationError(
            _(
                "Only CSV format files are accepted. Supported extensions: {extensions}"
            ).format(extensions=", ".join(SUPPORTED_FILE_EXTENSIONS))
        )


def process_csv_file(
    file_binary,
    filename,
    encoding=DEFAULT_ENCODING,
    delimiter=CSV_DELIMITER,
    quotechar=CSV_QUOTE_CHAR,
):
    """
    High-level function to process a CSV file with validation

    Args:
        file_binary (str): Base64 encoded file content
        filename (str): Original filename
        encoding (str): File encoding
        delimiter (str): CSV delimiter
        quotechar (str): CSV quote character

    Returns:
        CSVProcessor: Configured CSV processor instance

    Raises:
        ValidationError: If file validation fails
    """
    # Validate file extension
    validate_csv_file_extension(filename)

    # Decode base64 content
    try:
        file_data = base64.b64decode(file_binary)
    except Exception as e:
        raise ValidationError(
            _("Error decoding file content: {error}").format(error=str(e))
        )

    # Create and return processor
    processor = CSVProcessor(file_data, encoding, delimiter, quotechar)

    # Validate file can be processed
    processor.decode_file()

    return processor


def create_download_action(attachment_ref, description="Download Template"):
    """
    Create a download action for a file attachment

    Args:
        attachment_ref (str): XML reference to the attachment
        description (str): Description for the download action

    Returns:
        dict: Action dictionary for file download
    """
    return {
        "name": _(description),
        "type": "ir.actions.act_url",
        "url": f"/web/content/{attachment_ref}/?download=true",
        "target": "new",
    }


def format_import_errors(errors):
    """
    Format import errors for display in messages

    Args:
        errors (list): List of tuples (line_number, error_message)

    Returns:
        str: Formatted HTML error list
    """
    if not errors:
        return ""

    error_items = []
    for line_num, error_msg in errors:
        error_items.append(
            _("<li>Line {line}: {error}</li>").format(line=line_num, error=error_msg)
        )

    return _("Import errors found: <ul>{errors}</ul>").format(
        errors="\n".join(error_items)
    )
