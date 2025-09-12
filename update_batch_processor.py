#!/usr/bin/env python3
"""
Script to update the batch processor with 500 profiles
"""

import re

def update_batch_processor():
    # Read the converted profiles
    with open('profiles_500_converted.txt', 'r', encoding='utf-8') as f:
        profiles_content = f.read()
    
    # Read the current batch processor
    with open('supabase_batch_processor.py', 'r', encoding='utf-8') as f:
        batch_content = f.read()
    
    # Replace the profiles section
    pattern = r'profiles_input = \'\'\'(.*?)\'\'\''
    replacement = f'profiles_input = \'\'\'\n{profiles_content}\'\'\''
    
    new_content = re.sub(pattern, replacement, batch_content, flags=re.DOTALL)
    
    # Write back to file
    with open('supabase_batch_processor.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print('✅ Updated supabase_batch_processor.py with 500 profiles')

if __name__ == "__main__":
    update_batch_processor()

