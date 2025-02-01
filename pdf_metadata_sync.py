#!/usr/bin/env python3

import os
from PyPDF2 import PdfReader
from datetime import datetime
from paperlessngx_postprocessor import Config, PaperlessAPI

def extract_pdf_metadata(pdf_path):
    reader = PdfReader(pdf_path)
    metadata = reader.metadata
    
    # Convert PDF metadata to Paperless-NGX format
    paperless_metadata = {}
    
    if metadata.get('/Author'):
        paperless_metadata['correspondent'] = metadata['/Author']
    
    if metadata.get('/Title'):
        paperless_metadata['title'] = metadata['/Title']
    
    if metadata.get('/Keywords'):
        # Split keywords by comma and strip whitespace
        paperless_metadata['tags'] = [
            tag.strip() for tag in metadata['/Keywords'].split(',')
        ]
    
    # Handle various date formats that might be in the PDF
    if metadata.get('/CreationDate'):
        date_str = metadata['/CreationDate']
        # Remove D: prefix and timezone if present
        date_str = date_str.replace('D:', '')[:14]
        try:
            date = datetime.strptime(date_str, '%Y%m%d%H%M%S')
            paperless_metadata['created'] = date.isoformat()
        except ValueError:
            pass
    
    return paperless_metadata

if __name__ == "__main__":
    document_id = os.environ["DOCUMENT_ID"]
    document_source = os.environ["DOCUMENT_SOURCE_PATH"]

    config = Config(Config.general_options())
    
    api = PaperlessAPI(
        config["paperless_api_url"],
        auth_token=config["auth_token"],
        paperless_src_dir=config["paperless_src_dir"]
    )

    # Only process PDFs
    if document_source.lower().endswith('.pdf'):
        # Get PDF metadata
        metadata = extract_pdf_metadata(document_source)
        
        if metadata:
            # Get current document data
            doc = api.get_document_by_id(document_id)
            
            # Update only empty fields with PDF metadata
            updates = {}
            
            if metadata.get('correspondent') and not doc.get('correspondent'):
                # Need to look up or create correspondent ID
                correspondent_id = api.get_or_create_correspondent(
                    metadata['correspondent'])
                updates['correspondent'] = correspondent_id
            
            if metadata.get('title') and not doc.get('title'):
                updates['title'] = metadata['title']
                
            if metadata.get('created') and not doc.get('created'):
                updates['created'] = metadata['created']
                
            if metadata.get('tags'):
                # Get existing tags
                existing_tags = set(t['id'] for t in doc.get('tags', []))
                # Create new tags and get their IDs
                new_tag_ids = [
                    api.get_or_create_tag(tag_name)
                    for tag_name in metadata['tags']
                    if api.get_or_create_tag(tag_name) not in existing_tags
                ]
                if new_tag_ids:
                    updates['tags'] = list(existing_tags) + new_tag_ids

            # Update document if we have changes
            if updates:
                api.update_document(document_id, updates) 