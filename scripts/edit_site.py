#!/usr/bin/env python3
"""
Local site content editor for Alexander Salganik's website.
Edit profile content without touching the HTML code.
"""

import re
import sys
from pathlib import Path

# Get the root directory (parent of scripts folder)
ROOT_DIR = Path(__file__).parent.parent
INDEX_FILE = ROOT_DIR / "index.html"
CV_FILE = ROOT_DIR / "cv" / "index.html"

def read_file(file_path):
    """Read HTML file content."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(file_path, content):
    """Write content to HTML file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def extract_text(html, pattern):
    """Extract text between HTML tags using regex pattern."""
    match = re.search(pattern, html, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def replace_text(html, pattern, new_text):
    """Replace text in HTML while keeping tags intact."""
    def replacer(match):
        before = match.group(1)  # opening tag
        after = match.group(3)   # closing tag
        return f"{before}{new_text}{after}"
    
    new_html = re.sub(pattern, replacer, html, count=1, flags=re.DOTALL)
    return new_html

def edit_profile_title():
    """Edit profile title (h2#summary-title)."""
    html = read_file(INDEX_FILE)
    
    pattern = r'(<h2 class="section-title" id="summary-title">)(.*?)(<\/h2>)'
    current = extract_text(html, pattern)
    
    print("\n📝 Profile Title (Main headline)")
    print(f"Current: {current}")
    print("Enter new text (press Enter twice to finish):")
    
    lines = []
    while True:
        line = input()
        if line == "":
            if lines:
                break
        else:
            lines.append(line)
    
    new_text = "\n".join(lines).strip()
    
    if new_text:
        new_html = replace_text(html, pattern, new_text)
        write_file(INDEX_FILE, new_html)
        print("✓ Profile title updated!\n")
    else:
        print("No changes made.\n")

def edit_bio():
    """Edit bio paragraph."""
    html = read_file(INDEX_FILE)
    
    pattern = r'(<p>)(PhD researcher in high-energy astrophysics.*?<\/p>)'
    current = extract_text(html, pattern)
    
    print("\n📝 Bio (Short description)")
    print(f"Current: {current}")
    print("Enter new text (press Enter twice to finish):")
    
    lines = []
    while True:
        line = input()
        if line == "":
            if lines:
                break
        else:
            lines.append(line)
    
    new_text = "\n".join(lines).strip()
    
    if new_text:
        new_html = replace_text(html, pattern, new_text)
        write_file(INDEX_FILE, new_html)
        print("✓ Bio updated!\n")
    else:
        print("No changes made.\n")

def edit_research_overview():
    """Edit research overview paragraph."""
    html = read_file(INDEX_FILE)
    
    pattern = r'(<h2 id="overview-title">Research Overview<\/h2>\s*<p>)(.*?)(<\/p>)'
    current = extract_text(html, pattern)
    
    print("\n📝 Research Overview")
    print(f"Current (first 100 chars): {current[:100]}...")
    print("Enter new text (press Enter twice to finish):")
    
    lines = []
    while True:
        line = input()
        if line == "":
            if lines:
                break
        else:
            lines.append(line)
    
    new_text = "\n".join(lines).strip()
    
    if new_text:
        new_html = replace_text(html, pattern, new_text)
        write_file(INDEX_FILE, new_html)
        print("✓ Research overview updated!\n")
    else:
        print("No changes made.\n")

def edit_topics():
    """Edit research topics (chips)."""
    html = read_file(INDEX_FILE)
    
    pattern = r'(<div class="topic-row" aria-label="Research topics">)(.*?)(<\/div>)'
    current_html = extract_text(html, pattern)
    
    # Extract individual chips
    chip_pattern = r'<span class="chip">([^<]+)<\/span>'
    chips = re.findall(chip_pattern, current_html)
    
    print("\n📝 Research Topics (Chips)")
    print(f"Current topics: {', '.join(chips)}")
    print("Enter topics separated by comma:")
    
    user_input = input().strip()
    new_topics = [t.strip() for t in user_input.split(",") if t.strip()]
    
    if new_topics:
        chips_html = "\n      ".join([f'<span class="chip">{topic}</span>' for topic in new_topics])
        new_content = f"\n      {chips_html}\n    "
        
        new_html = replace_text(html, pattern, new_content)
        write_file(INDEX_FILE, new_html)
        print(f"✓ Topics updated: {', '.join(new_topics)}\n")
    else:
        print("No changes made.\n")

def edit_grant_info():
    """Edit grants section in CV."""
    html = read_file(CV_FILE)
    
    # Find grants section and show it
    pattern = r'(<h3>Grants<\/h3>)(.*?)(<h3>|<\/section>)'
    match = re.search(pattern, html, re.DOTALL)
    
    if match:
        current = match.group(2).strip()
        print("\n💰 Grants Section (CV)")
        print(f"Current content:\n{current}")
        print("\nEnter new grants content (press Enter twice to finish):")
        
        lines = []
        while True:
            line = input()
            if line == "":
                if lines:
                    break
            else:
                lines.append(line)
        
        new_text = "\n".join(lines).strip()
        
        if new_text:
            new_html = re.sub(
                pattern,
                r'\1' + new_text + r'\3',
                html,
                count=1,
                flags=re.DOTALL
            )
            write_file(CV_FILE, new_html)
            print("✓ Grants section updated!\n")
        else:
            print("No changes made.\n")

def show_menu():
    """Show main menu."""
    print("\n" + "="*50)
    print("🌐 Alexander Salganik - Site Content Editor")
    print("="*50)
    print("\nWhat would you like to edit?\n")
    print("1. Profile Title (main headline)")
    print("2. Bio (short description)")
    print("3. Research Overview (detailed text)")
    print("4. Research Topics (chip tags)")
    print("5. Grants Information (CV page)")
    print("0. Exit")
    print("\n" + "-"*50)

def main():
    """Main editor loop."""
    while True:
        show_menu()
        choice = input("Select option (0-5): ").strip()
        
        if choice == "0":
            print("\n👋 Goodbye!\n")
            break
        elif choice == "1":
            edit_profile_title()
        elif choice == "2":
            edit_bio()
        elif choice == "3":
            edit_research_overview()
        elif choice == "4":
            edit_topics()
        elif choice == "5":
            edit_grant_info()
        else:
            print("Invalid option. Please try again.\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!\n")
        sys.exit(0)
