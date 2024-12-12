import os
import re
import sys


def remove_unused_imports(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    # Remove blank lines with whitespace
    lines = [line for line in lines if not re.match(r'^\s+$', line)]

    # Track imports and their usage
    imports = []
    used_imports = set()

    # First pass: collect imports
    for line in lines:
        import_match = re.match(r'^(from\s+\S+\s+)?import\s+(.+)', line)
        if import_match:
            imports.append(line.strip())

    # Second pass: check import usage
    for line in lines:
        for imp in imports:
            # Simple check for import usage
            if re.search(r'\b' + imp.split()[-1] + r'\b', line):
                used_imports.add(imp)

    # Remove unused imports
    new_lines = []
    for line in lines:
        if not any(imp in line for imp in imports - used_imports):
            new_lines.append(line)

    # Write back to file
    with open(file_path, 'w') as f:
        f.writelines(new_lines)

    print(f"Processed {file_path}")


def process_directory(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                remove_unused_imports(file_path)


if __name__ == '__main__':
    directory = sys.argv[1] if len(sys.argv) > 1 else '.'
    process_directory(directory)
