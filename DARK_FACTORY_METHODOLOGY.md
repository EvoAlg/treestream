# Dark Factory (DF) Methodology

Version: v2.3
Status: Draft
Primary audience: AI model instances, human practitioners
Note: Tool-agnostic. For tool assignments see DF_CONFIG.md (project-specific).

Change log from v2.2:
- Added governance hierarchy (§3a) — three-level file taxonomy explicit
- Updated DF_CONFIG.md definition (§2) — human-only, governance level
- Updated §8.1 document precedence — AGENT_RULES.md and DF_CONFIG.md at same governance level
- Added DF_CONFIG.md to Human-only actions (§8.4)
- Updated Appendix A to reflect current TreeStream state

---

## 1. What Dark Factory Is

Dark Factory (DF) is a methodology for AI-assisted software development that orchestrates multiple AI models in defined, non-overlapping roles to produce higher-quality outputs than any single model generates alone.

The core thesis: AI will increasingly handle implementation. The human role shifts to specification, oversight, and role governance — not syntax.

DF is not a tool. It is a workflow discipline.

Key principle: independent verification layers are non-negotiable. Single-model workflows miss failure modes that multi-model workflows surface. Adversarial audit framing produces better verification than confirmation-biased prompts.

---

## 2. Defined Terms

| Term | Definition |
|------|------------|
| Human | The person governing the DF workflow. Only authorised party for commits, destructive actions, and final governance calls. |
| Spec Agent | AI model instance responsible for translating human intent into repo structure and maintaining spec artifacts. |
| Implementation Agent | AI model instance responsible for implementing software against a locked spec. |
| Adversarial Auditor | AI model instance responsible for independent verification of spec precision, implementation conformance, fixture correctness, and governance integrity. Must be a different model instance — preferably a different model family — from the Spec Agent and Implementation Agent. |
| SPEC.md | AI-readable, precise, deterministic specification of system behaviour. Primary input to the Implementation Agent. Single source of truth — governs over all derived artifacts in case of conflict. |
| SPEC Locked | A SPEC.md is locked when the Human has formally declared it stable. Locked status is recorded by a `LOCKED: true` header field in SPEC.md and a corresponding commit. No agent may modify a locked SPEC.md. A locked SPEC.md may only be modified via the Unlock Protocol (see §5.4). |
| Unlock Declaration | A formal Human action that reverts a locked SPEC.md to DRAFT status, halts Phase 3, and initiates the Spec Mutation Protocol (see §5.4). Must include stated reason. |
| Material Gap | A gap, ambiguity, or contradiction in SPEC.md that would cause a compliant Implementation Agent to produce behaviour that fails user intent, violates a stated constraint, or cannot be deterministically resolved from the spec text alone. Formatting suggestions, stylistic preferences, and implementation hints that do not affect observable behaviour are not material gaps. |
| PRD | Product Requirements Document. Human-readable, intent-first, may include images and UI mockups. Precedes and informs SPEC.md for projects with user-facing interfaces or non-trivial user stories. |
| SOP | Standard Operating Procedure. Documents the existing human workflow that software may automate or augment. Upstream of PRD in process-automation projects. Primary source for human-authored scenarios. |
| Scenario | A human-authored, end-to-end description of expected system behaviour from a user perspective. Written before implementation. Held outside the Implementation Agent's access. Default storage model is Model A (out-of-repo) unless DF_CONFIG.md explicitly records Model B. Format is domain-dependent (see §6). |
| Auditor Bootstrap | The procedure for instantiating the Adversarial Auditor on a first project before DF_CONFIG.md and AGENT_RULES.md exist. See §5.1 for the bootstrap procedure. |
| Fixture | A static, deterministic input/output data pair used to validate implementation behaviour against the spec. Created by Spec Agent. Human-only deletion rights. Read-only for Implementation Agent. Must be validated by Adversarial Auditor before Phase 3 begins. |
| Satisfaction | Probabilistic metric: across all observed trajectories through all scenarios, what fraction satisfy the user's intent? Evaluated by the Adversarial Auditor, not the Implementation Agent. Threshold defined per project in ACCEPTANCE_CRITERIA.md. |
| AGENT_RULES.md | Governance document defining role boundaries, access permissions, and escalation rules for a specific project instance. Modified by Human only. May narrow but not widen permissions defined in this methodology document. |
| DF_CONFIG.md | Project-specific document mapping DF roles to specific tools and models, and recording the chosen scenario storage model. Sits at the same governance level as AGENT_RULES.md. Human-only — no agent may modify it. Cannot modify role boundaries or permissions defined in AGENT_RULES.md. |
| Template Repo | Canonical repository structure that Spec Agent references when scaffolding a new DF project. Once built, supersedes §10 of this document as the authoritative scaffolding reference. Prior to Template Repo existence, §10 of this document serves as the scaffolding reference. |
| Authorship Metadata | Record of whether each artifact was authored by a human or which AI agent. Required for assessing verification independence. |

