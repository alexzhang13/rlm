"""
Alchemy Skill - Handles item combinations.
"""

def combine_items(item_a, item_b):
    player = get_state("player")
    inventory = player.get("inventory", [])
    
    # Check if player has the items
    if item_a not in inventory or item_b not in inventory:
        return f"FAILURE: You do not have both {item_a} and {item_b} in your inventory."
    
    # Recipe Logic
    if (item_a == "blue_crystal" and item_b == "void_salts") or \
       (item_a == "void_salts" and item_b == "blue_crystal"):
        
        # Remove ingredients
        inventory.remove(item_a)
        inventory.remove(item_b)
        
        # Add result
        inventory.append("stabilized_crystal")
        
        # Update World State
        update_state("player", {"inventory": inventory})
        
        return "SUCCESS: You have synthesized a Stabilized Crystal. It no longer reacts to metal."
    
    return f"FAILURE: Combining {item_a} and {item_b} produces nothing but a foul smell."