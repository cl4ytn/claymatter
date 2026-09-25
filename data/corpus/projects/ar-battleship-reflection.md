---
 category: projects
---

## AR Battleship Project Overview

Augmented reality (AR) displays virtual assets over physical objects through a mobile phone's camera. Ichiban Group developed AR Battleship to blend a ten-by-ten grid boardgame with AR, automating rule management and game-state tracking via a fiducial marker recognition system. As the key game logic developer, my role aimed to build a clean, testable Unity project that enforced game rules, tracked win/loss conditions, and seamlessly integrated a virtual game engine with the tabletop experience.

## Ethics and Privacy in AR Development

Examining AR Battleship through the Rights and Justice perspectives highlighted critical privacy concerns. Permitting camera access without transparent prompts risked users' digital autonomy and exposed them to third-party infrastructure. Furthermore, our use of a copyrighted Metal Gear Solid soundtrack bypassed property rights, while adopting Unity Relay created dependency vulnerabilities following Unity's per-install fee policy changes. Complying with ethical frameworks requires looking beyond immediate solutions to reinforce long-term user trust and rights.

## Engineering a Decoupled C# Architecture

To resolve early logic conflicts and satisfy our project brief, I took complete ownership of building a decoupled C# architecture. I used .NET to separate the system into a Domain project for core board game rules and an Application project to orchestrate state transitions. To ensure reliability, I built two test suites using NUnit to test every function across both components. This structural choice ensured our core game loop was foolproof, allowing teammates to rely on stable underlying logic.

## Multiplayer Scheduling and Bottlenecks

Our hasty project management created a massive bottleneck for multiplayer functionality using Unity Relay. Because I spent extensive time developing the core logic in isolation, my teammate Pascal was left waiting on my final code to implement the networking architecture. Although Pascal successfully integrated Unity Relay by week twelve, our lack of parallel scheduling triggered immense team pressure. Future projects require publishing mocked interfaces and dummy data structures early to prevent team members from waiting on dependent tasks.

## Prototype Usability Testing and UI Evaluation

We conducted usability tests using specific user tasks and System Usability Scale questionnaires, which uncovered major ambiguities in our user interface. Players struggled due to a lack of interactive feedback, tiny text, and unintuitive fiducial markers. Through the Justice Perspective, we realized an unfair cognitive overload on uninitiated players. Iteratively integrating this feedback allowed us to fix interface gaps before final submission, proving that usability testing must be continuous rather than a final-week afterthought.

## Final Crunch and Lessons on Transparency

Our final development weeks involved massive integration chaos, including UI overhauls, broken singleplayer logic, and a build too large to submit. Our primary failing was a lack of ongoing communication regarding friction points and progress. By week twelve, we coordinated to soft-submit early, but realizing the value of transparency taught me to adopt agile practices like daily stand-ups. Identifying friction early allows teams to divide and conquer effectively before facing last-minute technical debt.