---

## 3. Artifact Hierarchy

For process-automation projects, the full hierarchy is:

```
SOP
  (documents existing human workflow; source of human-authored scenarios)
  ↓ informs
PRD
  (human-readable intent; UI mockups; stakeholder language)
  ↓ derives
SPEC.md
  (AI-readable; precise; deterministic; no ambiguity; single source of truth)
  ↓ drives
Implementation
```

For pure software projects without an existing human workflow, SOP may be omitted. PRD may be omitted for CLI tools or narrow-scope utilities with no UI, but the tradeoff is a SPEC.md that risks being implementation-biased rather than user-intent-biased.

---

## 3a. Governance Hierarchy and File Taxonomy

### Governance Hierarchy

Every DF project has three governance levels. Files at a higher level govern over files at a lower level.

```
Level 1 — Methodology
  DARK_FACTORY_METHODOLOGY.md
  Defines the DF workflow, role definitions, governance principles, and
  phase model. Applies to all DF projects. Human-authored only.

Level 2 — Project Governance
  AGENT_RULES.md + DF_CONFIG.md (side by side — neither supersedes the other)
  AGENT_RULES.md: defines what each role may do
  DF_CONFIG.md: defines which tool/model fills each role
  Both are human-only. No agent may modify either.

Level 3 — Project Specification
  SPEC.md, SCENARIOS.feature, ACCEPTANCE_CRITERIA.md
  Define what the software does. Governed by Level 2.
  Spec Agent may author under human instruction.

Level 4 — Implementation
  Implementation files, tests, fixtures, build artifacts.
  Governed by Levels 2 and 3.
```

### File Taxonomy

Every file in a DF project is one of three types:

**Type 1 — General location, general content**
Same filename, same content across every DF project. No project-specific information. Examples: `AGENT.md` (agent entry point), `AGENT_RULES.md` template. An agent reading these learns how DF works, not what this specific project does.

**Type 2 — General location, specific content**
Same filename and location in every DF project, but content is project-specific. Examples: `SPEC.md`, `DF_CONFIG.md`, `ACCEPTANCE_CRITERIA.md`, `SCENARIOS/`. An agent knows where to find these across any DF repo; what is inside is unique to the project.

**Type 3 — Specific location and content**
Implementation files, fixtures, build artifacts. Vary by project in both location and content. Not part of the methodology governance layer.

Note: `AGENT.md` (or equivalent agent entry point file) is a Type 1 file — it should contain no project-specific content. It points to Type 2 files by their standard locations. The agent gets project specifics from Type 2 files, not from the entry point.

---

## 4. Role Structure

### 4.1 Human

Responsibilities:
- Author SOP (where applicable), PRD (where applicable), and SPEC.md
- Author or approve Scenarios
- Approve all commits
- Govern role violations
- Perform manual end-to-end testing
- Sole authority to modify AGENT_RULES.md
- Sole authority to delete fixtures and scenarios
- Sole authority to issue Unlock Declarations

Boundaries:
- Does not write implementation code
- Does not modify implementation files directly

### 4.2 Spec Agent

