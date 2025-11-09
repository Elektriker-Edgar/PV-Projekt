"""
File upload validators for the quotes app.

This module provides validators for uploaded files including:
- File size validation
- Image file validation (JPG, PNG)
- PDF file validation

All validators include MIME type checks and content verification
to prevent malicious file uploads.
"""

import io
from PIL import Image
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile


# Maximum allowed file size (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes

# Maximum image dimensions
MAX_IMAGE_WIDTH = 10000
MAX_IMAGE_HEIGHT = 10000

# Allowed MIME types
ALLOWED_IMAGE_MIME_TYPES = ['image/jpeg', 'image/png']
ALLOWED_PDF_MIME_TYPES = ['application/pdf']

# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png']
ALLOWED_PDF_EXTENSIONS = ['.pdf']


def validate_file_size(file: UploadedFile) -> None:
    """
    Validate that the uploaded file does not exceed the maximum file size.

    Args:
        file: The uploaded file to validate

    Raises:
        ValidationError: If the file size exceeds MAX_FILE_SIZE (5MB)
    """
    if file.size > MAX_FILE_SIZE:
        max_size_mb = MAX_FILE_SIZE / (1024 * 1024)
        actual_size_mb = file.size / (1024 * 1024)
        raise ValidationError(
            f'Die Datei ist zu groß ({actual_size_mb:.2f}MB). '
            f'Maximal erlaubt sind {max_size_mb:.0f}MB.'
        )


def validate_image_file(file: UploadedFile) -> None:
    """
    Validate that the uploaded file is a valid image (JPG or PNG).

    This validator performs multiple checks:
    1. File size validation (max 5MB)
    2. File extension check
    3. MIME type verification
    4. PIL image verification (opens and validates the actual image data)
    5. Image dimensions check (max 10000x10000 pixels)

    Args:
        file: The uploaded file to validate

    Raises:
        ValidationError: If the file is not a valid image or exceeds constraints
    """
    # Check file size first
    validate_file_size(file)

    # Get file extension
    file_name = file.name.lower()
    file_ext = None
    for ext in ALLOWED_IMAGE_EXTENSIONS:
        if file_name.endswith(ext):
            file_ext = ext
            break

    if not file_ext:
        raise ValidationError(
            f'Ungültiges Dateiformat. Erlaubte Formate: '
            f'{", ".join(ALLOWED_IMAGE_EXTENSIONS)}'
        )

    # Check MIME type
    content_type = file.content_type
    if content_type not in ALLOWED_IMAGE_MIME_TYPES:
        raise ValidationError(
            f'Ungültiger MIME-Type "{content_type}". '
            f'Erlaubte Typen: {", ".join(ALLOWED_IMAGE_MIME_TYPES)}'
        )

    # Verify the file is actually a valid image using PIL
    try:
        # Read file content
        file.seek(0)  # Reset file pointer to beginning
        image = Image.open(file)

        # Verify the image by loading it
        image.verify()

        # Re-open the image to get dimensions (verify() closes the file)
        file.seek(0)
        image = Image.open(file)

        # Check image dimensions
        width, height = image.size
        if width > MAX_IMAGE_WIDTH or height > MAX_IMAGE_HEIGHT:
            raise ValidationError(
                f'Bildabmessungen zu groß ({width}x{height}px). '
                f'Maximum: {MAX_IMAGE_WIDTH}x{MAX_IMAGE_HEIGHT}px.'
            )

        # Verify image format matches expected types
        if image.format not in ['JPEG', 'PNG']:
            raise ValidationError(
                f'Ungültiges Bildformat "{image.format}". '
                f'Erlaubte Formate: JPEG, PNG'
            )

        # Reset file pointer for further processing
        file.seek(0)

    except ValidationError:
        # Re-raise validation errors
        raise
    except Exception as e:
        # Catch any other errors (corrupted images, etc.)
        raise ValidationError(
            f'Die Datei ist kein gültiges Bild oder ist beschädigt: {str(e)}'
        )


def validate_pdf_file(file: UploadedFile) -> None:
    """
    Validate that the uploaded file is a valid PDF.

    This validator performs multiple checks:
    1. File size validation (max 5MB)
    2. File extension check
    3. MIME type verification
    4. PDF header verification (checks for PDF magic bytes)

    Args:
        file: The uploaded file to validate

    Raises:
        ValidationError: If the file is not a valid PDF or exceeds constraints
    """
    # Check file size first
    validate_file_size(file)

    # Get file extension
    file_name = file.name.lower()
    file_ext = None
    for ext in ALLOWED_PDF_EXTENSIONS:
        if file_name.endswith(ext):
            file_ext = ext
            break

    if not file_ext:
        raise ValidationError(
            f'Ungültiges Dateiformat. Erlaubte Formate: '
            f'{", ".join(ALLOWED_PDF_EXTENSIONS)}'
        )

    # Check MIME type
    content_type = file.content_type
    if content_type not in ALLOWED_PDF_MIME_TYPES:
        raise ValidationError(
            f'Ungültiger MIME-Type "{content_type}". '
            f'Erlaubte Typen: {", ".join(ALLOWED_PDF_MIME_TYPES)}'
        )

    # Verify PDF header (PDF magic bytes)
    try:
        file.seek(0)  # Reset file pointer to beginning
        header = file.read(8)

        # PDF files start with "%PDF-" (bytes: 25 50 44 46 2D)
        if not header.startswith(b'%PDF-'):
            raise ValidationError(
                'Die Datei ist kein gültiges PDF-Dokument (ungültiger Header).'
            )

        # Check PDF version (should be between 1.0 and 2.0)
        # Format: %PDF-1.x or %PDF-2.x
        if len(header) >= 8:
            version_char = chr(header[5]) if header[5] < 128 else '?'
            if version_char not in ['1', '2']:
                raise ValidationError(
                    f'Ungültige PDF-Version. Unterstützte Versionen: 1.x, 2.x'
                )

        # Reset file pointer for further processing
        file.seek(0)

    except ValidationError:
        # Re-raise validation errors
        raise
    except Exception as e:
        # Catch any other errors
        raise ValidationError(
            f'Fehler beim Validieren der PDF-Datei: {str(e)}'
        )


# Optional: Combined validator for multiple file types
def validate_upload_file(file: UploadedFile, file_type: str = 'image') -> None:
    """
    Combined validator that routes to specific validators based on file type.

    Args:
        file: The uploaded file to validate
        file_type: Type of file ('image' or 'pdf')

    Raises:
        ValidationError: If the file is not valid or file_type is unknown
    """
    if file_type == 'image':
        validate_image_file(file)
    elif file_type == 'pdf':
        validate_pdf_file(file)
    else:
        raise ValidationError(f'Unbekannter Dateityp: {file_type}')
