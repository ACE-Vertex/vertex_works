# Vertex Works GitHub Publish Hotfix 000002

## Diagnosis

The first publisher created a valid local source commit, but GitHub `main` already contained an unrelated one-line README commit:

`f8bf34b51021de6fe6695614b1641cbe2df25762` — `Initial commit`

Because the local repository was initialized independently, a normal push cannot fast-forward that unrelated remote history.

This hotfix:

1. applies `cargo fmt` to close the rustfmt-only failure from Works refinement 000026,
2. commits that formatting change only if needed,
3. re-runs cargo fmt/test/build,
4. re-runs the source safety scan,
5. reads remote `main`,
6. uses an **exact force-with-lease** only when remote HEAD is still the known trivial Initial commit,
7. blocks if the remote changed to anything else,
8. verifies local HEAD == remote HEAD.

This is deliberately not an unconditional force push.