Responsibilities:
- Translate SPEC.md intent into repo structure: fixtures, ACCEPTANCE_CRITERIA.md, archive management, test stubs
- Bump spec versions (archive-before-bump rule applies to spec artifacts only — see access note below)
- Regenerate affected fixtures and ACCEPTANCE_CRITERIA.md on every spec version bump
- Reference Template Repo (or §10 if Template Repo not yet built) for consistent project structure
- Record authorship metadata on all artifacts created

Access:
- Write access to fixtures/ (create and update only; deletion is Human-only)
- Write access to tests/ (stubs only; test logic implementation belongs to Implementation Agent)
- Write access to ACCEPTANCE_CRITERIA.md
- Write access to archive/ for spec artifacts (SPEC.md versions, AGENT_RULES.md versions, ACCEPTANCE_CRITERIA.md versions)
- Read-only access to implementation files
- No access to Scenarios storage location

Boundaries:
- Cannot modify AGENT_RULES.md
- Cannot modify SPEC.md content (version bumps and header field updates only, and only after Human approval)
- Must archive spec artifacts before any version bump
- Implementation file archiving during Spec Mutation Protocol (§5.4) is performed by the Human, not the Spec Agent
- Must halt and escalate at Tier 4A on genuine spec interpretation decisions (see §7)

### 4.3 Implementation Agent

Responsibilities:
- Implement against locked SPEC.md
- Complete test stubs created by Spec Agent
- Run test suite against fixtures
- Report results with pass/fail per fixture

Access:
- Read-only access to SPEC.md, tests/, and fixtures/
- Read-only access to AGENT_RULES.md (reference only — to understand applicable role boundaries and exclusions)
- Write access to implementation source files and build artifacts only
- No access to Scenarios storage location

Boundaries:
- Cannot modify SPEC.md, AGENT_RULES.md, or fixtures
- Cannot modify test assertion logic or weaken test assertions when completing stubs — test stubs define the pass criteria and must be completed faithfully to the intent of the stub, not to the convenience of the implementation
- Must halt and flag at Tier 4A on spec interpretation decisions — must not assume
- For all other decisions must apply tiered escalation model (see §7)

### 4.4 Adversarial Auditor

Responsibilities:
- Independent verification of SPEC.md precision and internal consistency
- Independent verification of implementation conformance against SPEC.md
- Fixture validation: verify each fixture faithfully represents the behaviour specified in SPEC.md and has not been incorrectly derived by the Spec Agent
- Scenario evaluation: assess whether implementation satisfies human-authored scenarios
- Surface spec gaps, regressions, and governance violations
- Return structured findings only — must not include scenario content in findings returned to the Human when the Implementation Agent may see them
- Verify authorship metadata completeness on all artifacts

Access:
- Read access to SPEC.md (all versions including archived)
- Read access to Scenarios (full access via agreed storage model)
- Read access to fixtures/
- Read access to test results and implementation outputs
- Read access to AGENT_RULES.md and DF_CONFIG.md
- Read access to authorship metadata
- No access to implementation source files (preserves independence of behavioural assessment)

Boundaries:
- Does not author implementation code
- Does not modify SPEC.md, AGENT_RULES.md, fixtures, or scenarios
- Must approach every audit with adversarial framing: assume failure modes exist and find evidence of them
- Must be a separate model instance from Spec Agent and Implementation Agent
- Preferably a different model family to maximise blind-spot independence (see §8.2)

---

## 5. Workflow Phases

### Phase 1 — Specification

#### Auditor Bootstrap (first project only)
On a first DF project, DF_CONFIG.md and AGENT_RULES.md do not yet exist. The Human must instantiate the Adversarial Auditor directly using the following bootstrap procedure before Phase 1 step 5:

1. Human selects the Auditor model instance manually — preferably a different model family from the intended Spec Agent and Implementation Agent
2. Human primes the Auditor with this methodology document and the project SPEC.md
3. Human records the selected Auditor model in a pre-scaffolding note (committed alongside the initial SPEC.md)
4. This selection is later formalised in DF_CONFIG.md when Spec Agent scaffolds the repo in Phase 2

On subsequent projects, DF_CONFIG.md from the Template Repo provides the Auditor assignment before Phase 1 begins.

