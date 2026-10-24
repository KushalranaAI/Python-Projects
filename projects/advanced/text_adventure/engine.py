"""The engine knows nothing about libraries or keys: rooms, items and puzzles all come from world.json.
Commands are objects (Command pattern) found through a registry of verbs and synonyms."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

WORLD_FILE = Path(__file__).with_name("world.json")
DIRECTIONS = {"n": "north", "s": "south", "e": "east", "w": "west", "u": "up", "d": "down"}
FILLER = {"the", "a", "an", "to", "at", "with", "on", "in", "into"}


@dataclass(frozen=True)
class World:
    data: dict

    @classmethod
    def load(cls, path: Path = WORLD_FILE) -> World:
        world = cls(json.loads(Path(path).read_text(encoding="utf-8")))
        world.validate()
        return world

    def validate(self) -> None:
        """Catch content mistakes when the game starts, not when a player walks into them."""
        rooms, items = self.data["rooms"], self.data["items"]
        for rid, room in rooms.items():
            for direction, target in room.get("exits", {}).items():
                if target not in rooms:
                    raise ValueError(f"Room {rid}: exit {direction} leads to unknown room {target}")
            for item in room.get("items", []) + list(room.get("locked", {}).values()):
                if item not in items:
                    raise ValueError(f"Room {rid}: unknown item {item}")
        if self.data["start"] not in rooms:
            raise ValueError("Unknown start room")

    def room(self, room_id: str) -> dict:
        return self.data["rooms"][room_id]

    def item(self, item_id: str) -> dict:
        return self.data["items"][item_id]


@dataclass
class GameState:
    """Everything that changes while playing - and nothing else. Serialises to a small dict."""

    location: str
    inventory: list[str] = field(default_factory=list)
    room_items: dict[str, list[str]] = field(default_factory=dict)
    unlocked: list[str] = field(default_factory=list)          # "room:direction"
    visited: list[str] = field(default_factory=list)
    lamp_lit: bool = False
    moves: int = 0
    won: bool = False

    @classmethod
    def new(cls, world: World) -> GameState:
        start = world.data["start"]
        return cls(start, room_items={rid: list(r.get("items", [])) for rid, r in world.data["rooms"].items()}, visited=[start])

    def to_dict(self) -> dict:
        return dict(vars(self))

    @classmethod
    def from_dict(cls, d: dict) -> GameState:
        return cls(**d)


class Command(ABC):
    verbs: tuple[str, ...] = ()
    help: str = ""

    @abstractmethod
    def execute(self, game: Game, noun: str) -> str: ...


class Game:
    def __init__(self, world: World, state: GameState | None = None):
        self.world = world
        self.state = state or GameState.new(world)
        self.commands: dict[str, Command] = {}
        for command in (Look(), Go(), Take(), Drop(), Inventory(), Examine(), Use(), Help()):
            for verb in command.verbs:
                self.commands[verb] = command

    # --- helpers commands use
    @property
    def room(self) -> dict:
        return self.world.room(self.state.location)

    @property
    def is_dark(self) -> bool:
        return self.room.get("dark", False) and not (self.state.lamp_lit and "lamp" in self.state.inventory)

    def items_here(self) -> list[str]:
        return self.state.room_items.get(self.state.location, [])

    def find_item(self, noun: str, places: list[str]) -> str | None:
        """Match 'key', 'iron key' or 'iron' against item ids and names."""
        for item_id in places:
            name = self.world.item(item_id)["name"]
            if noun in (item_id, name) or (noun and noun in name.split()):
                return item_id
        return None

    def describe_room(self) -> str:
        if self.is_dark:
            return "It is pitch black. You might be eaten by a grue."
        room = self.room
        lines = [f"== {room['name']} ==", room["description"]]
        if self.items_here():
            lines.append("You see: " + ", ".join(self.world.item(i)["name"] for i in self.items_here()) + ".")
        lines.append("Exits: " + ", ".join(room.get("exits", {})) + ".")
        return "\n".join(lines)

    # --- the one public entry point
    def handle(self, text: str) -> str:
        if self.state.won:
            return "You already won! Start a new game to play again."
        words = [w for w in text.lower().split() if w not in FILLER]
        if not words:
            return "Say something - try 'look' or 'help'."
        verb, noun = words[0], " ".join(words[1:])
        if verb in DIRECTIONS or verb in DIRECTIONS.values():          # "north" alone means "go north"
            verb, noun = "go", DIRECTIONS.get(verb, verb)
        command = self.commands.get(verb)
        if command is None:
            return f"I don't know how to '{verb}'. Type 'help'."
        self.state.moves += 1
        reply = command.execute(self, noun)
        goal = self.world.data["goal"]
        if goal["item"] in self.state.inventory and self.state.location == goal["room"]:
            self.state.won = True
            reply += f"\n\n🏆 {goal['message']} ({self.state.moves} moves)"
        return reply


# ---------------------------------------------------------------- commands
class Look(Command):
    verbs = ("look", "l")
    help = "look - describe where you are"

    def execute(self, game, noun):
        return game.describe_room()


class Go(Command):
    verbs = ("go", "walk", "move")
    help = "go <direction> - or just n / s / e / w / up / down"

    def execute(self, game, noun):
        direction = DIRECTIONS.get(noun, noun)
        room, state = game.room, game.state
        if direction not in room.get("exits", {}):
            return "You can't go that way."
        key = room.get("locked", {}).get(direction)
        if key and f"{state.location}:{direction}" not in state.unlocked:
            return f"The way {direction} is locked."
        if game.is_dark and direction != "up":
            return "You stumble around in the dark. Better find some light."
        state.location = room["exits"][direction]
        if state.location not in state.visited:
            state.visited.append(state.location)
        return game.describe_room()


class Take(Command):
    verbs = ("take", "get", "grab", "pick")
    help = "take <item>"

    def execute(self, game, noun):
        if game.is_dark:
            return "You can't see anything to take."
        noun = noun.removeprefix("up ").strip()
        item = game.find_item(noun, game.items_here())
        if item is None:
            return f"There's no {noun or 'such thing'} here."
        requirement = game.room.get("requires")
        if requirement and item in game.world.data["goal"]["item"] and requirement["item"] not in game.state.inventory:
            return requirement["message"]
        if not game.world.item(item)["portable"]:
            return "That won't budge."
        game.items_here().remove(item)
        game.state.inventory.append(item)
        if item == game.world.data["goal"]["item"] and requirement:
            game.state.inventory.remove(requirement["item"])
            return f"You fit the {game.world.item(requirement['item'])['name']} into the slot. The case opens - you take the {game.world.item(item)['name']}!"
        return f"Taken: {game.world.item(item)['name']}."


class Drop(Command):
    verbs = ("drop", "leave")
    help = "drop <item>"

    def execute(self, game, noun):
        item = game.find_item(noun, game.state.inventory)
        if item is None:
            return "You aren't carrying that."
        game.state.inventory.remove(item)
        game.state.room_items.setdefault(game.state.location, []).append(item)
        if item == "lamp":
            game.state.lamp_lit = False
        return f"Dropped: {game.world.item(item)['name']}."


class Inventory(Command):
    verbs = ("inventory", "inv", "i")
    help = "inventory - what you're carrying"

    def execute(self, game, noun):
        items = [game.world.item(i)["name"] + (" (lit)" if i == "lamp" and game.state.lamp_lit else "") for i in game.state.inventory]
        return "You carry: " + (", ".join(items) if items else "nothing") + "."


class Examine(Command):
    verbs = ("examine", "x", "read", "inspect")
    help = "examine <item>"

    def execute(self, game, noun):
        item = game.find_item(noun, game.state.inventory + ([] if game.is_dark else game.items_here()))
        return game.world.item(item)["description"] if item else "You don't see that here."


class Use(Command):
    verbs = ("use", "light", "unlock", "open")
    help = "use <item> - e.g. use lamp, use key"

    def execute(self, game, noun):
        item = game.find_item(noun.replace("door", "").strip() or "key", game.state.inventory)
        if item is None:
            return "You don't have that."
        if item == "lamp":
            game.state.lamp_lit = not game.state.lamp_lit
            return "The lamp flickers to life." if game.state.lamp_lit else "You put the lamp out."
        for direction, key in game.room.get("locked", {}).items():
            if key == item:
                marker = f"{game.state.location}:{direction}"
                if marker in game.state.unlocked:
                    return "It's already unlocked."
                game.state.unlocked.append(marker)
                return f"The {game.world.item(item)['name']} turns with a clunk. The way {direction} is open."
        return "Nothing happens."


class Help(Command):
    verbs = ("help", "h", "?")
    help = "help - this list"

    def execute(self, game, noun):
        unique = list(dict.fromkeys(game.commands.values()))
        return "Commands:\n" + "\n".join(f"  {c.help}" for c in unique)


def mermaid_map(game: Game) -> str:
    """A map of the rooms the player has visited (others stay a mystery)."""
    visited = set(game.state.visited)
    lines = ["flowchart TB"]
    for rid in visited:
        room = game.world.room(rid)
        marker = "📍 " if rid == game.state.location else ""
        lines.append(f'    {rid}["{marker}{room["name"]}"]')
        for direction, target in room.get("exits", {}).items():
            if target in visited and rid < target:
                lines.append(f"    {rid} ---|{direction}| {target}")
    return "\n".join(lines)
