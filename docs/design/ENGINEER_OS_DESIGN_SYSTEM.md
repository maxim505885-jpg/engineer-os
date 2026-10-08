# ENGINEER OS Design System

Stage: MASTER PLAN №11.

## Product goal

ENGINEER OS is a local-first engineering cabinet. The interface must help an engineer move from source files to a traceable FINAL AUDIT without confusing model output with evidence or acceptance.

## Primary workflow

1. Sources
2. ToR / requirements
3. Evidence candidates and source review
4. Normative / calculation packets
5. Real engineering case snapshot
6. FINAL AUDIT

The UI may simplify navigation, but it must never hide or bypass upstream gates.

## Modes

### Normal mode

Default for ordinary work:
- upload/import;
- chat / CORE_PLAN / CORE_RUN;
- requirements;
- evidence;
- source review;
- normative/calculation forms;
- Stage7 case;
- FINAL AUDIT.

Low-level JSON and manual extraction actions remain hidden.

### Advanced mode

For debugging and controlled specialist workflows:
- advanced domain JSON;
- manual extraction backends;
- lower-level technical details.

Switching modes changes presentation only. It cannot change acceptance semantics.

## Status semantics

| Status family | Meaning | UI rule |
| --- | --- | --- |
| PASS / READY / ACCEPTED | positively verified state | green tone + explicit text |
| WARNING | non-blocking caution | amber tone + explicit text |
| UNCERTAINTY / UNVERIFIED / NOT_RUN / NEEDS_DATA | incomplete evidence or verification | violet/neutral caution tone + explicit text |
| BLOCK / ERROR / FAILED / REJECTED / NOT ACCEPTED | blocking or failed state | red tone + explicit text |

Color is never the only carrier of meaning. Text and reason codes remain visible.

## Tokens

CSS custom properties in `engineering/local_app/ui/styles.css` own:
- background/surface;
- text/muted;
- border;
- primary action;
- PASS/WARNING/UNCERTAINTY/BLOCK;
- focus;
- radius;
- shadow.

Product code should use tokens rather than introduce one-off colors.

## Layout

Desktop:
- persistent history/workflow sidebar;
- conversation as primary work surface;
- evidence/checks column wide enough for forms and source traces.

Tablet/mobile:
- sidebar becomes top section;
- workflow navigation scrolls horizontally;
- work surfaces stack vertically;
- no required horizontal page scroll.

Reference widths: 390, 860, 1180, 1366+ px.

## Accessibility

Required:
- visible keyboard focus;
- labels or aria-labels for controls;
- status text independent of color;
- reduced-motion support;
- no content hidden solely behind hover;
- meaningful empty/error/loading states;
- readable contrast for all status families.

## Empty/loading/error/success

Every data-heavy surface must expose the current state rather than fabricate data.

- empty: say what is missing and next action;
- loading: retain context and disable conflicting actions;
- error: show the error without losing drafts;
- success: show stored result plus verification limits.

## Engineering anti-patterns

Do not:
- show model text as evidence;
- show green merely because a model call succeeded;
- collapse BLOCK reason codes into a generic icon;
- hide FINAL AUDIT freshness/staleness;
- treat imported files as verified;
- present sample/fake metrics as real project data;
- make destructive actions look primary;
- require raw JSON in normal mode;
- use decoration that reduces table/document readability.

## Reference sources

Adapted principles from:
- `di-sukharev/vibe` (Apache-2.0): UI consistency, state handling, visual checks, accessibility discipline. No framework migration.
- `nextlevelbuilder/ui-ux-pro-max-skill` (MIT): design-system reasoning, anti-patterns, responsive/accessibility checklist.

These repositories are references, not runtime dependencies.

## Stage11 acceptance

Stage11 can close only when:
- core workflow is visible without raw JSON;
- normal/advanced modes work;
- semantic statuses preserve text and fail-closed meaning;
- desktop/mobile Chromium smoke passes;
- static design-system guard passes;
- existing Python/DOM regressions remain green.
