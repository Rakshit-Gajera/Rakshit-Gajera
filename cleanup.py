import re

# Read the file
with open('README.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Filter out lines starting with markdown table syntax containing badges
new_lines = []
for line in lines:
    # Skip lines that are old table rows with badges
    if line.strip().startswith('| [!['):
        continue
    new_lines.append(line)

# Write back
with open('README.md', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Cleanup complete!")
