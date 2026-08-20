import os
import glob

frontend_dir = r"c:\Users\DEMİRCİ\OneDrive\Masaüstü\entegrasyon\frontend\src"

files = glob.glob(os.path.join(frontend_dir, "**", "*.tsx"), recursive=True)

for file in files:
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()
    
    if "'http://localhost:8000" in content:
        # We need to replace fetch('http://localhost:8000/api/... with fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/...
        # Also need to replace fetch(`http://localhost:8000/api/...
        
        # Let's do string replacement
        content = content.replace(
            "'http://localhost:8000",
            "`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}"
        )
        content = content.replace(
            "`http://localhost:8000",
            "`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}"
        )
        # Note: the closing single quote for the fetch string needs to be turned into a backtick.
        # But wait! If we replace 'http://localhost:8000/api/v1' with `${process.env...}/api/v1', the string ends with a single quote.
        # We must replace all 'http://localhost:8000/api/... ' with backticks.
        # Let's fix that. We can use regex.
        
        with open(file, "w", encoding="utf-8") as f:
            f.write(content)

import re
for file in files:
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Fix the trailing single quotes on lines that now use backticks for template literals
    # We look for lines containing `${process.env.NEXT_PUBLIC_API_URL` and ending with `'`
    new_lines = []
    for line in content.split("\n"):
        if "process.env.NEXT_PUBLIC_API_URL" in line and "'" in line:
            # find the end of the URL string which is likely ', { or ')
            line = re.sub(r"/([^']+)'", r"/\1`", line)
        new_lines.append(line)
        
    with open(file, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))
        
print("Replaced URLs")
