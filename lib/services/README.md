# CNTRLR Services

This library contains various services that extend the core functionality of the CNTRLR application. These services are designed to be modular and can be integrated seamlessly with the core framework.

## Available Services

- **Importer Services**:
  - `file_importer`
    - Services that handle the importing of data from various sources into the CNTRLR system.
      - 'repository_importer': Imports data from code repositories.
      - 'web_importer': Imports data from web sources.
      - 'image_importer': Imports image data.
      - 'video_importer': Imports video data.
      - 'audio_importer': Imports audio data.
      - 'obsidian_importer': Imports data from Obsidian vaults.
- **File System Services**:
  - Services that power the cre of the CLI tools for general development as well as specific file system operations.
- **Context Management Services**:
  - Services that manage and manipulate context data within the CNTRLR framework.
