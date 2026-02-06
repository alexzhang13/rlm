"""
Executable combat logic.
Note: get_state and update_state are available via builtins.
"""
import random

def attack(target_name, damage_type="physical"):
    # 1. Get State
    player = get_state("player")
    # For this demo, we assume a static enemy if not in state
    enemy = get_state(f"enemy_{target_name}")
    if not enemy:
        # Mock enemy for the test
        enemy = {"name": target_name, "hp": 20}
    
    # 2. Roll Logic
    roll = random.randint(1, 20)
    
    # 3. Calculate Damage
    damage = 0
    message = f"Rolled a {roll}. "
    
    if roll == 20:
        damage = 20
        message += "CRITICAL HIT! "
    elif roll > 10:
        damage = 10
        message += "Hit! "
    else:
        message += "Miss. "
        return message

    # Elemental Logic (Hardcoded for demo, but could read .md)
    if damage_type == "fire" and "goblin" in target_name.lower():
        damage *= 2
        message += "Super effective (Fire)! "

    # 4. Update State
    enemy['hp'] -= damage
    update_state(f"enemy_{target_name}", enemy)
    
    message += f"Dealt {damage} damage. {target_name} HP is now {enemy['hp']}."
    return message