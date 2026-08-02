mindmap
  root((📁 SchoolPipeProject))
    Root Files
      .env.example
      .gitignore
      README.md
      requirements.txt
    config
      settings.py
    data
      input
      logs
    src
      main.py
      extractors
        wordpress_extractor.py
        gdrive_extractor.py
        excel_extractor.py
      transformers
        metadata_pivoter.py
        schema_sanitizer.py
      loaders
        postgres_loader.py
    tests
      test_extractors.py
      test_transformers.py
