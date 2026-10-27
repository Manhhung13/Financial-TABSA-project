# ADR-0003: Frozen grouped and chronological evaluation
Status: accepted.
Context: Same article can yield many target/aspect records; translated and republished stories can also overlap across corpora.
Decision: split documents/events chronologically prior to expansion, quarantine Gold test, exclude test overlaps from all adaptation/weak-label pools; fixed same test for ablations.
Consequences: fewer independent samples but meaningful quality claims. Never choose checkpoints or tuning based on Gold test.
