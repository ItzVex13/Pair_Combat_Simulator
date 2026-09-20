# Simple Python Hitbox / Combat Simulator

# NPC Health
npc_hp = {
    "villager": 30,
    "knight": 500,
    "goblin": 100,
    "orc": 250
}

# Weapon Skills and Damage
weapons = {
    "sword": {
        "Slash": 50,
        "Heavy Strike": 80,
        "Sword Burst": 120
    },
    "axe": {
        "Chop": 60,
        "Axe Smash": 100,
        "Execution": 150
    }
}

while True:
    print("\n===== COMBAT SIMULATOR =====")

    # Choose NPC
    print("\nAvailable NPCs:")
    for npc in npc_hp:
        print("-", npc.title())

    npc = input("\nEnter the NPC you want to fight: ").lower()

    if npc not in npc_hp:
        print("NPC not found!")
        continue

    health = npc_hp[npc]

    print(f"\nYou selected: {npc.title()}")
    print(f"HP: {health}")

    # Choose Weapon
    print("\nChoose your weapon:")
    print("1. Sword")
    print("2. Axe")

    weapon_choice = input("Enter your choice: ")

    if weapon_choice == "1":
        weapon = "sword"
    elif weapon_choice == "2":
        weapon = "axe"
    else:
        print("Invalid weapon choice!")
        continue

    # Combat Loop
    while health > 0:

        print(f"\n{npc.title()} HP: {health}")

        print(f"\n{weapon.title()} Skills:")

        skills = list(weapons[weapon].keys())

        for i, skill in enumerate(skills, 1):
            damage = weapons[weapon][skill]
            print(f"{i}. {skill} - {damage} damage")

        skill_choice = input("\nChoose a skill: ")

        if skill_choice not in ["1", "2", "3"]:
            print("Invalid skill!")
            continue

        skill = skills[int(skill_choice) - 1]
        damage = weapons[weapon][skill]

        # Deal damage
        health -= damage

        # Prevent negative HP
        if health < 0:
            health = 0

        print(f"\nYou used {skill}!")
        print(f"You dealt {damage} damage!")
        print(f"{npc.title()} HP: {health}")

    # NPC defeated
    print(f"\n💀 {npc.title()} has been defeated!")

    # Continue?
    print("\nWhat do you want to do?")
    print("1. Fight another NPC")
    print("2. Stop playthrough")

    again = input("Enter your choice: ")

    if again == "2":
        print("\nPlaythrough ended.")
        break

    elif again != "1":
        print("\nInvalid choice. Playthrough ended.")
        break