# Measurement definitions

Version: `servicecraft.raw-static@1`. This protocol reports individual raw and
scaled measurements, with no custom weighting or overall static-quality index.

## Population and denominators

Analyze every `.py` file in the supplied candidate snapshot. Count physical source
lines using Python `str.splitlines()`, including comments and blank lines. Findings
are mapped to a `(source file, line number)` pair. Multiple messages on the same
line contribute once to that tool's fraction. Pairs outside the source population,
including module-level messages at line zero, are excluded from line fractions;
all messages remain in raw counts. The denominator is shared across the three
line-based measurements. An empty denominator uses 1 to avoid division by zero;
submission validation separately requires Python source files.

For each tool, `scaled_metrics` records `value`, `direction`, and `formula`.
Fractions are already in [0,1] and lower values indicate fewer flagged lines.
They describe finding prevalence; they are not probabilities of correctness.

## Flake8, Pylint and Bandit

For each tool, use:

```text
distinct source lines with findings / total physical Python source lines
```

Raw output retains total findings. Flake8 also reports findings per 100 lines;
Pylint retains counts by native message type; Bandit retains counts by severity.
There are no multipliers for errors, warnings or severity. Pylint's native rating
is not used because it combines message categories using the tool's own formula.

Flake8 runs with `--isolated`, Pylint with an evaluator-selected empty rcfile,
and Bandit with `--ignore-nosec`. Tool versions are fixed inside the runtime image.

## Radon

Preserve the native cyclomatic complexity of every analyzed block through block
count, mean CC and maximum CC. Complexity has no natural fixed upper bound, so
do not invent a 0–1 quality threshold or fit a minimum/maximum to experimental
results. No blocks produces unavailable mean/max CC, rather than an invented zero.

Radon's native maintainability index is bounded in [0,100]. Record MI per file and
scale each value by division by 100. The scaled project MI is the arithmetic mean
of native file MI values divided by 100. All files have equal contribution; per-file
values remain available. Higher values indicate a higher native MI. Radon's own
definition is unchanged; ServiceCraft adds no custom weights to it. Multi-line
strings count as comments in the native MI calculation (`multi=True`).

## Failure and availability

Syntax validity is binary and independent of lint findings. Missing analysis tools
and tool execution errors have unavailable metrics, not a default score. They
make the evaluation an infrastructure error unless invalid candidate syntax has
already caused the static stage to fail. Lint and security findings do not block
runtime by a numerical cutoff. The binary outcome uses the six stage verdicts.

The earlier prototype's weighted diagnostics, custom complexity thresholds and
diagnostic mean are superseded. Results must be grouped by measurement version;
old numeric diagnostics must not be pooled with these fractions.
