import os
import sys
import json
import builtins
import importlib.util
import shutil
from pathlib import Path
from rlm.environments.local_repl import LocalREPL

class GameREPL(LocalREPL):
    def __init__(self, workspace_dir: str = "game_world", template_dir: str = "game_world_template", **kwargs):
        self.workspace_path = Path(workspace_dir).absolute()
        self.template_path = Path(template_dir).absolute()
        
        if self.template_path.exists() and not (self.workspace_path / "skills").exists():
            shutil.copytree(self.template_path, self.workspace_path, dirs_exist_ok=True)
        
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        self.skills_path = self.workspace_path / "skills"
        for folder in ["world", "skills", "lore"]:
            (self.workspace_path / folder).mkdir(exist_ok=True)
        
        super().__init__(**kwargs)
        self.temp_dir = str(self.workspace_path)

        if str(self.skills_path) not in sys.path:
            sys.path.append(str(self.skills_path))
        if self.temp_dir not in sys.path:
            sys.path.append(self.temp_dir)

    def setup(self):
        super().setup()
        setattr(builtins, "json", json)
        setattr(builtins, "os_path_exists", os.path.exists)
        setattr(builtins, "os_listdir", os.listdir)

        kernel_tools = {
            "read_lore": self._read_lore,
            "update_state": self._update_state,
            "get_state": self._get_state,
            "list_skills": self._list_skills,
            "reload_skills": self._bootstrap_skills,
            "llm_query": self._llm_query,
            "llm_query_batched": self._llm_query_batched,
            "help": self._help_tool,
            "get_sensory_context": self.get_sensory_context,  # Expose sensory context refresh
            "FINAL": lambda x: x # FIX: Define FINAL so it doesn't crash if called in REPL
        }

        for name, func in kernel_tools.items():
            setattr(builtins, name, func)
            self.globals[name] = func  # Use globals instead of locals to ensure persistence

        self._bootstrap_skills()

    def _bootstrap_skills(self):
        count = 0
        # Ensure we always look for .py files, excluding internal ones
        for skill_file in self.skills_path.glob("*.py"):
            if skill_file.stem.startswith("__") or skill_file.stem.startswith("."): 
                continue
            
            try:
                module_name = skill_file.stem
                if module_name in sys.modules:
                    importlib.reload(sys.modules[module_name])
                    module = sys.modules[module_name]
                else:
                    spec = importlib.util.spec_from_file_location(module_name, skill_file)
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                
                # Make available in REPL environment
                self.locals[module_name] = module
                setattr(builtins, module_name, module) # Also set in builtins for easier access
                count += 1
            except Exception as e:
                # Log error but don't crash the bootstrap process
                print(f"Warning: Failed to load skill {skill_file.name}: {e}")
                
        return f"System: {count} skills active/reloaded."

    def get_sensory_context(self) -> str:
        """
        Reads the current player state and location description.
        Can be called mid-turn to refresh context after an action.
        """
        player = self._get_state("player")
        loc = player.get("location", "Unknown")
        desc = self._read_lore(f"locations/{loc}") if loc != "Unknown" else "You are in the void."
        return f"--- SENSORY DATA ---\nLOCATION: {loc}\nSTATUS: {json.dumps(player)}\nAREA DESC: {desc}\n"

    def _read_lore(self, topic: str) -> str:
        path = self.workspace_path / "lore" / f"{topic}.md"
        if not path.exists():
            matches = list(self.workspace_path.glob(f"lore/**/{topic}.md"))
            if matches: path = matches[0]
            else: return f"Note: No specific lore found for '{topic}'."
        return path.read_text()

    def _update_state(self, category: str, data: dict):
        path = self.workspace_path / "world" / f"{category}.json"
        current = self._get_state(category)
        current.update(data)
        path.write_text(json.dumps(current, indent=2))
        return f"Updated {category} state."

    def _get_state(self, category: str) -> dict:
        path = self.workspace_path / "world" / f"{category}.json"
        if path.exists():
            return json.loads(path.read_text())
        return {}

    def _list_skills(self) -> list[str]:
        return [f.stem for f in self.skills_path.glob("*.py") if not f.stem.startswith("__")]

    def _help_tool(self):
        return (
            "--- RLM GAME ENGINE HELP ---\n"
            "SYSTEM TOOLS:\n"
            "- skill_manager.create(skill_name, code_content, doc_content='...') \n"
            "- skill_manager.inspect(skill_name) -> Reads .md and .py files\n"
            "- skill_manager.consult_expert(domain, query) -> Recursive lore lookup\n"
            "- combat.attack(target_name, damage_type='physical')\n"
            "- get_state(category) -> e.g., get_state('player')\n"
            "- update_state(category, dict) -> Updates JSON files in /world\n"
            "- read_lore(topic) -> e.g., read_lore('magic/crystals')\n"
            "- get_sensory_context() -> Returns current player status/location\n\n"
            "USAGE: Always print() results. Use FINAL(text) OUTSIDE of code blocks to finish."
        )

    def cleanup(self):
        self.globals.clear()
        self.locals.clear()