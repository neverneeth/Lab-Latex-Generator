import json
import re
import shutil
from pathlib import Path

# Set up base paths relative to the script location
GEN_DIR = Path(__file__).parent
BASE_DIR = GEN_DIR.parent

def escape_latex(text):
    if not text: return text
    replacements = { '#': r'\#', '%': r'\%', '&': r'\&', '_': r'\_', '$': r'\$' }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text

def markdown_to_latex(text):
    if not text: return text
    text = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'\\textit{\1}', text)
    text = re.sub(r'`(.*?)`', r'\\texttt{\1}', text)
    return text

def format_algorithm(text, strip_prefix):
    lines = text.split('\n')
    formatted = []
    for line in lines:
        line = line.strip()
        if not line: continue
        
        if strip_prefix:
            step_match = re.match(r'^(?:\\textbf\{)?Step\s*\d+:(?:\})?\s*', line, re.IGNORECASE)
            num_match = re.match(r'^\d+\.\s*', line)
            
            if step_match:
                formatted.append(f"\\item {line[step_match.end():]}")
            elif num_match:
                formatted.append(f"\\item {line[num_match.end():]}")
            else:
                formatted.append(f"\\item {line}")
        else:
            formatted.append(f"\\item {line}")
    return "\n".join(formatted)

def parse_readme(readme_path, fallback_title, language, strip_prefix):
    aim = ""
    algorithm_latex = ""
    content = readme_path.read_text(encoding='utf-8')
    
    # 1. Extract AIM
    aim_match = re.search(r'^#+\s*AIM\s*\n(.*?)(?=(^#+\s|\Z))', content, re.DOTALL | re.IGNORECASE | re.MULTILINE)
    if aim_match:
        safe_aim = escape_latex(aim_match.group(1).strip())
        aim = markdown_to_latex(safe_aim)
        
    # 2. Extract ALL Algorithm Headings & Content
    algo_pattern = r'^#+\s+(?!AIM\s*$)(.*?)\s*\n(.*?)(?=(^#+\s|\Z))'
    algo_matches = list(re.finditer(algo_pattern, content, re.DOTALL | re.IGNORECASE | re.MULTILINE))
    
    if algo_matches:
        for match in algo_matches:
            raw_heading = match.group(1).strip()
            algo_heading = escape_latex(raw_heading).upper()
            
            safe_algo = escape_latex(match.group(2).strip())
            md_algo = markdown_to_latex(safe_algo)
            algorithm_items = format_algorithm(md_algo, strip_prefix)
            
            algorithm_latex += (
                f"\n%==================== {algo_heading} ====================%\n"
                f"\\section*{{{algo_heading}}}\n"
                f"\\begin{{enumerate}}\n{algorithm_items}\n\\end{{enumerate}}\n"
            )
    elif not aim_match and content.strip():
        algo_heading = escape_latex(fallback_title).upper() + " ALGORITHM"
        safe_algo = escape_latex(content.strip())
        md_algo = markdown_to_latex(safe_algo)
        algorithm_items = format_algorithm(md_algo, strip_prefix)
        algorithm_latex += (
            f"\n%==================== {algo_heading} ====================%\n"
            f"\\section*{{{algo_heading}}}\n"
            f"\\begin{{enumerate}}\n{algorithm_items}\n\\end{{enumerate}}\n"
        )
        
    return aim, algorithm_latex

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
    strip_step_prefix = config.get("strip_step_prefix", True)
    
    EXP_DIR = BASE_DIR / exp_dir_name
    OUT_DIR = BASE_DIR / out_dir_name

    base_template = (GEN_DIR / "templates" / "base_template.tex").read_text(encoding='utf-8')
    section_template = (GEN_DIR / "templates" / "section_template.tex").read_text(encoding='utf-8')

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    exp_folders = [d for d in EXP_DIR.iterdir() if d.is_dir()]
    
    def get_sort_key(folder):
        match = re.match(prefix_regex, folder.name)
        if match:
            num_match = re.search(r'\d+', match.group())
            if num_match: return int(num_match.group())
        return 9999 
        
    exp_folders.sort(key=get_sort_key)
    all_sections = ""

    for folder in exp_folders:
        prefix_match = re.match(prefix_regex, folder.name)
        if not prefix_match: continue 
            
        print(f"Processing {folder.name}...")
        title_raw = folder.name[prefix_match.end():]
        title_safe = escape_latex(title_raw.replace('_', ' '))
        
        # --- 1. GATHER ALL MARKDOWN FILES RECURSIVELY ---
        md_files = sorted(list(folder.rglob("*.md")), key=lambda x: str(x.relative_to(folder)))
        aims_list, algos_list = [], []
        
        for md in md_files:
            # Pass the subfolder name as fallback title in case it has its own algorithm
            sub_title = md.parent.name if md.parent != folder else title_safe
            aim, algo = parse_readme(md, sub_title, config['code_language'], strip_step_prefix)
            if aim: aims_list.append(aim)
            if algo: algos_list.append(algo)
            
        combined_aim = "\n\n".join(aims_list) if aims_list else f"To write a {config['code_language']} program to implement {title_safe}."
        combined_algo = "\n".join(algos_list)
        
        # --- 2. GATHER ALL CODE FILES RECURSIVELY ---
        code_files = sorted(list(folder.rglob(f"*{config['code_extension']}")), key=lambda x: str(x.relative_to(folder)))
        code_block_latex = "No code file found."
        
        if code_files:
            code_block_latex = ""
            for i, src_code in enumerate(code_files):
                # Create a unique flat name for the output directory (e.g., Q7_IPC_a_pipe_main_code.c)
                safe_rel_path = str(src_code.relative_to(folder)).replace('\\', '_').replace('/', '_')
                new_code_name = f"{folder.name}_{safe_rel_path}"
                dest_code_path = OUT_DIR / new_code_name
                
                shutil.copy2(src_code, dest_code_path)
                
                lang_lower = config['code_language'].lower()
                
                # If there are multiple code files, print the filename above the code block for clarity
                if len(code_files) > 1:
                    display_name = escape_latex(str(src_code.relative_to(folder)).replace('\\', '/'))
                    code_block_latex += f"\\textbf{{\\texttt{{File: {display_name}}}}}\n"
                    
                code_block_latex += f"\\inputminted[linenos, breaklines, fontsize=\\small]{{{lang_lower}}}{{{new_code_name}}}\n\n"
        
        # --- 3. GATHER ALL IMAGES RECURSIVELY ---
        img_files = sorted(list(folder.rglob("*.png")) + list(folder.rglob("*.jpg")), key=lambda x: str(x.relative_to(folder)))
        output_latex = "No output screenshot found."
        
        if img_files:
            output_latex = ""
            for src_img in img_files:
                safe_rel_path = str(src_img.relative_to(folder)).replace('\\', '_').replace('/', '_')
                new_img_name = f"{folder.name}_{safe_rel_path}"
                dest_img_path = OUT_DIR / new_img_name
                
                shutil.copy2(src_img, dest_img_path)
                
                # Append a new figure block for EVERY image found
                output_latex += (
                    f"\\begin{{figure}}[H]\n"
                    f"    \\centering\n"
                    f"    \\fbox{{\\includegraphics[width=0.8\\textwidth, keepaspectratio]{{{new_img_name}}}}}\n"
                    f"\\end{{figure}}\n"
                )
            
        # --- INJECT INTO TEMPLATE ---
        section_tex = section_template
        section_tex = section_tex.replace("{{title}}", title_safe.upper())
        section_tex = section_tex.replace("{{aim}}", combined_aim)
        section_tex = section_tex.replace("{{algorithm_section}}", combined_algo)
        section_tex = section_tex.replace("{{code_block}}", code_block_latex.strip()) 
        section_tex = section_tex.replace("{{output_section}}", output_latex.strip())
        
        all_sections += section_tex + "\n"

    final_tex = base_template
    final_tex = final_tex.replace("{{course_name}}", config.get("course_name", ""))
    final_tex = final_tex.replace("{{author_name}}", config.get("author_name", ""))
    final_tex = final_tex.replace("{{author_roll}}", config.get("author_roll", ""))
    final_tex = final_tex.replace("{{body}}", all_sections)

    output_file = OUT_DIR / "Lab_Record.tex"
    output_file.write_text(final_tex, encoding='utf-8')
    print(f"\nSuccess! Lab record generated in '{OUT_DIR.resolve()}'")

if __name__ == "__main__":
    main()