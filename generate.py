import json
import re
import shutil
from pathlib import Path

# Set up base paths relative to the script location
GEN_DIR = Path(__file__).parent
BASE_DIR = GEN_DIR.parent

def escape_latex(text):
    """Escapes special LaTeX characters to prevent compilation errors."""
    if not text: return text
    replacements = { '#': r'\#', '%': r'\%', '&': r'\&', '_': r'\_', '$': r'\$' }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text

def format_algorithm(text, strip_prefix):
    """Converts markdown lists to LaTeX items, conditionally stripping prefixes."""
    lines = text.split('\n')
    formatted = []
    for line in lines:
        line = line.strip()
        if not line: continue
        
        if strip_prefix:
            # Detects "\textbf{Step 1:}", "Step 1:", "1.", etc.
            step_match = re.match(r'^(?:\\textbf\{)?Step\s*\d+:(?:\})?\s*', line, re.IGNORECASE)
            num_match = re.match(r'^\d+\.\s*', line)
            
            if step_match:
                clean_line = line[step_match.end():]
                formatted.append(f"\\item {clean_line}")
            elif num_match:
                clean_line = line[num_match.end():]
                formatted.append(f"\\item {clean_line}")
            else:
                formatted.append(f"\\item {line}")
        else:
            # If flag is false, just wrap the whole raw line in \item
            formatted.append(f"\\item {line}")
            
    return "\n".join(formatted)

def parse_readme(readme_path, fallback_title, language):
    aim = f"To write a {language} program to implement {fallback_title}."
    algorithm = "\\item Algorithm not provided."
    
    if readme_path.exists():
        content = readme_path.read_text(encoding='utf-8')
        
        aim_match = re.search(r'# AIM\n(.*?)(?=# ALGORITHM|\Z)', content, re.DOTALL | re.IGNORECASE)
        if aim_match:
            aim = escape_latex(aim_match.group(1).strip())
            
        algo_match = re.search(r'# ALGORITHM\n(.*)', content, re.DOTALL | re.IGNORECASE)
        if algo_match:
            safe_algo = escape_latex(algo_match.group(1).strip())
            algorithm = format_algorithm(safe_algo)
        else:
            safe_content = escape_latex(content.strip())
            algorithm = format_algorithm(safe_content)
            
    return aim, algorithm

def main():
    config_path = GEN_DIR / "config.json"
    if not config_path.exists():
        print(f"Error: Could not find {config_path}")
        return
        
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    exp_dir_name = config.get("expts_dir", "experiments")
    out_dir_name = config.get("output_dir", "output")
    prefix_regex = config.get("regex", {}).get("expit_dir_enum_prefix", r"^\d+_")
    
    EXP_DIR = BASE_DIR / exp_dir_name
    OUT_DIR = BASE_DIR / out_dir_name

    base_template_path = GEN_DIR / "templates" / "base_template.tex"
    section_template_path = GEN_DIR / "templates" / "section_template.tex"
    
    if not base_template_path.exists() or not section_template_path.exists():
        print("Error: Template files missing in generator/templates/")
        return
        
    base_template = base_template_path.read_text(encoding='utf-8')
    section_template = section_template_path.read_text(encoding='utf-8')

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if not EXP_DIR.exists():
        print(f"Error: The target directory '{EXP_DIR}' was not found.")
        return

    exp_folders = [d for d in EXP_DIR.iterdir() if d.is_dir()]
    
    def get_sort_key(folder):
        match = re.match(prefix_regex, folder.name)
        if match:
            num_match = re.search(r'\d+', match.group())
            if num_match:
                return int(num_match.group())
        return 9999 
        
    exp_folders.sort(key=get_sort_key)

    all_sections = ""

    for folder in exp_folders:
        prefix_match = re.match(prefix_regex, folder.name)
        if not prefix_match:
            continue 
            
        print(f"Processing {folder.name}...")
        
        title_raw = folder.name[prefix_match.end():]
        title_safe = escape_latex(title_raw.replace('_', ' '))
        
        readme_path = folder / "README.md"
        aim, algorithm = parse_readme(readme_path, title_safe, config['code_language'])
        
        # --- NEW LOGIC FOR MINTED CODE FILES ---
        code_files = list(folder.glob(f"*{config['code_extension']}"))
        code_block_latex = "No code file found."
        
        if code_files:
            src_code = code_files[0]
            safe_folder_name = folder.name.replace(' ', '_')
            new_code_name = f"{safe_folder_name}_code{src_code.suffix}"
            dest_code_path = OUT_DIR / new_code_name
            
            # Copy the code file to output directory
            shutil.copy2(src_code, dest_code_path)
            
            # Minted usually expects lowercase language names (e.g., 'c', 'python')
            lang_lower = config['code_language'].lower()
            code_block_latex = f"\\inputminted[linenos, breaklines, fontsize=\\small]{{{lang_lower}}}{{{new_code_name}}}"
        # ---------------------------------------
        
        # Handle Image File
        img_files = list(folder.glob("*.png")) + list(folder.glob("*.jpg"))
        output_latex = "No output screenshot found."
        
        if img_files:
            src_img = img_files[0]
            safe_folder_name = folder.name.replace(' ', '_')
            new_img_name = f"{safe_folder_name}_out{src_img.suffix}"
            dest_img_path = OUT_DIR / new_img_name
            
            shutil.copy2(src_img, dest_img_path)
            output_latex = f"\\includegraphics[width=\\textwidth, height=0.4\\textheight, keepaspectratio]{{{new_img_name}}}"
            
        section_tex = section_template
        section_tex = section_tex.replace("{{title}}", title_safe.upper())
        section_tex = section_tex.replace("{{aim}}", aim)
        section_tex = section_tex.replace("{{algorithm}}", algorithm)
        # We inject the minted command directly instead of raw code text
        section_tex = section_tex.replace("{{code_block}}", code_block_latex) 
        section_tex = section_tex.replace("{{output}}", output_latex)
        
        all_sections += section_tex + "\n"

    final_tex = base_template
    final_tex = final_tex.replace("{{course_name}}", config.get("course_name", ""))
    final_tex = final_tex.replace("{{author_name}}", config.get("author_name", ""))
    final_tex = final_tex.replace("{{author_roll}}", config.get("author_roll", ""))
    final_tex = final_tex.replace("{{body}}", all_sections)

    output_file = OUT_DIR / "Lab_Record.tex"
    output_file.write_text(final_tex, encoding='utf-8')
    print(f"\nSuccess! Lab record, code files, and images generated in '{OUT_DIR.resolve()}'")

if __name__ == "__main__":
    main()