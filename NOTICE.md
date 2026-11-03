# Provenance and licensing

ServiceCraft consolidates benchmark and evaluation work for the ServiceCraft
research project. Benchmark sources derive from
https://github.com/aliduabubakari/custom-pipelines; each case's `provenance.json`
retains the source revision and fixture changes. Revised references and tasks
must not be represented as unchanged upstream pipelines.

At repository creation, the upstream GitHub metadata did not declare a license.
No blanket license is inferred or assigned here. Preserve existing notices;
resolve distribution and licensing terms before a public research release.
This repository was created private. Third-party Python/Docker dependencies
remain subject to their own licenses.

Files named `private/` are experiment-operator answer/oracle fixtures. Their name
defines an evaluation access boundary; Git does not make them inaccessible to
models given repository access. Keep them outside scored generation workspaces.
