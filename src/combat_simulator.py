"""
Combat Simulator — data-driven edition.

Design notes
------------
* One `Attack` type drives *everything*. Player attacks and NPC attacks are
  the same object, so both sides get accuracy, crits, and damage variance
  for free — the rules can't drift apart.
* Combat is pure data + a resolver. The `Battle` class only sequences turns
  and renders output; `resolve_attack()` only does math. Easy to unit test.
* The RNG is injected, not global, so a battle can be replayed from a seed.
* Enemies pick attacks by *expected damage* (accuracy * damage * crit), so
  they don't blindly spam their slowest, least reliable move.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

CRIT_MULTIPLIER = 2.0
PLAYER_MAX_HP = 200


# --------------------------------------------------------------------------
# Core data
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Attack:
    """A single move. `accuracy` and `crit` are probabilities in [0, 1]."""

    name: str
    damage: int
    accuracy: float
    crit: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.accuracy <= 1.0:
            raise ValueError(f"{self.name}: accuracy must be in [0, 1]")
        if not 0.0 <= self.crit <= 1.0:
            raise ValueError(f"{self.name}: crit must be in [0, 1]")

    @property
    def expected_damage(self) -> float:
        """Average damage per swing — the number an AI should optimize."""
        return self.damage * self.accuracy * (1 + self.crit)


@dataclass
class Combatant:
    name: str
    max_hp: int
    attacks: tuple[Attack, ...]
    hp: int = field(init=False)

    def __post_init__(self) -> None:
        if not self.attacks:
            raise ValueError(f"{self.name} has no attacks")
        self.hp = self.max_hp

    @property
    def alive(self) -> bool:
        return self.hp > 0


@dataclass(frozen=True)
class AttackResult:
    attacker: str
    target: str
    attack: Attack
    hit: bool
    crit: bool
    damage: int


# --------------------------------------------------------------------------
# Content
# --------------------------------------------------------------------------
WEAPONS: dict[str, tuple[Attack, ...]] = {
    "sword": (
        Attack("Slash", 50, 0.90, 0.15),
        Attack("Heavy Strike", 80, 0.75, 0.25),
        Attack("Sword Burst", 120, 0.60, 0.35),
    ),
    "axe": (
        Attack("Chop", 60, 0.85, 0.20),
        Attack("Axe Smash", 100, 0.70, 0.30),
        Attack("Execution", 150, 0.50, 0.50),
    ),
}


@dataclass(frozen=True)
class EnemyTemplate:
    max_hp: int
    attacks: tuple[Attack, ...]


ENEMIES: dict[str, EnemyTemplate] = {
    "villager": EnemyTemplate(30, (Attack("Jab", 8, 0.65, 0.05),)),
    "goblin": EnemyTemplate(
        100,
        (
            Attack("Stab", 14, 0.75, 0.10),
            Attack("Frenzy", 26, 0.50, 0.25),
        ),
    ),
    "orc": EnemyTemplate(
        250,
        (
            Attack("Cleave", 24, 0.70, 0.15),
            Attack("Brutal Swing", 40, 0.55, 0.30),
        ),
    ),
    "knight": EnemyTemplate(
        500,
        (
            Attack("Shield Bash", 22, 0.85, 0.10),
            Attack("Lance Thrust", 38, 0.70, 0.20),
            Attack("Impale", 60, 0.45, 0.35),
        ),
    ),
}


# --------------------------------------------------------------------------
# Rules
# --------------------------------------------------------------------------
def resolve_attack(
    attacker: Combatant,
    target: Combatant,
    attack: Attack,
    rng: random.Random,
) -> AttackResult:
    """Roll accuracy, then crit. Applies damage to `target` on a hit."""
    if rng.random() > attack.accuracy:
        return AttackResult(attacker.name, target.name, attack, False, False, 0)

    crit = rng.random() < attack.crit
    damage = int(attack.damage * CRIT_MULTIPLIER) if crit else attack.damage
    target.hp = max(0, target.hp - damage)

    return AttackResult(attacker.name, target.name, attack, True, crit, damage)


# --------------------------------------------------------------------------
# Presentation
# --------------------------------------------------------------------------
def health_bar(current: int, maximum: int, width: int = 18) -> str:
    filled = round(width * current / maximum) if maximum else 0
    return f"[{'#' * filled}{'.' * (width - filled)}] {current:>3}/{maximum}"


def format_result(result: AttackResult) -> str:
    if not result.hit:
        return f"  {result.attacker} uses {result.attack.name} — MISS."
    tag = "CRITICAL HIT! " if result.crit else ""
    return f"  {result.attacker} uses {result.attack.name} — {tag}{result.damage} damage."


def pick(prompt: str, options: list[str]) -> str:
    """Numbered menu. Returns the chosen option verbatim."""
    print(f"\n{prompt}")
    for i, option in enumerate(options, 1):
        print(f"  {i}. {option}")
    while True:
        raw = input("> ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print(f"  Enter a number between 1 and {len(options)}.")


# --------------------------------------------------------------------------
# Battle
# --------------------------------------------------------------------------
class Battle:
    def __init__(self, player: Combatant, enemy: Combatant, rng: random.Random) -> None:
        self.player = player
        self.enemy = enemy
        self.rng = rng

    def run(self) -> bool:
        """Runs to completion. Returns True if the player won."""
        print(f"\n{self.player.name} ({self.player.max_hp} HP) vs "
              f"{self.enemy.name} ({self.enemy.max_hp} HP)")

        while True:
            self._take_turn(self.player, self.enemy, self._player_attack())
            if not self.enemy.alive:
                return True

            self._take_turn(self.enemy, self.player, self._enemy_attack())
            if not self.player.alive:
                return False

    def _take_turn(self, actor: Combatant, target: Combatant, attack: Attack) -> None:
        print(f"\n{'-' * 52}")
        print(f"{self.player.name:<12}{health_bar(self.player.hp, self.player.max_hp)}")
        print(f"{self.enemy.name:<12}{health_bar(self.enemy.hp, self.enemy.max_hp)}")
        print(f"{'-' * 52}")

        result = resolve_attack(actor, target, attack, self.rng)
        print(format_result(result))
        if result.hit:
            print(f"  (hit chance was {attack.accuracy:.0%})")

    # -- attack selection --------------------------------------------------
    def _player_attack(self) -> Attack:
        by_name = {a.name: a for a in self.player.attacks}
        if len(by_name) == 1:
            return next(iter(by_name.values()))
        return by_name[pick("Choose your attack:", list(by_name))]

    def _enemy_attack(self) -> Attack:
        """Pick the highest expected-damage move, with a little jitter."""
        return max(
            self.enemy.attacks,
            key=lambda a: a.expected_damage * self.rng.uniform(0.9, 1.1),
        )


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------
def main() -> None:
    rng = random.Random()  # pass a seed for reproducible fights

    print("=" * 52)
    print("        COMBAT SIMULATOR — HITBOX EDITION")
    print("=" * 52)

    enemy_name = pick("Choose your opponent:", list(ENEMIES))
    template = ENEMIES[enemy_name]
    enemy = Combatant(enemy_name.title(), template.max_hp, template.attacks)

    weapon_name = pick("Choose your weapon:", list(WEAPONS))
    player = Combatant("You", PLAYER_MAX_HP, WEAPONS[weapon_name])

    won = Battle(player, enemy, rng).run()
    print(f"\n{'*' * 52}")
    print(f"  {'VICTORY — ' + enemy.name + ' is defeated!' if won else 'DEFEAT — you have fallen.'}")
    print(f"{'*' * 52}")


if __name__ == "__main__":
    main()