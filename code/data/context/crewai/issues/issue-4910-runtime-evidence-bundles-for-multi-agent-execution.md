# Runtime evidence bundles for multi-agent execution

**Issue #4910** | State: open | Created: 2026-03-16 | Updated: 2026-03-18
**Author:** joy7758

Hi CrewAI team,

We have been experimenting with packaging multi-agent execution runs into verifiable evidence bundles.

The idea is similar to tamper-evident logs but specialized for autonomous agent runtimes.

Implementation:
https://github.com/joy7758/agent-evidence

Artifact:
https://doi.org/10.5281/zenodo.19055948

The system exports:

agent run → evidence bundle → offline verification → tamper detection

This might be useful for:

- agent governance
- execution audit
- reproducibility of agent workflows

Curious if CrewAI would benefit from an optional runtime evidence export layer for multi-agent pipelines.
