# Claudit CLI — Lessons Learned

## Entry Point

- The CLI is `claudit` (defined in `pyproject.toml` → `claudit.cli:main`).
- Do NOT use `python -m claudit.skills.<skill>` — those are packages, not runnable modules.

## Subcommand Syntax

| Skill | Correct | Wrong |
|-------|---------|-------|
| path  | `claudit path find <src> <tgt> <dir>` | `python -m claudit.skills.path find ...` |
| graph callees | `claudit graph callees <func> <dir>` | `claudit graph query --callees <func>` |
| graph callers | `claudit graph callers <func> <dir>` | `claudit graph query --callers <func>` |
| highlight path | `claudit highlight path <f1> <f2> ... --project-dir <dir>` | — |

## Flag Placement

- `--language` is accepted by `claudit path find` but NOT by `claudit graph callees/callers`.
  Graph subcommands infer language automatically from the cached index.
- `--max-depth N` is a `path find` option (default 10).

## Known Limitations

- **GNU Global misses Java interface→impl edges.** `createOrGet` → `getByName` was
  not captured because `createOrGet` is declared in the `ScimGroupProvisioning`
  interface while the call to `getByName` lives in the `JdbcScimGroupProvisioning`
  implementation. When `path find` returns 0 paths, verify manually by reading
  the source of intermediate functions.
- When the graph seems incomplete, use `claudit graph callees <func> <dir>` to
  inspect what edges exist, then manually check source for missing call sites.

## Workflow: Finding a Path When Auto-Discovery Fails

1. Run `claudit path find <src> <tgt> <dir>` first.
2. If 0 paths, use `claudit graph callees <src>` to see direct callees.
3. Use `claudit graph callers <tgt>` to see what calls the target.
4. Read source of promising intermediate functions to find the missing edge.
5. Once the full chain is confirmed, pass the hop list to `claudit highlight path`.
