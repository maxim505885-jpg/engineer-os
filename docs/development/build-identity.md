# Build identity and safe local reuse

The local server and worker share a startup build record. Authenticated `/api/build`
and `/api/status.build` expose version, Git tree claim, profile, data schema version,
source/manifest digests and artifact-integrity status. Worker terminal results carry
`runtime_build`; UI displays the same build metadata. The data-directory identity
is a path digest, not its contents and not a portable database identity.

A new manifest is generated only from an explicit version/profile and known clean
Git tree by `scripts/build_release_manifest.py --output <new-path> --version <version>`.
The explicit `--allow-dirty` option produces a non-qualified development manifest.
Set `ENGINEER_OS_BUILD_MANIFEST` to its path. No manifest permits development mode,
with `artifact_verified=false`; real launcher captures actual runtime file digests.
Code inventory excludes data, caches and tests, has byte/file limits and rejects
links. Source/manifest drift observed by the guard remains invalid until restart,
even if the file is subsequently restored. This does not attest process memory,
external dependencies, publisher identity, stable-release readiness or engineering
acceptance; these require their separate qualification gates.

The Windows supervisor checks source/profile/manifest and selected data-directory
identity before reusing a listener. Missing legacy API or a mismatch gives BLOCK
and leaves that instance running. Choose another port or explicitly stop the owner.
Build checks use loopback-only, bounded requests with redirects/proxies disabled;
the app token is never included in output. No user server is replaced automatically.
