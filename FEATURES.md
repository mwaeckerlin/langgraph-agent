# Features

Numbered register of every feature; a number is never reused. Every feature is covered by tests listed in [TESTS.md](TESTS.md); the guard `tests/docs-contract.sh` fails when a feature has no test.

- **F1 — Health check.** `GET /ok` answers `{"status": "ok"}` without authentication.
- **F2 — Graphs from a directory.** Every Python module in `GRAPHS_DIR` (default `/app/graphs`) that exports `graph` is loaded at start under its `name`, with its `description`; `GET /graphs` lists them.
- **F3 — Stateless run.** `POST /runs` runs the named graph with the given input and configuration and returns its output; an unknown graph answers 404.
- **F4 — Threads with persistence.** `POST /threads` creates a thread id, `POST /threads/{id}/runs` runs a graph with the state kept in PostgreSQL, `GET /threads/{id}/state` returns the stored state, also after a restart; an unknown thread answers 404.
- **F5 — Database required.** The database comes from `DATABASE_URI`, or from the secret `langgraph_db_password` for the user and database `langgraph` on host `db`; without either the service does not start.
- **F6 — Bearer token.** With a key configured, every endpoint except `/ok` requires `Authorization: Bearer <key>`; the key comes from the secret `langgraph_api_key`, which wins, or from `LANGGRAPH_API_KEY`. Without a key the API is open to everybody.
- **F7 — Local answer without LLM key.** The sample graph `echo` answers `[local-echo] <message>` when `OPENAI_API_KEY` is empty, so the stack works without an LLM; with a key it asks the model `LLM_MODEL` at `OPENAI_BASE_URL`, and the secret `litellm_master_key` provides the key.
- **F8 — Headless.** The image contains Python and the application, no shell.
- **F9 — Published for amd64 and arm64.** Every push builds the image natively for both architectures and publishes it under one tag on Docker Hub, with the reusable workflow of `mwaeckerlin/scratch`.
- **F10 — Several instances on one database.** Instances that start at the same moment against the same database migrate the checkpoint tables one after the other, so every one of them comes up.
