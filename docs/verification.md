# Verification and publication checklist

Run from the repository root with Python 3.11+:

```sh
python3 -m unittest discover -s tests -v
python3 -m ops_lab.demo > /tmp/demo-output.json
diff -u docs/demo-output.json /tmp/demo-output.json
python3 scripts/publication_scan.py
python3 -m compileall -q ops_lab tests scripts
```

The workflow matrix repeats these checks on Python 3.11 and 3.13. CI bootstraps the runner using GitHub actions; the application demonstration itself is offline. Actions are pinned to full commit identifiers and repository permissions are read-only.

## Test evidence

The initial public test suite was created before the modules; its first run failed because those modules did not exist. This is a scaffolding failure, not a claim of a meaningful behavioral red test. The implemented behavior is verified by positive and negative tests and by deterministic full-demo output.

The suite currently contains 22 tests. Scanner-specific tests prove staged and deleted historical credentials, dot-env files, non-synthetic values, binary artifacts, symlinks and runtime networking imports are rejected.

Coverage includes consent status/scope/evidence/validity, content modification after approval, suppression priority, invalid fixture addresses, duplicate planning, spacing at 119/120 seconds, daily cap, uncertain submission holds, pagination de-duplication/cycles/budgets/permission failure, fulfillment event order/replay/incomplete inputs/uncertainty, exact settlement grouping and unknown profit. The integration test denies sockets and external process creation while exercising all four real demo modules together.

No production tests were executed. No production source was imported. Six core production source/test files were hashed privately before and after public implementation; all six remained unchanged. That inventory stays outside the public repository.

## Publication gate

Only individually reviewed, newly authored source, documentation, fixtures and workflow files are staged. No archive or old Git objects are imported. A local public noreply GitHub commit identity is used. The scanner checks every non-generated working file, staged blob and reachable historical blob, including files deleted in earlier commits, and commit messages. It rejects selected credential patterns, non-synthetic email addresses, typical private home paths, IPv4 values, platform order-number patterns, binaries and symlinks in the working tree. A runtime import gate detects common networking, credential and process modules.

This is a narrow publication check, not a complete DLP engine. It cannot determine every person's identity, arbitrary secret format, external legal ownership or all dynamic code behavior. Manual full-file/diff inspection, deliberate new-file selection and exclusion of private materials are essential. Python's source is editable; these checks are evidence for this committed demo, not a sandbox guarantee for arbitrary future modifications.

Before pushing: run the complete suite and offline demo, inspect every staged diff, scan all Git history, confirm no private source was modified. After publishing: compare remote HEAD with the local commit, verify public HTTP availability, and inspect CI results for that exact commit. If any check fails, fix and reverify before declaring publication complete.

## Operational validation

This repository deploys no production service and has no production monitoring requirement. For each pushed commit, the owner should expect both Python jobs to pass and the deterministic JSON comparison and publication gate to remain green. Failure blocks a release claim; correct the public tree and rerun CI. No rollback of operational data is relevant because no live adapter exists.
