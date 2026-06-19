# Local CLI Runner Feasibility

Last verified: 2026-06-19

This project treats the filesystem and `events.jsonl` as the source of truth. CLI runners are adapters that read generated prompt files and write Markdown results into `inbox/<agent>/` before the workflow imports them into immutable `agents/<agent>/...vN.md` files.

## Summary

| Runner | Status | Mode | Evidence |
|---|---|---|---|
| Codex CLI | Supported | Headless command runner | Smoke test produced `MADR_RUNNER_SMOKE_OK`. |
| Claude Code | Supported | Headless command runner | Smoke test produced `MADR_RUNNER_SMOKE_OK`. |
| Antigravity CLI | Partial | Launch-and-wait runner | CLI accepts stdin and opens a chat session, but current local CLI did not write the requested output file headlessly. |

## Codex CLI

Command template:

```text
"{executable}" exec --cd "{workspace}" --sandbox read-only -o "{output_file}" - < "{prompt_file}"
```

Observed behavior:

- Reads prompt from stdin.
- Writes the model answer to the requested output file.
- Can be slow, so runner execution must stay asynchronous.
- May print plugin or skill warnings to stderr; these do not necessarily mean the result failed.

## Claude Code

Command template:

```text
type "{prompt_file}" | "{executable}" -p --output-format text > "{output_file}"
```

Observed behavior:

- Reads prompt from stdin.
- Writes the model answer to stdout, which the command redirects to the requested output file.
- Smoke test completed successfully as a headless runner.

## Antigravity CLI

Command template:

```text
"{executable}" chat --mode agent - < "{instruction_file}"
```

Observed behavior:

- Reads stdin and reports `Reading from stdin via: ...`.
- Opens or hands off to an Antigravity chat session.
- The CLI process exits with code `0` before any requested output file is written.
- The runner therefore records `waiting_input` and leaves the workflow waiting for an output file or a manual/file submission.

Current integration stance:

- Antigravity is registered and visible in Web UI runner health.
- Antigravity smoke tests are asynchronous and return quickly.
- Antigravity cannot yet be treated as a fully headless runner in this local setup.
- If Antigravity later writes the expected Markdown file into `inbox/<agent>/`, the next graph step imports it before launching another runner.

## Next Work

- Find whether Antigravity exposes a true headless completion mode or output-file flag.
- If no headless mode exists, keep Antigravity as a launch-and-wait runner and make its waiting state clearer in the Web UI.
- Run a full mixed-run workflow with Codex and Claude as headless agents, then verify the Antigravity handoff path with a real file written into `inbox/<agent>/`.
