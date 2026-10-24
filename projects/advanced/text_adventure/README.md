---
title: Text Adventure Engine
order: 5
icon: 🗝️
time: 6-8 hours
summary: A classic interactive-fiction game - rooms, items, locked doors, darkness and a final puzzle - where the engine is generic and the whole world is a JSON file. Command pattern, data-driven design and serialisable game state.
python_skills:
  - JSON as a content format, validated on load
  - str.removeprefix, list/dict comprehensions
  - Parsing natural-ish commands (verbs, synonyms, filler words)
  - Generating diagrams from data (a Mermaid map)
oop_concepts:
  - Command pattern - one class per verb, found through a registry
  - Separation of static world data (World) and changing state (GameState)
  - Abstract base class for commands
  - Polymorphic dispatch by dictionary lookup
clean_code:
  - The engine contains no story - all content is data
  - Validate content when loading, with precise messages
  - Small serialisable state for save/load and sessions
  - A walkthrough test that plays the whole game
features:
  - "The Lost Library - 6 rooms, 6 items, a locked door, a dark archive and a final puzzle"
  - Commands with synonyms - go/walk, take/get/grab, examine/x/read, n/s/e/w/up/down
  - Save and load (terminal), session persistence (web)
  - A live map of the rooms you've visited
architecture: |
  classDiagram
    class World {
      <<frozen>>
      +data dict
      +load(path)$ World
      +validate()
      +room(id) dict
      +item(id) dict
    }
    class GameState {
      +location str
      +inventory list
      +room_items dict
      +unlocked list
      +visited list
      +lamp_lit bool
      +moves int
      +won bool
      +to_dict() dict
      +from_dict(d)$ GameState
    }
    class Game {
      +world World
      +state GameState
      +commands dict~verb, Command~
      +handle(text) str
      +describe_room() str
    }
    class Command {
      <<abstract>>
      +verbs tuple
      +help str
      +execute(game, noun)* str
    }
    class Look
    class Go
    class Take
    class Drop
    class Use
    class Examine
    Command <|-- Look
    Command <|-- Go
    Command <|-- Take
    Command <|-- Drop
    Command <|-- Use
    Command <|-- Examine
    Game --> World
    Game --> GameState
    Game o-- Command
flow: |
  flowchart LR
    I["'grab the brass lamp'"] --> W["words without filler:<br/>grab, brass, lamp"]
    W --> V{"commands['grab']"}
    V --> T["Take.execute(game, 'brass lamp')"]
    T --> F["find_item matches id / name / word"]
    F --> S["state changes: room_items → inventory"]
    S --> G{goal reached?}
    G -->|yes| WIN[🏆]
steps:
  - title: Separate world, state and engine
    files: [world.json, engine.py]
    body: |
      **World** = what never changes (rooms, exits, descriptions). **GameState** = what changes (location, inventory, unlocked
      doors, moves). **Game** = the rules connecting them. Saving a game means saving only the state.
  - title: Make content data
    files: [world.json]
    body: |
      Rooms list their exits, items, locks (`"locked": {"north": "key"}`), darkness and requirements. You could write a new
      adventure without touching Python, and `World.validate()` catches broken exits or unknown items at start-up.
  - title: Parse commands
    files: [engine.py]
    body: |
      `handle` lowercases, drops filler words ("the", "to"…), splits the verb from the noun and turns a bare direction into
      `go`. Then it looks the verb up in the command registry. Unknown verbs get a helpful reply instead of an exception.
  - title: One class per command
    files: [engine.py]
    body: |
      Each command subclasses `Command`, lists its verbs (synonyms!) and implements `execute`. The registry maps each verb to
      its command object. Adding "eat" or "talk" means adding one class, without editing a growing `if/elif` chain.
  - title: Puzzles are just conditions on state
    files: [engine.py]
    body: |
      Locked exits check `unlocked`, dark rooms check `lamp_lit`, and the final pedestal checks for the gear. Every rule is a
      couple of lines reading `GameState`, and every rule has a test.
  - title: Test by playing
    files: [tests/test_adventure.py]
    body: |
      `WALKTHROUGH` is the full solution as a list of commands; the test plays it and asserts that you win. Smaller tests cover
      each puzzle, error messages, synonyms, saving and the map.
  - title: Web and terminal front ends
    files: [cli.py, web.py, templates/text_adventure/index.html]
    body: |
      The terminal version adds `save` and `load` (JSON files). The web version keeps the state and the transcript in the
      session, and draws a map of visited rooms with Mermaid, generated from the world data.
exercises:
  - Add an **NPC** that gives a hint when you `talk` to it. Which classes and data change?
  - Add a **score** - points for first visits and found items - shown on winning.
  - Write a second world file (a space station?) and let the player choose it at the start.
  - Add **containers** (a chest you `open` to reveal items). Model it in the JSON first.
---

## Spoiler-free hint system

Stuck? The note in the corridor is a real clue, the archive is very dark, and the vault's pedestal wants something
mechanical. The full solution is in `tests/test_adventure.py`. Reading tests is a great way to understand code.
