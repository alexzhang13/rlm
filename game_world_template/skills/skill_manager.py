"""
Skill Manager - Create, inspect, and manage skills dynamically.

Uses the WorldEngine for state and LLM for expert queries.
Includes validation to prevent broken code from being saved.
"""
import os
import ast
import importlib.util
import sys
import traceback


def inspect(skill_name: str) -> str:
    """
    Inspect a skill's documentation and code.
    
    Args:
        skill_name: Name of the skill to inspect
    
    Returns:
        Combined documentation and code content.
    """
    output = []
    
    md_path = f"skills/{skill_name}.md"
    py_path = f"skills/{skill_name}.py"
    
    if os.path.exists(md_path):
        with open(md_path) as f:
            output.append(f"=== {skill_name}.md (RULES) ===\n{f.read()}")
    else:
        output.append(f"=== {skill_name}.md (RULES) ===\n[No documentation]")
    
    if os.path.exists(py_path):
        with open(py_path) as f:
            output.append(f"\n=== {skill_name}.py (CODE) ===\n{f.read()}")
    else:
        output.append(f"\n=== {skill_name}.py (CODE) ===\n[No code]")
    
    return "\n".join(output)


def create(skill_name: str, code_content: str, doc_content: str = "No rules provided.") -> str:
    """
    Create a new skill with code and documentation.
    Validates Python syntax before saving to prevent breaking the engine.
    
    Args:
        skill_name: Name for the new skill (no spaces, python identifier)
        code_content: Python code for the skill
        doc_content: Markdown documentation
    
    Returns:
        Status message and usage instructions.
    """
    # 1. Validation: Check if skill_name is valid identifier
    if not skill_name.isidentifier():
        return f"ERROR: Invalid skill name '{skill_name}'. Must be a valid Python identifier."
    
    # 2. Validation: Syntax Check
    try:
        ast.parse(code_content)
    except SyntaxError as e:
        return f"ERROR: Syntax error in code. Operation cancelled.\nTraceback: {e}"

    # 3. Validation: Test Import (Dry Run)
    # Write to a temp file to test importability without breaking the real skill
    temp_path = f"skills/.tmp_{skill_name}.py"
    try:
        with open(temp_path, "w") as f:
            f.write(code_content)
        
        # Try importing the temp module
        spec = importlib.util.spec_from_file_location(f"tmp_{skill_name}", temp_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Clean up temp file
        os.remove(temp_path)
        
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return f"ERROR: Runtime error during import check. Code logic might be broken.\nError: {e}\n{traceback.format_exc()}"

    # 4. Success: Write actual files
    try:
        # Write documentation
        with open(f"skills/{skill_name}.md", "w") as f:
            f.write(doc_content)
        
        # Write code
        with open(f"skills/{skill_name}.py", "w") as f:
            f.write(code_content)
        
        # Reload skills to make it available immediately
        reload_skills()
        
        return f"SUCCESS: Skill '{skill_name}' created and loaded. Use: print({skill_name}.run())"
        
    except Exception as e:
        return f"ERROR: Failed to write skill files: {e}"


def consult_expert(domain: str, query: str) -> str:
    """
    Query the lore library with an LLM expert.
    
    Aggregates all lore files in a domain and uses the LLM
    to answer questions based on that context.
    
    Args:
        domain: Lore domain (subdirectory name, e.g., "magic")
        query: Question to ask
    
    Returns:
        Expert's answer based on lore documents.
    """
    lore_dir = f"lore/{domain}"
    
    if not os.path.exists(lore_dir):
        return f"Domain '{domain}' not found in the lore library."
    
    # Aggregate all lore documents
    context_parts = []
    for filename in os.listdir(lore_dir):
        if filename.endswith(".md"):
            with open(os.path.join(lore_dir, filename)) as f:
                content = f.read()
                context_parts.append(f"=== {filename} ===\n{content}")
    
    if not context_parts:
        return f"No lore documents found in '{domain}'."
    
    full_context = "\n\n".join(context_parts)
    
    prompt = (
        f"You are an Expert Librarian specializing in {domain}.\n"
        f"Answer the following query based ONLY on the provided documents.\n"
        f"If the answer is not in the documents, say so.\n\n"
        f"Query: {query}\n\n"
        f"Documents:\n{full_context}"
    )
    
    return llm_query(prompt)