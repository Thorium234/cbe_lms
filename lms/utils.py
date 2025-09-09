# lms/utils.py
"""
Utility functions for the LMS application
"""
import os
import tempfile
from django.core.files.base import ContentFile
from docx2pdf import convert as docx2pdf_convert

def convert_doc_to_pdf(input_path, output_path=None):
    """
    Convert DOC/DOCX file to PDF using docx2pdf library
    
    Args:
        input_path (str): Path to the input DOC/DOCX file
        output_path (str, optional): Path for the output PDF file
    
    Returns:
        str: Path to the converted PDF file
    
    Raises:
        Exception: If conversion fails
    """
    if output_path is None:
        output_path = input_path.replace('.docx', '.pdf').replace('.doc', '.pdf')
    
    try:
        docx2pdf_convert(input_path, output_path)
        return output_path
    except Exception as e:
        raise Exception(f"Failed to convert document to PDF: {str(e)}")

def handle_document_upload(uploaded_file):
    """
    Handle document upload and conversion to PDF
    
    Args:
        uploaded_file: Uploaded file object
    
    Returns:
        tuple: (processed_file, final_resource_type)
            - processed_file: The file (converted to PDF if needed)
            - final_resource_type: The resource type (PDF if converted)
    """
    from .models import ResourceType
    
    # Get the file extension
    file_name = uploaded_file.name.lower()
    
    # Check if it's a document that needs conversion
    if file_name.endswith(('.doc', '.docx')):
        # Create temporary files
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx' if file_name.endswith('.docx') else '.doc') as temp_input:
            # Save uploaded file to temporary location
            for chunk in uploaded_file.chunks():
                temp_input.write(chunk)
            temp_input_path = temp_input.name
        
        # Create output path
        temp_output_path = temp_input_path.replace('.docx', '.pdf').replace('.doc', '.pdf')
        
        try:
            # Convert to PDF
            convert_doc_to_pdf(temp_input_path, temp_output_path)
            
            # Read the converted PDF
            with open(temp_output_path, 'rb') as pdf_file:
                pdf_content = pdf_file.read()
            
            # Create a new file object
            from django.core.files.base import ContentFile
            from django.core.files.uploadedfile import SimpleUploadedFile
            
            pdf_file = SimpleUploadedFile(
                os.path.basename(uploaded_file.name).replace('.docx', '.pdf').replace('.doc', '.pdf'),
                pdf_content,
                content_type='application/pdf'
            )
            
            # Clean up temporary files
            os.unlink(temp_input_path)
            os.unlink(temp_output_path)
            
            # Return the converted PDF and PDF resource type
            pdf_resource_type = ResourceType.objects.get(name='PDF')
            return pdf_file, pdf_resource_type
            
        except Exception as e:
            # Clean up temporary files on error
            if os.path.exists(temp_input_path):
                os.unlink(temp_input_path)
            if os.path.exists(temp_output_path):
                os.unlink(temp_output_path)
            raise e
    else:
        # For non-document files, return as-is
        pdf_resource_type = ResourceType.objects.get(name='PDF') if file_name.endswith('.pdf') else ResourceType.objects.get(name='Document')
        return uploaded_file, pdf_resource_type

# Create the directory if it doesn't exist
def create_utils_module():
    """
    This function is just for documentation - create the utils.py file manually
    """
    pass