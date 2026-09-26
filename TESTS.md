# Tests

Register of all tests, sorted by the [FEATURES.md](FEATURES.md) number each test covers. `npm test` runs everything; the guard `tests/docs-contract.sh` fails when a feature has no test entry here or a test carries a skip marker.

## E2E (`tests/run-e2e.sh`, client `tests/e2e/test_api.py`, real PostgreSQL)

- **F1** health_without_token — `/ok` answers without a token.
- **F2** graphs_listed_with_token, graph_from_graphs_dir_runs — `echo` and the mounted `upper` are listed, and `upper` runs.
- **F3** stateless_run_echo, unknown_graph_404 — a stateless run, and 404 for an unknown graph.
- **F4** thread_created, thread_run, thread_state_stored, unknown_thread_404, thread_state_survives_restart — a thread keeps its state in the database, also after the agent restarted (regression: the checkpointer was handed to `ainvoke()`, which ignores it, and no state was ever stored).
- **F5** database_from_password_secret, refuses_to_start_without_database — the database from the password secret, and no start without a database.
- **F6** graphs_refused_without_token, graphs_refused_with_wrong_token, run_refused_without_token, secret_key_accepted, secret_wins_over_environment, no_key_means_no_authentication — the token, where it comes from, and the open API without one.
- **F7** stateless_run_echo, thread_run — without `OPENAI_API_KEY` the echo graph answers locally (regression: the graph created the OpenAI client at import, which refuses an empty key, and the service did not start).
- **F7** llm_answers_with_configured_model — with the key from the secret `litellm_master_key`, the echo graph asks the local OpenAI compatible endpoint `fake-llm` for the model `LLM_MODEL` and returns its answer.

- **F10** health checks of `agent`, `agent-secret`, `agent-open` and `agent-llm`, which the runner starts at once against one database (regression: all but one died with «duplicate key value violates unique constraint checkpoint_migrations_pkey»).

## Image contract

- **F8** `tests/image-contract.sh` › no sh, no bash, no busybox, no perl — the image is headless.

## Workflow contract

- **F9** `tests/workflow-contract.sh` of `mwaeckerlin/scratch` — the reusable workflow selects exactly the images a repository publishes; this repository calls it from `.github/workflows/docker.yml`.
