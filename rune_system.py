import random

class Rune:
    def __init__(self, name, symbol, category):
        self.name = name
        self.symbol = symbol
        self.category = category
        # Effects for different positions (alpha, beta, gamma, etc.)
        self.position_effects = {}
        
    def __str__(self):
        return f"{self.symbol} ({self.name})"

class RuneSystem:
    def __init__(self):
        self.runes = []
        self.position_order = []  # Will store the randomized order of positions
        self.categories = ["damage", "target", "modifier", "connector"]
        
    def generate_runes(self, num_runes=20):
        """Generate a set of runes with random effects"""
        damage_types = ["fire", "ice", "lightning", "earth", "arcane", "void"]
        target_types = ["single", "area", "self", "line", "cone", "random"]
        modifier_types = ["amplify", "extend", "split", "diminish", "stabilize", "volatile"]
        connector_types = ["chain", "bind", "link", "merge", "separate", "transform"]
        
        rune_types = {
            "damage": damage_types,
            "target": target_types,
            "modifier": modifier_types,
            "connector": connector_types
        }
        
        symbols = "αβγδεζηθικλμνξοπρστυφχψω"  # Greek letters as symbols
        used_symbols = set()
        
        for _ in range(num_runes):
            category = random.choice(self.categories)
            effect_type = random.choice(rune_types[category])
            
            # Get a unique symbol
            symbol = random.choice(symbols)
            while symbol in used_symbols:
                symbol = random.choice(symbols)
            used_symbols.add(symbol)
            
            rune = Rune(f"{effect_type.capitalize()} {category.capitalize()}", symbol, category)
            
            # Generate random effects for each position
            positions = ["alpha", "beta", "gamma", "delta", "epsilon", 
                         "zeta", "eta", "theta", "iota", "kappa"]
            
            for pos in positions:
                # Simplified effect generation - in a real game this would be more complex
                power = random.randint(1, 10)
                duration = random.randint(1, 5)
                rune.position_effects[pos] = {
                    "power": power,
                    "duration": duration,
                    "description": f"{effect_type} effect (power: {power}, duration: {duration})"
                }
            
            self.runes.append(rune)
    
    def generate_position_order(self, max_length=10):
        """Generate the randomized order of positions for spells of different lengths"""
        positions = ["alpha", "beta", "gamma", "delta", "epsilon", 
                     "zeta", "eta", "theta", "iota", "kappa"]
        
        # Start with just alpha
        self.position_order = [["alpha"]]
        
        # For each length, insert the new position somewhere in the previous order
        current_order = ["alpha"]
        for i in range(1, max_length):
            new_pos = positions[i]
            insert_idx = random.randint(0, len(current_order))
            new_order = current_order.copy()
            new_order.insert(insert_idx, new_pos)
            self.position_order.append(new_order)
            current_order = new_order
    
    def cast_spell(self, rune_sequence):
        """Attempt to cast a spell with the given sequence of runes"""
        if not rune_sequence:
            return "No runes selected."
        
        spell_length = len(rune_sequence)
        if spell_length > len(self.position_order):
            return "Spell too complex - cannot be cast."
        
        # Get the position order for this spell length
        positions = self.position_order[spell_length - 1]
        
        # Map runes to positions
        spell_components = []
        for i, rune in enumerate(rune_sequence):
            position = positions[i]
            effect = rune.position_effects[position]
            spell_components.append({
                "rune": rune,
                "position": position,
                "effect": effect
            })
        
        # Evaluate the spell (simplified)
        total_power = sum(comp["effect"]["power"] for comp in spell_components)
        spell_categories = [rune.category for rune in rune_sequence]
        
        # Check for valid spell combinations (simplified)
        has_damage = "damage" in spell_categories
        has_target = "target" in spell_categories
        
        if has_damage and has_target:
            success = True
            backfire = False
        elif random.random() < 0.3:  # 30% chance of backfire for invalid combinations
            success = False
            backfire = True
        else:
            success = False
            backfire = False
        
        # Generate result
        if success:
            result = f"Success! Spell cast with power {total_power}.\n"
            result += "Components:\n"
            for comp in spell_components:
                result += f"  {comp['rune']} in {comp['position']} position: {comp['effect']['description']}\n"
        elif backfire:
            result = f"Backfire! The spell destabilizes and causes {total_power // 2} damage to the caster.\n"
        else:
            result = "Fizzle. The runes glow briefly but nothing happens.\n"
        
        return result

# Example usage
if __name__ == "__main__":
    # Initialize the system
    rune_system = RuneSystem()
    rune_system.generate_runes()
    rune_system.generate_position_order()
    
    # Print available runes
    print("Available Runes:")
    for i, rune in enumerate(rune_system.runes):
        print(f"{i+1}. {rune} - {rune.category}")
    
    # Print position orders
    print("\nPosition Orders for Different Spell Lengths:")
    for i, order in enumerate(rune_system.position_order):
        print(f"{i+1} runes: {' -> '.join(order)}")
    
    # Example spell casting
    print("\nExample Spells:")
    for _ in range(3):
        spell_length = random.randint(1, 5)
        runes = random.sample(rune_system.runes, spell_length)
        print(f"\nCasting spell with runes: {', '.join(str(r) for r in runes)}")
        result = rune_system.cast_spell(runes)
        print(result)