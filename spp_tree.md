\# SchoolPipeProject — Visual Folder Architecture



This document provides a visual break down of the repository's file tree and module hierarchy.



\---



\## 1. Visual Module Map (Flowchart Layout)



This diagram highlights how files are logically grouped into pipeline phases (\*\*Configuration\*\*, \*\*Data\*\*, \*\*ETL Core\*\*, and \*\*Testing\*\*).



```mermaid

flowchart LR

&#x20;   classDef root fill:#1e88e5,stroke:#0d47a1,stroke-width:2px,color:#fff;

&#x20;   classDef dir fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1;

&#x20;   classDef file fill:#ffffff,stroke:#90caf9,stroke-width:1px,color:#333;

&#x20;   classDef core fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#e65100;



&#x20;   ROOT\["📁 SchoolPipeProject"]:::root



&#x20;   ROOT --> CFG\["📁 config/"]:::dir

&#x20;   ROOT --> DAT\["📁 data/"]:::dir

&#x20;   ROOT --> SRC\["📁 src/"]:::dir

&#x20;   ROOT --> TST\["📁 tests/"]:::dir

&#x20;   ROOT --> ENV\[".env.example"]:::file

&#x20;   ROOT --> REQ\["requirements.txt"]:::file



&#x20;   %% Config Branch

&#x20;   CFG --> CFG\_SET\["settings.py"]:::file



&#x20;   %% Data Branch

&#x20;   DAT --> DAT\_IN\["📁 input/"]:::file

&#x20;   DAT --> DAT\_LOG\["📁 logs/"]:::file



&#x20;   %% Source Core

&#x20;   SRC --> MAIN\["main.py (Orchestrator)"]:::core

&#x20;   SRC --> EXT\["📁 extractors/"]:::dir

&#x20;   SRC --> TRN\["📁 transformers/"]:::dir

&#x20;   SRC --> LDR\["📁 loaders/"]:::dir



&#x20;   EXT --> EX1\["wordpress\_extractor.py"]:::file

&#x20;   EXT --> EX2\["gdrive\_extractor.py"]:::file

&#x20;   EXT --> EX3\["excel\_extractor.py"]:::file



&#x20;   TRN --> TR1\["metadata\_pivoter.py"]:::file

&#x20;   TRN --> TR2\["schema\_sanitizer.py"]:::file



&#x20;   LDR --> LD1\["postgres\_loader.py"]:::file



&#x20;   %% Tests

&#x20;   TST --> TS1\["test\_extractors.py"]:::file

&#x20;   TST --> TS2\["test\_transformers.py"]:::file

