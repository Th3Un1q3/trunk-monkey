# Architecture

## Current
```mermaid
flowchart TD
%% Nodes
    A[User]
    B[Assistant]
    C[Thread]
    D[Vector Store]
    E[Local Functions]
    F[Trunk-Monkey CLI]
    G[CI Automation]
    H[GitHub]
    I[Slack]

%% Edge connections between nodes
    A --> |Runs locally| F
    A --> |Commits and pushes| H
    B --> |Searches| D 
    B --> |Calls| E
    C --> |Uses| B
    F --> |Initiates| C
    F --> |Uploads code to| D
    G --> |Runs| F
    G --> |Sends results to| I
    H --> |Triggers| G
```

## Design ideas
- Automatically triggered checks
- Git actions such as blame, history and diff implemented functions
- Source code is uploaded(some sub parts of it) by schedule
- Checks implemented as prompts
- Output should be a function call, so that it's machine readable
