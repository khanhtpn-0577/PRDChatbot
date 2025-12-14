


def generate_tree_structure(
    folder: str, 
    max_depth: int = 5, 
    skip_dirs=None, 
    indent: str = "", 
    is_root=True
):
    """
    Generate a clean and readable directory tree, optimized for LLM context.
    
    Args:
        folder: root folder path
        max_depth: maximum recursion depth
        skip_dirs: directories to ignore
        indent: internal indent handling
        is_root: print root header only once
        
    Returns:
        A formatted tree string
    """

    import os

    if skip_dirs is None:
        skip_dirs = {
            "node_modules", ".git", "__pycache__", ".venv",
            "dist", "build", ".next", ".pytest_cache", "venv"
        }

    result = []

    # Print root folder name only once
    if is_root:
        result.append(f"[ROOT] {os.path.abspath(folder)}")
    
    current_depth = indent.count("│")
    if current_depth >= max_depth:
        return "\n".join(result)

    try:
        items = sorted(os.listdir(folder))
    except PermissionError:
        return "\n".join(result)

    dirs, files = [], []
    for item in items:
        path = os.path.join(folder, item)
        if os.path.isdir(path) and item not in skip_dirs:
            dirs.append(item)
        elif os.path.isfile(path):
            files.append(item)

    # Print directories
    for i, d in enumerate(dirs):
        is_last = (i == len(dirs) - 1 and len(files) == 0)
        prefix = "└── " if is_last else "├── "

        result.append(f"{indent}{prefix}{d}/")

        new_indent = indent + ("    " if is_last else "│   ")
        subtree = generate_tree_structure(
            os.path.join(folder, d),
            max_depth=max_depth,
            skip_dirs=skip_dirs,
            indent=new_indent,
            is_root=False
        )
        if subtree:
            result.append(subtree)

    # Print files
    for i, f in enumerate(files):
        is_last = (i == len(files) - 1)
        prefix = "└── " if is_last else "├── "
        result.append(f"{indent}{prefix}{f}")

    return "\n".join(result)

if __name__ == "__main__":
    tree = generate_tree_structure("frontend", max_depth=10)
    print(tree)