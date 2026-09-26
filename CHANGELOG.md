# Changelog

- 2026-09-26 **1.1.1**
    - The image is published for amd64 and arm64 under one tag, built and published automatically on every change and every week
    - The documentation states that the API is open to everybody when no API key is configured
    - Threads keep their state: a run on a thread did not write it to the database, so `GET /threads/{id}/state` always answered «Thread not found», and where a state existed it answered with an empty object
    - Several instances can start at the same moment against one database; before, all but one died while creating the checkpoint tables
    - The service starts again without an LLM key: the sample graph failed at start with «Missing credentials», so the documented local answer `[local-echo] …` never worked

- 2026-07-16 **1.1.0**
    - The shipped image is now automatically verified to contain no shell and no scripting language besides Python

- 2026-03-27 **1.0.0**
    - LangGraph agent workflows as a REST API: health check, list of graphs, stateless runs, threads with runs and state
    - Graphs are loaded from Python modules in a mounted directory
    - Threads are kept in PostgreSQL; the service refuses to start without a database
    - Bearer token authentication, with the key from a Docker secret or the environment
    - Any OpenAI compatible LLM endpoint; without a key the sample graph answers locally
