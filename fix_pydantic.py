#!/usr/bin/env python
"""Fix Pydantic V1 to V2 migration in factor_registry.py"""

import re

filepath = 'src/memory/factor_registry.py'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix import
content = content.replace(
    "from pydantic import BaseModel, Field, validator",
    "from pydantic import BaseModel, Field, field_validator"
)

# Fix @validator decorators - using regex to replace
# Pattern 1: @validator with single field
content = re.sub(
    r"@validator\('([^']+)'\)",
    r"@field_validator('\1', mode='before')\n    @classmethod",
    content
)

# Pattern 2: @validator with multiple fields
content = re.sub(
    r"@validator\('([^']+)',\s*'([^']+)'\)",
    r"@field_validator('\1', '\2', mode='before')\n    @classmethod",
    content
)

# Fix method signatures - add @classmethod and fix parameter
# This is trickier, let's do it line by line
lines = content.split('\n')
fixed_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    fixed_lines.append(line)
    
    # If line is @field_validator, ensure next non-empty line is @classmethod
    if '@field_validator' in line:
        if i + 1 < len(lines) and '@classmethod' not in lines[i + 1]:
            # Check if next line is method definition
            if i + 1 < len(lines) and 'def ' in lines[i + 1]:
                fixed_lines.append('    @classmethod')
    
    i += 1

content = '\n'.join(fixed_lines)

# More careful fix of validator methods - use a simpler approach
# Read again and do more careful replacement
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Replace @validator lines
    if line.strip().startswith('@validator('):
        # Extract field names
        match = re.search(r"@validator\((.*?)\)", line)
        if match:
            fields = match.group(1)
            fixed_lines.append(f"    @field_validator({fields}, mode='before')\n")
            fixed_lines.append("    @classmethod\n")
        i += 1
        continue
    
    # Skip old @classmethod if it comes after our decorator
    if line.strip() == '@classmethod' and i > 0 and '@field_validator' in fixed_lines[-1]:
        i += 1
        continue
    
    # Fix method signature - change (cls, v, values) to (cls, v)
    if 'def validate_' in line and '(cls, v, values)' in line:
        line = line.replace('(cls, v, values)', '(cls, v)')
    
    fixed_lines.append(line)
    i += 1

# Write back
with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print(f"✓ Fixed {filepath}")
print("\nKey changes:")
print("  - Updated import: validator -> field_validator")
print("  - Updated decorators: @validator -> @field_validator(..., mode='before')")
print("  - Added @classmethod where needed")
print("  - Updated method signatures")
