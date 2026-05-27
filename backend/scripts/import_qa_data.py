#!/usr/bin/env python3
"""
Import Q&A Data Script

This script imports initial Q&A content from YAML file into the database.
Usage:
  python -m backend.scripts.import_qa_data
  OR
  cd backend && python scripts/import_qa_data.py
"""

import yaml
import sys
import os
import argparse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# Add the project root to the Python path (same approach as other scripts)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# Import required modules
from backend.models.wizard_models import QACategory, QAItem
from backend.core.db import get_engine


def import_qa_data(yaml_file):
    """
    Import Q&A data from YAML file into the database.
    
    Args:
        yaml_file (str): Path to the YAML file containing Q&A data
        
    Returns:
        tuple: (success, message, categories_count, qa_items_count)
    """
    engine = get_engine()
    with engine.connect() as connection:
        db = Session(connection)
        try:
            # Read YAML file
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
        
        if not data or 'categories' not in data:
            return False, "Invalid YAML format: 'categories' section missing", 0, 0
        
        # Import categories first
        categories_map = {}
        categories_created = 0
        
        for category_data in data['categories']:
            # Check if category already exists
            existing_category = db.query(QACategory).filter_by(name=category_data['name']).first()
            
            if existing_category:
                categories_map[category_data['name']] = existing_category.id
                continue
            
            # Create new category
            category = QACategory(
                name=category_data['name'],
                description=category_data.get('description', '')
            )
            db.add(category)
            db.flush()  # Get the ID immediately
            categories_map[category_data['name']] = category.id
            categories_created += 1
        
        # Import Q&A items
        qa_items_created = 0
        qa_items_skipped = 0
        
        for category_data in data['categories']:
            category_id = categories_map[category_data['name']]
            
            for question_data in category_data['questions']:
                # Check if Q&A item already exists
                existing_item = db.query(QAItem).filter_by(question=question_data['question']).first()
                
                if existing_item:
                    qa_items_skipped += 1
                    continue
                
                # Create new Q&A item
                qa_item = QAItem(
                    question=question_data['question'],
                    answer=question_data['answer'],
                    category_id=category_id
                )
                db.add(qa_item)
                qa_items_created += 1
        
        db.commit()
        
        success_message = (
            f"Successfully imported {categories_created} categories and {qa_items_created} Q&A items"
        )
        if qa_items_skipped > 0:
            success_message += f" (skipped {qa_items_skipped} duplicate questions)"
        
        return True, success_message, categories_created, qa_items_created
        
    except yaml.YAMLError as e:
        db.rollback()
        return False, f"YAML parsing error: {str(e)}", 0, 0
    
    except SQLAlchemyError as e:
        db.rollback()
        return False, f"Database error: {str(e)}", 0, 0
        
    except Exception as e:
        db.rollback()
        return False, f"Unexpected error: {str(e)}", 0, 0
        
	finally:
	    db.close()


def main():
    """Main function to run the import script."""
    parser = argparse.ArgumentParser(description='Import Q&A data into the database')
    parser.add_argument('--file', '-f', default='backend/data/initial_qa_content.yaml',
                       help='Path to the YAML file containing Q&A data')
    
    args = parser.parse_args()
    yaml_file = args.file
    
    print(f"Starting Q&A data import from {yaml_file}...")
    
    success, message, categories_count, qa_items_count = import_qa_data(yaml_file)
    
    if success:
        print(f"✅ {message}")
        print(f"   Categories: {categories_count}")
        print(f"   Q&A Items: {qa_items_count}")
    else:
        print(f"❌ Import failed: {message}")
        sys.exit(1)


if __name__ == "__main__":
    main()