# Adding A Mode

Modes tune SemShift for a review context such as `policy`, `prompt`, `research`, `resume`, or `readme`.

To add or improve a mode:

1. Update `semshift/core/modes.py` with a clear description and focus terms.
2. Add mode-specific risk rules in `semshift/core/risk_analyzer.py`.
3. Add examples to `benchmarks/semshift_bench_v1.jsonl`.
4. Add tests that cover true positives and benign paraphrases.
5. Document the mode maturity as stable or experimental.

Keep rules conservative. A mode should surface a review queue, not make an authoritative decision.
