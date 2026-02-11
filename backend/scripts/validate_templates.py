#!/usr/bin/env python3
"""
Template Validator Script

Validates all proposal and concept note templates to ensure consistency and correctness.

Validation Checks:
1. JSON Syntax - Valid JSON structure
2. Required Fields - Presence of mandatory template fields
3. Section Consistency - All sections have corresponding sequence entries
4. Section Configuration - Valid format_type, proper field definitions
5. Special Requirements - Valid structure
6. Cross-References - Internal consistency checks

Usage:
    python3 backend/scripts/validate_templates.py
    python3 backend/scripts/validate_templates.py --template proposal_template_private.json
    python3 backend/scripts/validate_templates.py --verbose
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
import argparse

# Color codes for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

# Validation result types
class ValidationLevel:
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"

class ValidationResult:
    def __init__(self, level: str, check: str, message: str):
        self.level = level
        self.check = check
        self.message = message
    
    def __str__(self):
        icon = "❌" if self.level == ValidationLevel.ERROR else "⚠️" if self.level == ValidationLevel.WARNING else "ℹ️"
        color = Colors.RED if self.level == ValidationLevel.ERROR else Colors.YELLOW if self.level == ValidationLevel.WARNING else Colors.CYAN
        return f"{icon} {color}{self.level}{Colors.RESET}: [{self.check}] {self.message}"

class TemplateValidator:
    """Validates proposal and concept note templates."""
    
    REQUIRED_ROOT_FIELDS = ["template_type", "donors", "sections"]
    VALID_TEMPLATE_TYPES = ["Proposal", "Concept Note"]
    VALID_FORMAT_TYPES = ["text", "fixed_text", "number", "table"]
    
    def __init__(self, templates_dir: Path, verbose: bool = False):
        self.templates_dir = templates_dir
        self.verbose = verbose
        self.results: List[ValidationResult] = []
    
    def add_result(self, level: str, check: str, message: str):
        """Add a validation result."""
        self.results.append(ValidationResult(level, check, message))
    
    def validate_json_syntax(self, template_path: Path) -> Tuple[bool, Any]:
        """Check if the file is valid JSON."""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return True, data
        except json.JSONDecodeError as e:
            self.add_result(ValidationLevel.ERROR, "JSON Syntax", 
                          f"Invalid JSON: {e.msg} at line {e.lineno}, column {e.colno}")
            return False, None
        except Exception as e:
            self.add_result(ValidationLevel.ERROR, "File Access", f"Cannot read file: {str(e)}")
            return False, None
    
    def validate_required_fields(self, data: Dict) -> bool:
        """Check for required root-level fields."""
        valid = True
        for field in self.REQUIRED_ROOT_FIELDS:
            if field not in data:
                self.add_result(ValidationLevel.ERROR, "Required Fields", 
                              f"Missing required field: '{field}'")
                valid = False
        return valid
    
    def validate_template_type(self, data: Dict) -> bool:
        """Validate template_type field."""
        template_type = data.get("template_type")
        if not template_type:
            return False
        
        if template_type not in self.VALID_TEMPLATE_TYPES:
            self.add_result(ValidationLevel.ERROR, "Template Type",
                          f"Invalid template_type '{template_type}'. Must be one of: {self.VALID_TEMPLATE_TYPES}")
            return False
        
        if self.verbose:
            self.add_result(ValidationLevel.INFO, "Template Type", f"Valid template_type: {template_type}")
        return True
    
    def validate_donors(self, data: Dict) -> bool:
        """Validate donors field."""
        donors = data.get("donors")
        if not donors:
            self.add_result(ValidationLevel.WARNING, "Donors", "No donors specified")
            return True
        
        if not isinstance(donors, list):
            self.add_result(ValidationLevel.ERROR, "Donors", "Donors field must be an array")
            return False
        
        if len(donors) == 0:
            self.add_result(ValidationLevel.WARNING, "Donors", "Donors array is empty")
        elif self.verbose:
            self.add_result(ValidationLevel.INFO, "Donors", f"Found {len(donors)} donor(s): {', '.join(donors[:3])}")
        
        return True
    
    def validate_sections(self, data: Dict) -> bool:
        """Validate sections array."""
        sections = data.get("sections")
        if not sections:
            return False
        
        if not isinstance(sections, list):
            self.add_result(ValidationLevel.ERROR, "Sections", "Sections field must be an array")
            return False
        
        if len(sections) == 0:
            self.add_result(ValidationLevel.ERROR, "Sections", "Sections array is empty")
            return False
        
        valid = True
        section_names = []
        
        for i, section in enumerate(sections):
            # Check section_name
            section_name = section.get("section_name")
            if not section_name:
                self.add_result(ValidationLevel.ERROR, "Sections",
                              f"Section at index {i} missing 'section_name'")
                valid = False
                continue
            
            section_names.append(section_name)
            
            # Check for duplicate section names
            if section_names.count(section_name) > 1:
                self.add_result(ValidationLevel.ERROR, "Sections",
                              f"Duplicate section_name: '{section_name}'")
                valid = False
            
            # Check format_type
            format_type = section.get("format_type", "text")
            if format_type not in self.VALID_FORMAT_TYPES:
                self.add_result(ValidationLevel.ERROR, "Sections",
                              f"Section '{section_name}' has invalid format_type: '{format_type}'")
                valid = False
            
            # Validate table format sections
            if format_type == "table":
                if not self.validate_table_section(section_name, section):
                    valid = False
            
            # Check for instructions
            if "instructions" not in section and format_type not in ["fixed_text", "table"]:
                self.add_result(ValidationLevel.WARNING, "Sections",
                              f"Section '{section_name}' missing 'instructions'")
            
            # Check for word_limit or char_limit
            has_limit = "word_limit" in section or "char_limit" in section
            if not has_limit and format_type == "text":
                self.add_result(ValidationLevel.WARNING, "Sections",
                              f"Section '{section_name}' has no word_limit or char_limit")
        
        if self.verbose:
            self.add_result(ValidationLevel.INFO, "Sections", f"Found {len(sections)} section(s)")
        
        return valid
    
    def validate_table_section(self, section_name: str, section: Dict) -> bool:
        """Validate table format section configuration."""
        valid = True
        
        # Check for columns
        if "columns" not in section:
            self.add_result(ValidationLevel.ERROR, "Table Sections",
                          f"Table section '{section_name}' missing 'columns'")
            valid = False
        else:
            columns = section["columns"]
            if not isinstance(columns, list) or len(columns) == 0:
                self.add_result(ValidationLevel.ERROR, "Table Sections",
                              f"Table section '{section_name}' has invalid 'columns'")
                valid = False
        
        # Check for rows
        if "rows" not in section:
            self.add_result(ValidationLevel.ERROR, "Table Sections",
                          f"Table section '{section_name}' missing 'rows'")
            valid = False
        else:
            rows = section["rows"]
            if not isinstance(rows, list) or len(rows) == 0:
                self.add_result(ValidationLevel.ERROR, "Table Sections",
                              f"Table section '{section_name}' has invalid 'rows'")
                valid = False
        
        return valid
    
    def validate_section_sequence(self, data: Dict) -> bool:
        """Validate section_sequence consistency with sections."""
        section_sequence = data.get("section_sequence", [])
        sections = data.get("sections", [])
        
        if not section_sequence:
            self.add_result(ValidationLevel.WARNING, "Section Sequence",
                          "No section_sequence defined - will use sections array order for generation")
            return True
        
        if not isinstance(section_sequence, list):
            self.add_result(ValidationLevel.ERROR, "Section Sequence",
                          "section_sequence must be an array")
            return False
        
        # Create sets for comparison
        section_names = {s.get("section_name") for s in sections if s.get("section_name")}
        sequence_names = set(section_sequence)
        
        valid = True
        
        # Check for sections in sequence that don't exist in sections array
        missing_in_sections = sequence_names - section_names
        if missing_in_sections:
            self.add_result(ValidationLevel.ERROR, "Section Sequence",
                          f"Sections in sequence but not in sections array ({len(missing_in_sections)}): {sorted(missing_in_sections)[:5]}"
                          + (f" ...and {len(missing_in_sections) - 5} more" if len(missing_in_sections) > 5 else ""))
            valid = False
        
        # Check for sections in array that aren't in sequence
        missing_in_sequence = section_names - sequence_names
        if missing_in_sequence:
            self.add_result(ValidationLevel.ERROR, "Section Sequence",
                          f"Sections in array but not in sequence ({len(missing_in_sequence)}): {sorted(missing_in_sequence)[:5]}"
                          + (f" ...and {len(missing_in_sequence) - 5} more" if len(missing_in_sequence) > 5 else ""))
            valid = False
        
        # Check for duplicates in sequence
        duplicates = [name for name in sequence_names if section_sequence.count(name) > 1]
        if duplicates:
            self.add_result(ValidationLevel.ERROR, "Section Sequence",
                          f"Duplicate entries in section_sequence: {duplicates}")
            valid = False
        
        # Info: Check if sequence differs from sections array order
        if valid:
            sections_array_order = [s["section_name"] for s in sections]
            if section_sequence != sections_array_order:
                if self.verbose:
                    self.add_result(ValidationLevel.INFO, "Section Sequence",
                                  "Generation order differs from output order (optimization enabled)")
            else:
                self.add_result(ValidationLevel.WARNING, "Section Sequence",
                              "Generation order same as output order (no optimization benefit)")
        
        return valid
    
    def validate_special_requirements(self, data: Dict) -> bool:
        """Validate special_requirements field."""
        special_requirements = data.get("special_requirements")
        if not special_requirements:
            if self.verbose:
                self.add_result(ValidationLevel.INFO, "Special Requirements", "No special requirements defined")
            return True
        
        if not isinstance(special_requirements, dict):
            self.add_result(ValidationLevel.ERROR, "Special Requirements",
                          "special_requirements must be an object")
            return False
        
        instructions = special_requirements.get("instructions")
        if instructions and not isinstance(instructions, list):
            self.add_result(ValidationLevel.ERROR, "Special Requirements",
                          "special_requirements.instructions must be an array")
            return False
        
        if self.verbose and instructions:
            self.add_result(ValidationLevel.INFO, "Special Requirements",
                          f"Found {len(instructions)} requirement(s)")
        
        return True
    
    def validate_template(self, template_path: Path) -> Tuple[bool, int, int, int]:
        """
        Validate a single template file.
        
        Returns:
            (is_valid, error_count, warning_count, info_count)
        """
        self.results = []  # Reset results
        
        print(f"\n{Colors.BOLD}{'='*80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}Validating: {template_path.name}{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*80}{Colors.RESET}")
        
        # 1. Validate JSON syntax
        is_valid_json, data = self.validate_json_syntax(template_path)
        if not is_valid_json:
            self._print_results()
            return False, 1, 0, 0
        
        # 2. Validate required fields
        self.validate_required_fields(data)
        
        # 3. Validate template_type
        self.validate_template_type(data)
        
        # 4. Validate donors
        self.validate_donors(data)
        
        # 5. Validate sections
        self.validate_sections(data)
        
        # 6. Validate section_sequence
        self.validate_section_sequence(data)
        
        # 7. Validate special_requirements
        self.validate_special_requirements(data)
        
        # Print results
        self._print_results()
        
        # Count results by level
        error_count = sum(1 for r in self.results if r.level == ValidationLevel.ERROR)
        warning_count = sum(1 for r in self.results if r.level == ValidationLevel.WARNING)
        info_count = sum(1 for r in self.results if r.level == ValidationLevel.INFO)
        
        is_valid = error_count == 0
        
        # Print summary
        status_icon = "✅" if is_valid else "❌"
        status_text = f"{Colors.GREEN}VALID{Colors.RESET}" if is_valid else f"{Colors.RED}INVALID{Colors.RESET}"
        print(f"\n{status_icon} Status: {status_text}")
        print(f"   Errors: {error_count}, Warnings: {warning_count}, Info: {info_count}")
        
        return is_valid, error_count, warning_count, info_count
    
    def _print_results(self):
        """Print validation results grouped by level."""
        if not self.results:
            print(f"{Colors.GREEN}✅ No issues found{Colors.RESET}")
            return
        
        # Group by level
        errors = [r for r in self.results if r.level == ValidationLevel.ERROR]
        warnings = [r for r in self.results if r.level == ValidationLevel.WARNING]
        infos = [r for r in self.results if r.level == ValidationLevel.INFO]
        
        # Print errors first
        if errors:
            print(f"\n{Colors.RED}{Colors.BOLD}ERRORS ({len(errors)}):{Colors.RESET}")
            for result in errors:
                print(f"  {result}")
        
        # Print warnings
        if warnings:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}WARNINGS ({len(warnings)}):{Colors.RESET}")
            for result in warnings:
                print(f"  {result}")
        
        # Print info only in verbose mode
        if infos and self.verbose:
            print(f"\n{Colors.CYAN}{Colors.BOLD}INFO ({len(infos)}):{Colors.RESET}")
            for result in infos:
                print(f"  {result}")
    
    def validate_all_templates(self) -> Tuple[int, int, int, int]:
        """
        Validate all templates in the templates directory.
        
        Returns:
            (total_count, valid_count, total_errors, total_warnings)
        """
        # Find all template files
        template_files = sorted(self.templates_dir.glob("proposal_template_*.json")) + \
                         sorted(self.templates_dir.glob("concept_note_*.json"))
        
        if not template_files:
            print(f"{Colors.RED}No template files found in {self.templates_dir}{Colors.RESET}")
            return 0, 0, 0, 0
        
        total_count = 0
        valid_count = 0
        total_errors = 0
        total_warnings = 0
        
        for template_path in template_files:
            is_valid, errors, warnings, _ = self.validate_template(template_path)
            total_count += 1
            if is_valid:
                valid_count += 1
            total_errors += errors
            total_warnings += warnings
        
        # Print overall summary
        print(f"\n{Colors.BOLD}{'='*80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}OVERALL SUMMARY{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*80}{Colors.RESET}")
        print(f"Total templates:     {total_count}")
        print(f"Valid templates:     {Colors.GREEN}{valid_count}{Colors.RESET}")
        print(f"Invalid templates:   {Colors.RED if (total_count - valid_count) > 0 else Colors.GREEN}{total_count - valid_count}{Colors.RESET}")
        print(f"Total errors:        {Colors.RED if total_errors > 0 else Colors.GREEN}{total_errors}{Colors.RESET}")
        print(f"Total warnings:      {Colors.YELLOW if total_warnings > 0 else Colors.GREEN}{total_warnings}{Colors.RESET}")
        
        if valid_count == total_count:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✅ All templates are valid!{Colors.RESET}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ Some templates have validation errors{Colors.RESET}")
        
        return total_count, valid_count, total_errors, total_warnings

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate proposal and concept note templates")
    parser.add_argument("--template", "-t", help="Validate a specific template file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed information")
    parser.add_argument("--templates-dir", default="backend/templates", help="Templates directory path")
    
    args = parser.parse_args()
    
    # Determine templates directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    templates_dir = project_root / args.templates_dir
    
    if not templates_dir.exists():
        print(f"{Colors.RED}Templates directory not found: {templates_dir}{Colors.RESET}")
        return 1
    
    validator = TemplateValidator(templates_dir, verbose=args.verbose)
    
    if args.template:
        # Validate single template
        template_path = templates_dir / args.template
        if not template_path.exists():
            print(f"{Colors.RED}Template file not found: {template_path}{Colors.RESET}")
            return 1
        
        is_valid, errors, warnings, _ = validator.validate_template(template_path)
        return 0 if is_valid else 1
    else:
        # Validate all templates
        total, valid, errors, warnings = validator.validate_all_templates()
        return 0 if valid == total else 1

if __name__ == "__main__":
    sys.exit(main())