1. Human authors SOP (if applicable)
2. Human authors PRD (if applicable)
3. Human authors SPEC.md derived from PRD/SOP
4. Human stores Scenarios using default Model A (out-of-repo) unless DF_CONFIG.md already exists and specifies Model B
5. Adversarial Auditor reviews SPEC.md for material gaps, ambiguities, and regressions
6. Human resolves all flagged material gaps
7. Repeat steps 5–6 until Adversarial Auditor finds no material gaps (see §2 for definition of material gap)
8. Human declares SPEC locked (records `LOCKED: true` in SPEC.md header; commits with tag `spec-locked-vX.X.X`)

### Phase 2 — Transition Gate

Spec Agent scaffolds repo from locked SPEC.md:
- Directory structure per Template Repo (or §10 if Template Repo not yet built)
- AGENT_RULES.md (populated from template)
- ACCEPTANCE_CRITERIA.md
- fixtures/ (all gates)
- tests/ stubs
- Authorship metadata recorded on all artifacts

Adversarial Auditor validates scaffolded artifacts:
- Verifies fixtures correctly represent SPEC.md behaviour
- Verifies ACCEPTANCE_CRITERIA.md is consistent with SPEC.md
- Returns structured findings to Human

Human reviews Adversarial Auditor findings and scaffolded repo. Human must confirm Phase 2 complete before Phase 3 begins.

### Phase 3 — Implementation

1. Implementation Agent implements against locked SPEC.md
2. Implementation Agent completes test stubs and runs test suite; reports results
3. Adversarial Auditor evaluates results against Scenarios (see §6.3)
4. Adversarial Auditor returns structured findings to Human
5. Human decides: accept, patch spec (triggers Spec Mutation Protocol — see §5.4), or re-implement
6. Repeat until Satisfaction threshold met (threshold defined in ACCEPTANCE_CRITERIA.md)

### Phase 3 Exit

Human issues final acceptance. Implementation is committed. Project moves to maintenance or next iteration.

### 5.4 Spec Mutation Protocol (Post-Lock)

A locked SPEC.md must not be modified without following this protocol. This protocol applies whenever a Tier 4A escalation, Adversarial Auditor finding, or Human decision requires changing a locked SPEC.md.

