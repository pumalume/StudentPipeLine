# SchoolPipeProject — Visual Folder Architecture

This document provides a visual breakdown of the repository's file tree and module hierarchy.

---

## 1. Visual Module Map (Flowchart Layout)

```mermaid
flowchart LR
    classDef root fill:#1e88e5,stroke:#0d47a1,stroke-width:2px,color:#fff;
    classDef dir fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1;
    classDef file fill:#ffffff,stroke:#90caf9,stroke-width:1px,color:#333;
    classDef core fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#e65100;

    ROOT["📁 SchoolPipeProject"]:::root

    ROOT --> CFG["📁 config/"]:::dir
    ROOT --> DAT["📁 data/"]:::dir
    ROOT --> SRC["📁 src/"]:::dir
    ROOT --> TST["📁 tests/"]:::dir
    ROOT --> ENV[".env.example"]:::file
    ROOT --> REQ["requirements.txt"]:::file

    %% Config Branch
    CFG --> CFG_SET["settings.py"]:::file

    %% Data Branch
    DAT --> DAT_IN["📁 input/"]:::file
    DAT --> DAT_LOG["📁 logs/"]:::file

    %% Source Core
    SRC --> MAIN["main.py (Orchestrator)"]:::core
    SRC --> EXT["📁 extractors/"]:::dir
    SRC --> TRN["📁 transformers/"]:::dir
    SRC --> LDR["📁 loaders/"]:::dir

    EXT --> EX1["wordpress_extractor.py"]:::file
    EXT --> EX2["gdrive_extractor.py"]:::file
    EXT --> EX3["excel_extractor.py"]:::file

    TRN --> TR1["metadata_pivoter.py"]:::file
    TRN --> TR2["schema_sanitizer.py"]:::file

    LDR --> LD1["postgres_loader.py"]:::file

    %% Tests
    TST --> TS1["test_extractors.py"]:::file
    TST --> TS2["test_transformers.py"]:::file
