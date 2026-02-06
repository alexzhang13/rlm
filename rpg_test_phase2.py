import os
import argparse
import json
from pathlib import Path
from rlm import RLM

def setup_test_env():
    Path("game_world_template/lore/magic").mkdir(parents=True, exist_ok=True)
    Path("game_world_template/skills").mkdir(parents=True, exist_ok=True)
    Path("game_world_template/world").mkdir(parents=True, exist_ok=True)
    
    with open("game_world_template/lore/magic/crystals.md", "w") as f:
        f.write("Blue Crystals vibrate at 440Hz. They explode if touched by metal.")
    
    with open("game_world_template/world/player.json", "w") as f:
        json.dump({"name": "Ob1", "hp": 100, "location": "The Crystal Cave", "inventory": ["metal_sword"]}, f)

GM_SYSTEM_PROMPT = """You are the RLM Game Engine.
The `context` contains SENSORY DATA followed by the PLAYER ACTION.

RULES OF THE REPL:
1. MANDATORY PRINT: You MUST wrap every tool call or variable check in `print()`. If you don't print it, you won't see the result and you will fail.
   - Good: `print(combat.attack('goblin'))`
   - Bad: `combat.attack('goblin')`
2. GLOBAL NAMESPACE: Skills are loaded as global modules. If you create a skill named 'scout', you call it as `print(scout.run())`. 
   - DO NOT use `skill_manager.skills`. 
   - If you are unsure what is available, call `print(help())`.
3. SKILL STRUCTURE: When creating a skill, always define a function like `def run():`.

YOUR GOAL: Execute the player's request and provide a FINAL_VAR() narrative.

Reminder: use `repl` lang identifier instead of `python` when using the REPL.

Example:
```repl
print("Hello World")
```

FINAL_VAR(): The final narrative of the turn, from a variable. This is the output of the RLM.

Tips: 
1. Save the narrative in a variable. Use some multiline-friendly string format such as triple quotes.
2. Call `FINAL_VAR(narrative)` to return the final narrative of the turn. Do not wrap FINAL_VAR in `print()`.
A `FINAL_VAR` call automatically ends your turn and returns the narrative to the player.
"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--model", default="x-ai/grok-4.1-fast") # Good at coding
    parser.add_argument("-k", "--api_key_var", default="INFERENCE_API_KEY")
    parser.add_argument("-b", "--base_url", default="https://api.pinference.ai/api/v1")
    args = parser.parse_args()

    api_key = os.environ.get(args.api_key_var)
    
    rlm = RLM(
        backend="openai",
        backend_kwargs={"model_name": args.model, "api_key": api_key, "base_url": args.base_url},
        environment="game",
        environment_kwargs={
            "workspace_dir": "game_world",
            "template_dir": "game_world_template"
        },
        verbose=True,
        custom_system_prompt=GM_SYSTEM_PROMPT,
        max_iterations=8
    )

    with rlm._spawn_completion_context("init") as (handler, env):
        sensory = env.get_sensory_context()

    player_action = (
        "1. Consult the 'magic' expert about Blue Crystals and metal. "
        "2. Attack the 'crystal_golem' with my sword. "
        "3. Create a 'scout' skill (Rules: find shadows. Code: def run(): return 'Shadow found'). "
        "4. Use the scout skill by calling its run function."
    )

    full_context = sensory + "\nPLAYER ACTION: " + player_action

    print(f"--- Starting Refactored Phase 2 Test with {args.model} ---")
    rlm.completion(full_context)

if __name__ == "__main__":
    setup_test_env()
    main()