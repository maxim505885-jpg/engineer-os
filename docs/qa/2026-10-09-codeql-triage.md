# CodeQL source-to-sink triage — PR91 / 90263af

Reviewed commit: `90263af601e8c491352f46d0a02b7196eeaf2bc1`.
Analysis ref: `refs/pull/91/head`; aggregate check113609776255 reported29 high alerts.
All29 full alert details were fetched individually. This is a disposition of the
specified queries, not a claim of complete security or an engineering acceptance.

## Trust boundary and inputs

The application is a single-owner loopback desktop service. Recovery POSTs require
the session token, exact Host, same Origin when supplied, and no cross-site fetch.
Normal application mode refuses data operations. Maintenance mode serializes them.
`server.py:48/58` are bounded body/JSON reads;65/66/68 are request-path dispatch
and authorization. Recovery accepts an absolute archive/target chosen by the owner;
the selection-file path is fixed by the server, not taken from the JSON request.
The owner can back up/select/restore a project outside the checkout by design.
Restricting these paths to the repository would break the desktop contract.

Supported storage is a directory controlled by this OS user, without an adversary
able to concurrently replace entries. Archive contents are still untrusted:
bounded inventory, allowed paths, no links, hashes, SQLite checks and original
bindings are validated independently. Existing outputs are not replaced. Managed
database/sidecars/key/settings/lock leaves reject symbolic/hard/broken links.

## Individual dispositions

For every path row, source is the authenticated owner recovery input described
above (CodeQL sometimes includes dispatch as implicit-flow sources). FP means
false positive for uncontrolled path traversal under this stated contract.

| Alert | Sink at reviewed commit | Actual flow and control | Disposition |
|---|---|---|---|
|3|backup.py74 root.resolve|Server active root or explicitly selected project; canonicalization only.|FP|
|5|backup.py90 output.parent.mkdir|Owner-selected new archive outside canonical project root; existing/link output denied.|FP|
|6|backup.py91 TemporaryDirectory|Private random workspace under chosen archive parent; no archive member names used.|FP|
|7|backup.py141 os.link source|Source is completed, independently verified temporary archive; exclusive publication.|FP|
|8|backup.py142 output.stat|Chosen archive just exclusively published; metadata only.|FP|
|9|backup.py205 target.exists|Owner-selected absent restore directory; metadata check.|FP|
|10|backup.py205 target.is_symlink|Reject link destination; metadata check.|FP|
|11|backup.py206 parent.mkdir|Intentional owner-selected restore parent, canonicalized; no ZIP entry used.|FP|
|12|backup.py208 TemporaryDirectory|Private random staging directory under chosen parent; extraction validates each member.|FP|
|13|backup.py224 target.exists|Second no-replace guard before atomic publication; metadata only.|FP|
|15|settings.py25 path.exists|Fixed settings.json under selected project; managed_file already rejects leaf links.|FP|
|16|settings.py26 path.stat|Fixed settings.json, bounded size and managed leaf; metadata only.|FP|
|17|settings.py27 path.read_text|Fixed settings.json, size bound and five-key settings validation; selected project is intentional.|FP|
|18|settings.py78 selection.is_symlink|Fixed server selection path, rejects links/selection inside project; not owner-supplied filename.|FP|
|21|store.py44 target.exists|Fixed history.pre-migration-v0.sqlite3 under selected root; leaf validated and content compared.|FP|
|22|store.py45 mkstemp|Random migration snapshot in selected project; exclusive creation.|FP|
|23|store.py52 os.link source|Source is validated private migration snapshot matching current SQLite dump.|FP|
|24|store.py52 os.link target|Fixed managed recovery-copy leaf, exclusive publication; existing copy verified.|FP|
|25|store.py53 temporary.unlink|Deletes only application-created temporary migration file in owner-controlled directory.|FP|
|26|store.py72 root.resolve|Explicitly selected project canonicalization; arbitrary project locations supported.|FP|
|27|store.py72 root.mkdir|Initial project directory or selected root; intentional owner operation.|FP|
|28|store.py74 path.exists|Fixed history.sqlite3 metadata; connection validates leaf and all SQLite sidecars before open.|FP|
|29|backup.py222 settings.write_text|Source backup.py44 non_secret_config; validated by settings.validate before extraction/write. API keys excluded; credential/query URLs rejected. Writes only staging settings.json.|FP|
|30|backup.py86 output.parent.resolve|Canonicalizes chosen archive parent before outside-project check; prevents alias containment bypass.|FP|
|31|backup.py89 output.exists|Chosen new archive metadata; overwrite refused.|FP|
|32|backup.py89 output.is_symlink|Rejects archive destination links including broken links.|FP|
|33|backup.py204 target.parent.resolve|Canonicalizes chosen restore parent before absent-target validation; metadata only.|FP|
|34|lock.py14 path.lstat|Protective inspection of managed leaf; rejects links, hardlinks and nonregular files; no content access.|FP|
|35|settings.py79 selection.parent.resolve|Canonicalizes server-owned selection parent before atomic write; not JSON-selected filename.|FP|

## Verification and remaining scope

Existing focused recovery/link/backup/UI tests were rerun for this triage. They
cover unchanged external files after rejected link attacks, owner directory aliases,
two archive formats, corrupted/path-traversal archives, migration and no-replace.
Prior independent follow-up review also sent real HTTP missing-token/bad-Host/
bad-Origin/cross-site requests: all403, no archive produced.

Each alert is dismissed individually as false positive with its reviewed sink and
contract recorded here. No query is disabled and no CodeQL workflow is suppressed.
Check the resulting aggregate check and current PR head before merging.

Pre-open filesystem checks do not defend against another process with permission
to swap entries concurrently. Windows ACL/confidentiality is not established by
Linux tests. Backup currently intentionally carries the issuer key in an unencrypted
owner archive; protect it like the original project data. Alert29 concerns settings,
not that archive key. These limits remain in release gates; no FINAL RELEASE AUDIT.