1. Human issues Unlock Declaration (states reason; records in commit message)
2. SPEC.md status changes from LOCKED to DRAFT (update header field)
3. All Phase 3 work halts immediately
4. Human archives current implementation state (Spec Agent cannot perform this step — implementation files are read-only for Spec Agent)
5. Human applies required changes to SPEC.md
6. Adversarial Auditor reviews changes (full Phase 1 audit or targeted audit of changed sections at Human's discretion)
7. Human re-locks SPEC.md
8. Spec Agent regenerates all affected fixtures and ACCEPTANCE_CRITERIA.md
9. Adversarial Auditor validates regenerated fixtures (Phase 2 fixture validation step repeated for affected fixtures)
10. Human confirms Phase 2 complete; Phase 3 resumes from clean state

---

## 6. Scenarios

### 6.1 Purpose

Scenarios are the primary mechanism for validating that implementation satisfies user intent rather than merely passing fixtures. Fixtures are deterministic and machine-checked. Scenarios are probabilistic and evaluator-checked.

Scenarios describe expected behaviour from a user perspective. They are not implementation descriptions. They are authored before implementation begins.

### 6.2 Format

Scenarios do not require Gherkin or any structured syntax. Format is domain-dependent:

| Project type | Recommended scenario format |
|---|---|
| CLI tool | Plain English step-by-step user narrative |
| UI application | Annotated screenshots or Figma exports + plain English behavioural assertions |
| Process automation | Derived from SOP steps; plain English with exception cases explicit |
| Data pipeline | Input/output examples with edge cases stated |

If the Implementation Agent has no access to Scenarios (see §6.3), machine-parseable syntax is not required. The Adversarial Auditor (a model) evaluates against plain English and images directly.

For UI projects, Figma is the recommended human scenario authoring tool. Annotated interaction flows exported as images embedded in a markdown scenario file are valid and evaluable.

### 6.3 Access Controls — Holdout Principle

Scenarios must be held outside the Implementation Agent's access. This is the primary anti-gaming control.

Rationale: an Implementation Agent with access to scenarios can optimise against them rather than against the underlying user intent. This is the DF equivalent of a machine learning model overfitting to a test set.

**Default storage model: Model A applies unless explicitly overridden.**

Two valid storage models. The default is Model A. Model B may only be used if DF_CONFIG.md explicitly records it and the environment conditions for Model B are met.

**Model A — Out-of-repo storage (default)**
Scenarios stored in a separate private repository or file system location entirely outside the Implementation Agent's workspace. Required in environments where workspace files are automatically indexed for retrieval (RAG-enabled LLM interfaces). In such environments, Model A is mandatory regardless of DF_CONFIG.md settings.

**Model B — In-repo excluded directory**
Scenarios stored in a `scenarios/` directory within the repo, with explicit exclusion in AGENT_RULES.md. Valid only in environments where the Implementation Agent's context is strictly bounded to explicitly provided files and no automatic workspace indexing occurs. Must be explicitly recorded in DF_CONFIG.md.

Technical isolation requirement: rule-based exclusion alone (AGENT_RULES.md) is insufficient in RAG-enabled environments. If there is any doubt about whether the Implementation Agent's workspace is automatically indexed, Model A must be used.

Evaluation proxy:
- Adversarial Auditor reads scenarios via agreed storage model
- Adversarial Auditor evaluates implementation output against scenarios
- Returns structured findings only
- Findings must not include scenario content, paraphrases of scenario steps, category labels derived from scenario structure, or any information that would allow the Implementation Agent to infer scenario content

### 6.4 Authorship

Scenarios should be human-authored wherever possible. AI-assisted scenario authoring is permitted but must be recorded in authorship metadata. Scenarios authored by the same model as the Spec Agent or Implementation Agent weaken the independence of the verification layer and require compensating cross-model review.

---

## 7. Escalation Model

The following tiered model applies to Spec Agent and Implementation Agent. Adversarial Auditor applies Tier 4B only; audit findings are not escalations — they are outputs.

| Tier | Condition | Action |
|---|---|---|
| 1 | Implementation or scaffolding choice with no spec dependency | Decide independently; proceed |
| 2 | Test failure with clear cause | Fix and re-run; report outcome |
| 3 | Tooling or environment issue | Attempt standard resolution; document if unresolved; escalate to Human only if unresolvable after documented attempts |
| 4A | Spec ambiguity affecting implementation or scaffolding decision | Halt; flag to Human with specific ambiguity stated and section reference |
| 4B | Governance rule conflict | Halt; flag to Human with specific conflict stated and sections in conflict |

Tier 4A and Tier 4B are the only conditions requiring a halt. All other conditions must be worked through independently before escalating.

Mixed cases: if a tooling issue (Tier 3) cannot be resolved and the resolution path implicates a spec interpretation decision, escalate as Tier 4A, not Tier 3.

Frequent Tier 4A escalations signal upstream spec gaps that should be addressed in SPEC.md, not resolved ad hoc. Frequent Tier 4B escalations signal governance gaps in AGENT_RULES.md.

---

## 8. Governance

### 8.1 AGENT_RULES.md, DF_CONFIG.md, and Document Precedence

AGENT_RULES.md defines role boundaries, access permissions, and escalation rules for a specific project instance. It is modified by Human only.

DF_CONFIG.md defines which tools and models fill each DF role for a specific project instance. It is modified by Human only.

These two documents sit at the same governance level (Level 2). Neither supersedes the other — they serve different purposes:
- AGENT_RULES.md answers: what may each role do?
- DF_CONFIG.md answers: which tool/model fills each role?

If a conflict arises between them, the Human must resolve it. No agent may interpret its way past a conflict between Level 2 documents.

Document precedence — in any conflict between governance documents, the following order applies:

1. This methodology document (Level 1 — highest authority)
2. AGENT_RULES.md and DF_CONFIG.md (Level 2 — project governance; neither supersedes the other; both may narrow but not widen methodology permissions)
3. SPEC.md, SCENARIOS.feature, ACCEPTANCE_CRITERIA.md (Level 3 — project specification)
4. All other files (Level 4 — implementation)

An AGENT_RULES.md or DF_CONFIG.md that conflicts with this methodology document is invalid and must be corrected by the Human.

Target state: a version of AGENT_RULES.md stable enough to apply across any DF project with only a DF_CONFIG.md overlay. Frequent modifications signal governance gaps upstream.

### 8.2 Model Diversity

The Adversarial Auditor must be a separate model instance from the Spec Agent and Implementation Agent. Where possible, it should be a different model family.

Rationale: models share training data biases and failure modes within a family. An auditor from the same family as the model being audited may share the same blind spots. Cross-family verification is more likely to surface issues that survive same-family review.

Same-model multi-agent setups are permitted but require compensating controls: stronger adversarial prompt framing for the audit pass, and explicit recording in authorship metadata that blind-spot independence is weakened.

### 8.3 Authorship Metadata

Every artifact must record its author:

```
# Author: [Human | Spec Agent | Implementation Agent | Adversarial Auditor]
# Model: [model name and version if AI-authored]
# Date: [ISO date]
# Version: [artifact version]
```

Authorship metadata completeness is verified by the Adversarial Auditor as part of every audit pass.

Authorship metadata enables:
- Assessment of verification independence
- Detection of shared blind-spot risk
- Audit trail for governance review

### 8.4 Human-Only Actions

The following actions are Human-only and must never be delegated to an agent:

- Commits to the repository
- Deletion of fixtures
- Deletion or modification of Scenarios
- Modification of AGENT_RULES.md
- Modification of DF_CONFIG.md
- Declaration of SPEC locked
- Issuance of Unlock Declarations
- Final acceptance of implementation
- Branch creation and merge conflict resolution
- Dependency version upgrades that affect externally observable behaviour
- Secrets and environment configuration
- Test baseline regeneration
- Authorship metadata correction

---

## 9. Validation Approach

### 9.1 Fixtures

Fixtures are deterministic. Each fixture is a known input/output pair. Test suite pass/fail against fixtures is binary. Fixtures are created by the Spec Agent and are read-only for the Implementation Agent.

Fixture validation is the responsibility of the Adversarial Auditor. Fixture validation must occur during Phase 2 review before Phase 3 begins. A fixture that does not accurately represent SPEC.md behaviour is a governance violation equivalent to a spec gap and must be corrected before Phase 3 proceeds.

Fixture authorship must be recorded in authorship metadata.

### 9.2 Scenarios and Satisfaction

Scenarios are probabilistic. Satisfaction is the fraction of observed user trajectories through all scenarios that the implementation correctly handles. Evaluated by the Adversarial Auditor, not the Implementation Agent.

Satisfaction threshold for acceptance is defined per project in ACCEPTANCE_CRITERIA.md. Where no threshold is specified, a default of 80% is applied.

### 9.3 Relationship Between Fixtures and Scenarios

Fixtures operationalise scenario intent at the deterministic level. A scenario without a fixture is unverified prose. A fixture without a scenario is a test case without a stated user rationale.

Both are required for a complete validation picture. No role is currently assigned to formally verify scenario-fixture completeness pairing before Phase 3 — this is an open item for Round 2.

### 9.4 Artifact Precedence

SPEC.md is the single source of truth. In any conflict between SPEC.md and generated artifacts (fixtures, ACCEPTANCE_CRITERIA.md, test stubs), SPEC.md governs. Agents must not treat fixture behaviour or acceptance criteria as normative if they conflict with SPEC.md. Such conflicts must be flagged as Tier 4A escalations.

---

## 10. Template Repo

The Template Repo is a canonical repository structure that the Spec Agent references when scaffolding a new DF project. Once built, it supersedes this section as the authoritative scaffolding reference.

Prior to Template Repo existence: Spec Agent uses the directory structure and artifact list below as the scaffolding reference. This is a bootstrap fallback, not a permanent state.

Required contents:
- Canonical directory structure
- AGENT_RULES.md template (role boundaries, access permissions, escalation tiers)
- ACCEPTANCE_CRITERIA.md template (including default satisfaction threshold)
- Fixture directory structure with authorship metadata placeholders
- DF_CONFIG.md template (tool and model assignments per role; scenario storage model selection)
- Scenario storage model guidance (Model A vs Model B per §6.3)
- README explaining DF workflow for new model instances

Status: not yet built. Identified as highest-leverage unbuilt DF artifact. Building the Template Repo is the recommended first DF project after this methodology document is stable.

---

## 11. Key Failure Modes (Round 1 Learnings)

| Failure mode | Description | Mitigation |
|---|---|---|
| Spec gap produces compliant but wrong implementation | Ambiguous spec language allows technically correct implementation that fails user intent | Adversarial audit of SPEC.md before locking; precise, unambiguous language required |
| Context window degradation | Long agent sessions produce silent quality degradation as earlier context is lost | Context sentinels: periodic explicit re-statement of current spec version and open items |
| Agent gaming test suite | Implementation Agent optimises against visible fixtures rather than underlying intent | Scenario holdout principle: scenarios held outside Implementation Agent access |
| Shared blind spot | Same model family auditing its own outputs misses systematic failure modes | Model diversity in verification layer; cross-family audit |
| Stale fixtures | Spec change does not trigger fixture regeneration, leaving fixtures inconsistent with current spec | Spec Agent regenerates affected fixtures on every spec bump; Adversarial Auditor validates fixtures in Phase 2 |
| Implicit spec | SPEC.md omits behaviour that practitioners consider obvious | SOP-to-spec and PRD-to-spec derivation surfaces implicit assumptions |
| AI-authored scenarios compromising holdout independence | Scenarios authored by same model as implementation weaken independence guarantee | Authorship metadata; human scenario authorship preferred; compensating cross-model review where AI-authored |
| Scenario leakage via RAG | Workspace indexing exposes scenarios to Implementation Agent despite directory exclusion rules | Out-of-repo storage (Model A) mandatory in RAG-enabled environments |
| Test logic corruption | Implementation Agent weakens test assertion logic when completing stubs, causing tests to pass on non-conforming implementations | Implementation Agent prohibited from weakening assertions (§4.3); Adversarial Auditor validates fixture and test integrity in Phase 2 |
| Hallucinated fixtures | Spec Agent generates fixtures that reflect its interpretation of the spec rather than the spec itself | Adversarial Auditor validates all fixtures during Phase 2 before Phase 3 begins |

---

## 12. Open Questions for Round 2

- Template Repo: build and validate
- Scenario-fixture completeness pairing: assign a role to formally verify pairing before Phase 3
- Adversarial spec review semi-automation: feasibility of multi-model API script for parallel spec review
- Satisfaction metric: define trajectory sampling procedure and minimum sample size
- Partial compliance and waiver mechanism: formal protocol for accepting with known gaps
- Governance violation remediation: define quarantine, rollback, and re-audit procedures
- Agent identity model: define what constitutes a "separate model instance" operationally
- Tiered escalation: validate in practice; calibrate Tier 4A threshold
- DF applied to non-software domains: which governance patterns transfer
- Launcher/TUI interface layer: for projects targeting non-developer users, what interface pattern sits above CLI and how does this affect scenario authoring

---

## Appendix A — Round 1 Reference (TreeStream)

TreeStream is a Python CLI tool for deterministic directory serialisation. It served as the primary Round 1 DF test vehicle.

Round 1 status at close:
- SPEC.md: v0.1.16 (Final)
- AGENT_RULES.md: v0.1.19
- Scenario suite: 39/39 passing (S01–S36, automated)
- Manual end-to-end test: Passed (serialise → email → reconstruct)
- Repo: https://github.com/EvoAlg/treestream

Round 1 validated: role separation, adversarial audit framing, fixture-based testing, evaluation proxy pattern, human-only commit and deletion governance, `.treestreamignore` ignore file support, `--exclude` CLI flag, full automated test coverage S01–S36.

Note: Round 1 pre-dates this methodology version. Not all v2.3 governance requirements were applied in Round 1. Appendix A describes what was done, not what is required. The normative requirements are in §1–12.
