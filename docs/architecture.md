```mermaid
sequenceDiagram
  participant CLI
  participant Executor
  participant Adapter
  CLI->>Executor: run manifest
  Executor->>Adapter: fetch()
  Adapter-->>Executor: Inline VAST

