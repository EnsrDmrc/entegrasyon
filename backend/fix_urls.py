import os
import glob

frontend_dir = r"c:\Users\DEMİRCİ\OneDrive\Masaüstü\entegrasyon\frontend\src"
files = glob.glob(os.path.join(frontend_dir, "**", "*.tsx"), recursive=True)

for file in files:
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # We want to replace 'http://localhost:8000`} with 'http://localhost:8000'}
    if "'http://localhost:8000`}" in content:
        content = content.replace("'http://localhost:8000`}", "'http://localhost:8000'}")
        with open(file, "w", encoding="utf-8") as f:
            f.write(content)
            
print("Fixed syntax errors")
