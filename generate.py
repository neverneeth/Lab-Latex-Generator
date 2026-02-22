import json
import re
from pathlib import Path

# Set up base paths relative to the script location
GEN_DIR = Path(__file__).parent
BASE_DIR = GEN_DIR.parent

def format_algorithm(text):
    """Converts numbered markdown lists into LaTeX item formats."""
    lines = text.split('\n')
    formatted = []
    for line in lines:
        line = line.strip()
        if not line: continue
        # Convert "1. Step" to "\item Step"
        if re.match(r'^\d+\.', line):
            formatted.append(re.sub(r'^\d+\.', r'\\item', line))
        else:
            formatted.append(f"\\item {line}")
    return "\n".join(formatted)

def parse_readme(readme_path, fallback_title, language):
    """Extracts AIM and ALGORITHM from the markdown file."""
    aim = f"To write a {language} program to implement {fallback_title}."
    algorithm = "\\item Algorithm not provided."
    
    if readme_path.exists():
        content = readme_path.read_text(encoding='utf-8')
        
        # Extract AIM
        aim_match = re.search(r'# AIM\n(.*?)(?=# ALGORITHM|\Z)', content, re.DOTALL | re.IGNORECASE)
        if aim_match:
            aim = aim_match.group(1).strip()
            
        # Extract ALGORITHM
        algo_match = re.search(r'# ALGORITHM\n(.*)', content, re.DOTALL | re.IGNORECASE)
        if algo_match:
            algorithm = format_algorithm(algo_match.group(1).strip())
        else:
            algorithm = format_algorithm(content.strip())
            
    return aim, algorithm

def main():
    # 1. Load Configuration
    config_path = GEN_DIR / "config.json"
    if not config_path.exists():
        print(f"Error: Could not find {config_path}")
        return
        
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 2. Extract dynamic config variables
    # Defaults are provided as a fallback
    exp_dir_name = config.get("expts_dir", "experiments")
    out_dir_name = config.get("output_dir", "output")
    prefix_regex = config.get("regex", {}).get("expit_dir_enum_prefix", r"^\d+_")
    
    EXP_DIR = BASE_DIR / exp_dir_name
    OUT_DIR = BASE_DIR / out_dir_name

    # 3. Load Templates
    base_template_path = GEN_DIR / "templates" / "base_template.tex"
    section_template_path = GEN_DIR / "templates" / "section_template.tex"
    
    if not base_template_path.exists() or not section_template_path.exists():
        print("Error: Template files missing in generator/templates/")
        return
        
    base_template = base_template_path.read_text(encoding='utf-8')
    section_template = section_template_path.read_text(encoding='utf-8')

    # Ensure output directory exists
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if not EXP_DIR.exists():
        print(f"Error: The target directory '{EXP_DIR}' was not found.")
        return

    # 4. Process Experiment Folders
    exp_folders = [d for d in EXP_DIR.iterdir() if d.is_dir()]
    
    # Smart Sorting: Extracts the actual number from "Q10_" so Q10 comes after Q9
    def get_sort_key(folder):
        match = re.match(prefix_regex, folder.name)
        if match:
            # Find the digits within the matched prefix
            num_match = re.search(r'\d+', match.group())
            if num_match:
                return int(num_match.group())
        return 9999  # Push unrecognized folders to the bottom
        
    exp_folders.sort(key=get_sort_key)

    all_sections = ""

    for folder in exp_folders:
        # Check if the folder matches our configured prefix pattern
        prefix_match = re.match(prefix_regex, folder.name)
        if not prefix_match:
            continue # Skip folders that don't match the required structure
            
        print(f"Processing {folder.name}...")
        
        # Extract title by chopping off the matched prefix
        title_raw = folder.name[prefix_match.end():]
        title = title_raw.replace('_', ' ')
        
        # Parse README
        readme_path = folder / "README.md"
        aim, algorithm = parse_readme(readme_path, title, config['code_language'])
        
        # Find Code File
        code_files = list(folder.glob(f"*{config['code_extension']}"))
        code_content = "/* Code file not found */"
        if code_files:
            code_content = code_files[0].read_text(encoding='utf-8')
        
        # Find Image File (assumes screenshots are inside the Q_ folder now)
        img_files = list(folder.glob("*.png")) + list(folder.glob("*.jpg"))
        output_latex = "No output screenshot found."
        if img_files:
            img_path = img_files[0].resolve().as_posix()
            output_latex = f"\\includegraphics[width=\\textwidth, height=0.4\\textheight, keepaspectratio]{{{img_path}}}"
            
        # 5. Inject data into section template
        section_tex = section_template
        section_tex = section_tex.replace("{{title}}", title.upper())
        section_tex = section_tex.replace("{{aim}}", aim)
        section_tex = section_tex.replace("{{algorithm}}", algorithm)
        section_tex = section_tex.replace("{{code_language}}", config['code_language'])
        section_tex = section_tex.replace("{{code}}", code_content)
        section_tex = section_tex.replace("{{output}}", output_latex)
        
        all_sections += section_tex + "\n"

    # 6. Build Final Document
    final_tex = base_template
    final_tex = final_tex.replace("{{course_name}}", config.get("course_name", ""))
    final_tex = final_tex.replace("{{author_name}}", config.get("author_name", ""))
    final_tex = final_tex.replace("{{author_roll}}", config.get("author_roll", ""))
    final_tex = final_tex.replace("{{body}}", all_sections)

    # 7. Save Output
    output_file = OUT_DIR / "Lab_Record.tex"
    output_file.write_text(final_tex, encoding='utf-8')
    print(f"\nSuccess! Lab record generated at {output_file}")

if __name__ == "__main__":
    main()