# The "I Refuse to Typeset" Lab Record Generator

Why would you spend 2 hours doing repetitive things manually when you could spend 4 hours automating it instead. That's how I started making the Lab Record Generator. 

This is an almost totally automated, recursive, markdown-parsing LaTeX engine. You write your code, you take your screenshots, you scribble some markdown, and this Python script stitches the whole thing into a pristine, beautifully formatted PDF-ready `.tex` file. **Ideally**. **Hopefully**.

## Installation

This tool is designed to integrate seamlessly into your existing workspace without requiring structural changes to your project directories. It operates as an independent module alongside your current lab files.

1. **Navigate to your workspace:** Open your terminal or command prompt and change the directory to your primary class folder (the parent directory containing your lab experiment subdirectories).
2. **Clone the repository:** Execute the following command to clone the tool directly into a new folder named `generator`:

```bash
git clone https://github.com/neverneeth/Lab-Latex-Generator/.git generator

```

3. **Verify the directory structure:** Once the cloning process is complete, ensure your project hierarchy matches the following layout:

```text
Your-Main-Class-Folder/       # Original directory
├── Lab Cycle Solutions/      # Subfolder containing your lab resources
│   ├── Q1_Experiment_Name/   # A subfolder corresponding to each experiment. The prefix specified in config.json is ignored. Everything else is parsed into natural language
│   │   ├── codefile.ext      # Every directory can have zero or more code files with the extension specified in config.json. The code by default placed in sections called program 
│   │   ├──output.jpg         # Every directory can have zero or more output image files(jpg, png) which by default are placed in output sections
|   │   ├── something.md      # Every directory can have zero or more md files which can be used to specify the internal structure of each experiment. Every heading(# or ## in markdown) is treated as a section inside an experiment
│   └── Q2_Experiment_Name/
└── generator/                # What you just cloned
    ├── generate.py
    ├── config.json
    └── templates/

```

## Configure `config.json`

Modify `generator/config.json` to match the requirements of your specific course and directory structure.

```json
{
  "course_name": "Operating Systems Lab",
  "author_name": "Your Name Here",
  "author_roll": "Your Roll Number",
  "code_language": "C",
  "code_extension": ".c",
  "expts_dir": "Lab Cycle Solutions",
  "output_dir": "output",
  "strip_step_prefix": false, 
  "regex": {
    "expit_dir_enum_prefix": "Q[0-9]+_"
  }
}

```

### Configuration Parameters:

* **`code_language` & `code_extension`:** Identifies the target code files for syntax highlighting and formatting.
* **`expts_dir`:** Defines the path to your main experiments directory.
* **`strip_step_prefix`:** When set to `true`, the script removes repetitive prefixes like `**Step 1:**` from your Markdown so LaTeX can handle the numbered lists cleanly natively. Defaults to `false`.
* **`expit_dir_enum_prefix`:** The regex pattern used to identify experiment folders. For example, `Q[0-9]+_` correctly targets folders formatted as `Q1_Name`, `Q12_Name`, etc.

---

## How to Structure Your Files

The generator is built to recursively handle a variety of file structures and edge cases. Here is how to set up your directories for different scenarios:

### 1. Standard Experiments

For a basic experiment, place your source code (`main.c`), notes (`README.md`), and screenshot (`output.png`) directly inside the experiment folder (e.g., `Q1_Basic`). The script will extract the Aim and Algorithm from the Markdown, format the code, and apply a frame to the image automatically.

### 2. Multi-Part Experiments

If a single question contains multiple subdivisions (e.g., parts a, b, and c), create nested subfolders for each part:

```text
Q7_IPC/
├── a_pipe/
├── b_message_que/
└── c_share_mem/

```

The script will recursively process these subfolders, synthesize a collective aim, append the individual algorithms, and compile the code files sequentially in lexicographical order.

### 3. Multiple Code Files

If your experiment spans multiple source files (e.g., `main.c`, `functions.c`, and `structs.c`), save them all within the same directory. The generator will extract all matching files and prepend a descriptive comment block (e.g., `/* ====== File: functions.c ====== */`) above each snippet to maintain clarity in the final document.

### 4. Multiple Screenshots

To document extended output or various test cases, include all necessary `.png` or `.jpg` files within the experiment folder. The script handles multiple images by generating consecutive, framed figures in the output file.

### 5. Dynamic Indexing

Folders are numbered based on their physical presence rather than their strict naming conventions. If your directories are named `Q1_`, `Q2_`, and `Q8_`, the final PDF will dynamically index them sequentially as Program 1, Program 2, and Program 3, preventing gaps in your lab record.

### 6. Markdown Translation

Your `README.md` files require no manual LaTeX. Write normally, and the script will natively translate standard syntax such as `**bold**`, `*italic*`, and ``inline code`` tags into appropriate LaTeX formatting prior to injection.

---

Would you like me to draft a quick, copy-pasteable `README.md` template that users can drop into their experiment folders to ensure the parser always catches their Aim and Algorithm headings perfectly?

