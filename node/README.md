# MagnetBank Node Worker

The synchronization engine responsible for monitoring the Hive blockchain and indexing MagnetBank operations.

## 🚀 Capabilities
- **Real-time Sync**: Tracks the live head of the Hive blockchain.
- **Batch Processing**: Efficiently retrieves and processes blocks in configurable batches (default: 100) to minimize API latency.
- **Atomic Commits**: Uses SQLAlchemy session management to perform bulk SQLite insertions, ensuring data integrity and high performance.
- **Custom JSON Protocol**: Parses `custom_json` operations with the `MagnetBank` ID.
- **Admin Support**: Handles `update` and `delete` actions broadcast by the authorized `ADMIN_ACCOUNT`.

## 🛠️ Execution

### Run the Node
From the project root:
```bash
uv run python node/node.py
```

### Configuration
The node depends on several environment variables defined in the root `.env`:
- `HIVE_NODE`: Hive API endpoint(s).
- `ADMIN_ACCOUNT`: Hive account for admin ops.
- `GENISYS_BLOCK`: Starting point for first-time synchronization.
- `SQLITE_DB`: Destination database file.

## 📊 Monitoring
Logs are output to `stdout` with detailed information about scanned blocks and ingested metadata. The node also updates the `head_block` setting in SQLite, which is displayed on the frontend `/about` dashboard.
