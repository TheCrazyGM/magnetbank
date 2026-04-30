# TODO Checklist

## Modernization Tasks

- [x] **1. Template Consolidation**
  - [x] Refactor `list.html` to use `torrents.html`.
  - [x] Refactor `user.html` to use `torrents.html`.
  - [x] Ensure all list views are consistent.

- [x] **2. Form Category Update**
  - [x] Update `add.html` to use the new category list (VIDEO, AUDIO, APP, TEXT, OTHER).
  - [x] Update `convert.html` and `admin.html`.

- [x] **3. Form Validation Polish**
  - [x] Fix `add.html`: Only show validation messages after an actual submission attempt.
  - [x] Fix `convert.html`: Only show validation messages after an actual upload attempt.

- [x] **4. Exact Source Integration**
  - [x] Add `exact_source` column to the `torrents` table in `utils/database.py`.
  - [x] Update `node/node.py` to ingest `exact_source` from custom_json operations.
  - [x] Update `frontend/templates/details.html` to display the `exact_source` link.
  - [x] Update `frontend/templates/torrents.html` (card grid) to show a source icon.

- [x] **5. Node Modernization**
  - [x] Refactor `node/node.py` for performance and best practices.
  - [x] Improve error handling and Hive node rotation/failover.
  - [x] Implement cleaner logging and batch processing.
