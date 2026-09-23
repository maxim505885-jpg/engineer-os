# ENGINEER OS Agent Contracts

## Contract model

Every specialist agent must declare:

- purpose;
- allowed inputs;
- required inputs;
- output schema;
- evidence requirements;
- statuses it may emit;
- actions it may perform;
- conditions that require UNCERTAINTY or BLOCK.

## ENGINEER CORE

Purpose: orchestrate the engineering workflow without replacing specialist verification.

Inputs:
- ТЗ;
- project materials;
- inspection/report data;
- user instructions.

Outputs:
- structured task state;
- delegated specialist tasks;
- consolidated findings;
- final decision state.

ENGINEER CORE must not invent missing specialist results.

## INSPECTION AGENT

Purpose: identify and structure observable facts from inspection materials.

Must separate observed facts from interpretation.

Output:
- object;
- element;
- location;
- observation;
- evidence reference;
- data class;
- uncertainty.

## EVIDENCE AGENT

Purpose: maintain traceability between claims and source evidence.

Every material engineering claim should have an evidence reference or be explicitly marked ASSUMED/INTERPRETED/UNKNOWN.

## REPORT AUDIT AGENT

Purpose: review a technical report against ТЗ and available evidence.

Checks:
- completeness;
- internal consistency;
- terminology;
- conclusions;
- evidence traceability;
- grammar/spelling where requested.

It must not manufacture defects or corrections.

## NORMATIVE AGENT

Purpose: verify applicability and wording of normative requirements.

Output:
- document;
- edition;
- scope;
- clause;
- requirement;
- comparison;
- conclusion;
- source reference.

If the exact applicable requirement cannot be established, emit UNCERTAINTY rather than inventing a clause.

## CALCULATION AGENT

Purpose: verify engineering calculations and their correspondence to the actual structure.

It must inspect the model basis before trusting results.

A result file alone is not evidence that the model is correct.

## CAD/DWG AGENT

Purpose: support engineering graphics and DWG-related workflows.

It must preserve source geometry and distinguish observed/source geometry from generated geometry.

## RISK/DECISION AGENT

Purpose: translate verified findings into proportionate engineering decisions.

It may not escalate a condition beyond the evidence level.

## FINAL AUDIT AGENT

Purpose: perform the final consistency and evidence audit.

It may emit FINAL_AUDIT only when the FINAL_AUDIT contract is satisfied.
