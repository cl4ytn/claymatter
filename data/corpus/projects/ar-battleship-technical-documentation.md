---
category: projects
---

## AR-Battleship Project Overview

AR-Battleship is a hybrid augmented reality reimagining of the classic strategy board game. Built for mobile devices using Unity and Vuforia, the prototype replaces traditional physical boards and manual bookkeeping with digital tracking driven by physical AR markers. Players use a board marker for the 10x10 grid, an aim marker to select target cells, and a confirm marker to execute shots. This design reduces setup overhead and prevents accidental disruption of the game state while preserving the tactile, strategic appeal of a tabletop game.

## AR-Battleship Architecture and Game Engine

The game engine is split into three decoupled layers: domain, application, and Unity scripts. The domain layer contains the core rules in a Board and BattleshipGame class, enforcing turn order, boundary checks, and win conditions using typed Result returns rather than exceptions. A dedicated NUnit dotnet project was used to unit test this logic independently of Unity. The application layer handles player snapshots and enforces fog of war, ensuring opponent ship data remains hidden until sunk. The GameManager MonoBehaviour routes calls between single-player and multiplayer sessions while keeping the rules engine isolated from UI and AR dependencies.

## AR-Battleship Networking and Unity Relay

Multiplayer functionality supports a two-player competitive format where one user acts as the host and the other connects as a client. Unity Relay was chosen as the networking solution, allowing players to connect via a generated join code without directly exposing their IP addresses or network ports. The networking layer is kept separate from the core game rules, acting only to transmit player actions like ship placements and firing coordinates. This separation ensures that network transmission delays or dropped messages cannot result in an inconsistent board state, as all actions are validated by the domain rules engine.

## AR-Battleship Augmented Reality and Manual Fallbacks

The augmented reality system uses Vuforia Engine for multi-target image detection. Three physical markers govern board placement, targeting, and firing, creating a two-step confirmation flow that prevents accidental shots. The AR layer functions strictly as a visual and input interface, subscribing to GameManager events without modifying game state directly. Additionally, a manual coordinate input system was implemented as a fallback for situations with poor lighting or limited physical space. This fallback also allowed the game logic and UI layers to be tested without requiring physical markers to be present.

## AR-Battleship 3D Models and Visual Design

To make the game more immersive than simple 2D grids, open-license 3D ship models were sourced and reviewed for consistent scale and art style. Using Blender, ships were split into separate segment prefabs that spawn progressively as the opponent successfully lands hits. These ship section prefabs were configured as child objects of their respective tiles, with rotations and coordinates hard-coded for both horizontal and vertical cases to prevent runtime bugs. Water prefabs were also used to construct the 10x10 grid, providing a thematic sea environment that visually reflects the underlying domain state.

## AR-Battleship Security and Privacy Considerations

The project addresses security and privacy by adhering to Australian Privacy Principles, collecting only the minimum data required for gameplay without requiring user accounts or persistent storage. Camera usage is strictly limited to recognizing the three designated AR game markers and does not record or upload environmental data or faces. Network security is maintained by treating join codes as temporary access tokens and routing actions through Unity Relay, where only minimal game action commands are transmitted rather than identifying user information.