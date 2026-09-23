# UMI — Formalized Project Baseline

**Project:** UMI  
**Document:** Project Baseline — Problem, Origin, Vision and Solution  
**Status:** Working baseline  
**Last updated:** 9 September 2026

---

## 1. Purpose of This Document

This document establishes the formal baseline for the UMI project.

It captures the reasoning developed so far: where the idea came from, the problem being addressed, the intended solution, the experience we are designing, and the boundaries of what the first demonstrable version should prove.

This is a **baseline**, not a final product specification. As research, user validation, technical implementation, and competition requirements develop, individual sections may be refined. The central problem and intended direction should, however, remain stable unless new evidence requires a deliberate change.

---

# 2. The Birth of the Idea

UMI was born from a practical observation about how quality assurance work is managed.

The problem is not simply that QA teams have defects or findings. The deeper problem is what happens **after an issue is identified**.

A QA participant can report something that is wrong, incomplete, confusing, or broken. From there, the organization needs to understand the report, determine what action is required, assign responsibility, communicate with the right person, follow up on the fix, verify that the issue has actually been resolved, and finally close the work.

In a conventional process, these activities are fragmented across people, messages, reports, spreadsheets, and management follow-up.

This creates a gap between:

> **“Someone found a problem.”**

and

> **“The organization has verified that the problem has been resolved.”**

UMI emerged from the idea that this entire journey should be treated as one connected workflow rather than as a collection of disconnected administrative tasks.

The central design question became:

> **What if QA management could move from finding an issue to verified closure through one clear, intelligent workflow?**

That question forms the foundation of UMI.

---

# 3. Context

Quality assurance depends heavily on participation.

A QA process can have strong testing procedures, competent reviewers, and good reporting tools, but its effectiveness still depends on people actively reporting problems and following issues through to resolution.

In practice, this can create several operational challenges:

- QA findings can be difficult to organize and prioritize.
- Reports may lack the context needed for immediate action.
- Responsibility for fixing an issue may not be clear.
- Managers may need to manually coordinate follow-up.
- A reported issue can remain open without clear visibility into its current state.
- Verification of a fix can become a separate manual activity.
- Closing the loop with the person who reported or verified the issue can be inconsistent.
- The overall process can become administrative rather than outcome-oriented.

The project therefore focuses not only on **capturing QA findings**, but on managing the **full lifecycle of a QA issue**.

---

# 4. Problem Statement

## Core Problem

**UMI QA faces problems with low participant engagement and inefficient issue management, making it difficult to consistently move QA findings from initial reporting through assignment, resolution, verification, and closure.**

The current challenge is therefore both a **participation problem** and a **workflow-management problem**.

When the process requires too much manual coordination, participants have less incentive to engage, managers spend more effort chasing progress, and issues can remain unresolved or poorly tracked.

The result is a QA process where the existence of a report does not necessarily translate into a completed outcome.

## Problem in One Sentence

> **QA teams need a simpler and more accountable way to turn participant findings into verified, closed outcomes without relying on fragmented manual coordination.**

---

# 5. Why This Problem Matters

The value of QA is ultimately realized when findings lead to improvement.

A system that only collects reports can produce a large volume of information without necessarily producing better outcomes.

UMI therefore treats the following chain as important:

**Report → Understand → Assign → Fix → Verify → Close**

A weakness at any point can reduce the value of the entire QA process.

For example:

- A report that is not understood correctly cannot be acted on efficiently.
- An issue without an owner can remain unresolved.
- A fix without verification can create false confidence.
- A verified issue that is never properly closed leaves the workflow incomplete.

The objective is consequently not merely to increase the number of reports.

It is to improve the **conversion of QA participation into completed, verified outcomes**.

---

# 6. Solution Statement

## Formal Solution Statement

> **UMI is an intelligent QA management workflow that transforms participant findings into structured, actionable issues and guides them through reporting, triage, assignment, fixing, verification, and closure in one connected experience.**

The system is intended to reduce the coordination burden on QA managers while making the process clearer and more engaging for participants.

Rather than treating every QA report as an isolated message, UMI turns the report into a managed workflow with an explicit state and next action.

---

# 7. The Core Idea

At its simplest, UMI is built around one principle:

> **Every QA finding should have a clear path from discovery to verified closure.**

The system should make that path visible and actionable.

The intended lifecycle is:

```text
QA Finding
    ↓
Focused Report
    ↓
Triage / Understand
    ↓
Assign
    ↓
Fix
    ↓
Confirm
    ↓
Close
```

This lifecycle is the backbone of the UMI experience.

---

# 8. What UMI Is Trying to Change

UMI is not primarily trying to create another place where QA teams store reports.

It is trying to change the workflow from:

```text
Participant reports issue
        ↓
Manager interprets report
        ↓
Manager contacts responsible person
        ↓
Manager follows up
        ↓
Someone says it is fixed
        ↓
QA verifies manually
        ↓
Manager closes issue
```

into a more connected experience:

```text
Participant
   ↓
Clear finding
   ↓
UMI structures the issue
   ↓
Responsible person is assigned
   ↓
Fix is tracked
   ↓
QA confirms resolution
   ↓
Issue is closed
```

The important distinction is that UMI is designed around **workflow continuity and accountability**.

---

# 9. Intended Users

The primary stakeholders represented in the current concept are:

### QA Participants

People who identify and report problems.

Their experience should be lightweight and clear. They should not need to understand the entire internal QA management process simply to contribute a useful finding.

### QA Managers / Coordinators

People responsible for understanding findings, organizing work, assigning issues, monitoring progress, and ensuring closure.

UMI should reduce the amount of manual coordination required from this role.

### Fix Owners / Responsible Teams

People responsible for resolving identified issues.

They need enough context to understand what needs to be fixed and a clear indication of what is expected from them.

### Verifiers

People responsible for confirming whether a proposed fix actually resolves the reported issue.

Verification is treated as an explicit step rather than assuming that a claimed fix automatically means the issue is resolved.

---

# 10. Core Experience

The prototype developed for UMI is centered around a focused management workflow.

The primary demonstration should communicate the complete journey:

### 1. Focused Report

A QA finding is presented in a form that allows the manager to understand the actual issue quickly.

The objective is to move away from an unstructured report and toward a clear, actionable representation of the problem.

### 2. Assign

Once the issue is understood, it is assigned to the appropriate person or team.

The assignment creates ownership.

### 3. Fix

The responsible party works on the issue.

The workflow should make the current state visible rather than leaving the manager to infer progress from separate conversations.

### 4. Confirm

The proposed fix is reviewed and verified.

The confirmation step is critical because:

> **“Fixed” is not the same thing as “verified fixed.”**

### 5. Close

Once the issue has been confirmed as resolved, it is formally closed.

Closure represents completion of the QA lifecycle.

---

# 11. The Demo Story

The first prototype is intentionally designed around one complete scenario rather than attempting to demonstrate every possible UMI feature.

The demo should allow a user to click **Play Demo** and naturally experience the entire workflow.

The intended story is:

> A QA issue has been reported.  
> The QA manager opens the finding and quickly understands the problem.  
> The issue is assigned to the responsible person.  
> The responsible person addresses the issue.  
> QA reviews the result and confirms that the problem has been resolved.  
> The issue is closed.

The prototype should therefore contain all screens necessary to make this story coherent:

**Focused Report → Assign → Fix → Confirm → Close**

Each screen should feel like the next logical state of the same issue rather than a collection of unrelated mockups.

---

# 12. Product Principles

The current UMI direction is guided by several principles.

## 12.1 Outcome over volume

The goal is not simply to collect more QA reports.

The goal is to increase the number of findings that become **actionable, resolved, verified outcomes**.

## 12.2 Minimize coordination overhead

A QA manager should not have to manually orchestrate every step of the lifecycle.

The system should make the next action obvious.

## 12.3 Make ownership explicit

An issue should have a clear responsible person or team.

## 12.4 Make status visible

The state of an issue should be understandable without searching through multiple conversations or records.

## 12.5 Verification is a distinct state

A fix should not automatically equal closure.

Verification is part of the workflow.

## 12.6 Keep participation lightweight

Participants should be able to contribute useful QA findings without navigating a complicated management system.

## 12.7 Design for a natural human workflow

The interface should follow how people actually think about the task:

> What was found?  
> What needs to happen?  
> Who owns it?  
> Has it been fixed?  
> Is the fix correct?  
> Can we close it?

---

# 13. Conceptual System Model

At the conceptual level, UMI can be viewed as a workflow layer around QA findings.

```text
                   ┌─────────────────────┐
                   │   QA Participant    │
                   └──────────┬──────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  QA Finding      │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Focused Report   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Triage / Manage  │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │     Assign       │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │       Fix        │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │      Confirm     │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │      Close       │
                    └──────────────────┘
```

This is a conceptual model rather than a final technical architecture.

---

# 14. What the First Prototype Must Prove

The first prototype is not expected to prove the complete technical implementation of UMI.

It should prove that the **workflow itself makes sense**.

Specifically, the prototype should demonstrate:

1. A QA finding can be represented clearly.
2. A manager can understand what requires action.
3. Responsibility can be assigned.
4. Progress toward resolution can be represented.
5. A fix can be explicitly confirmed.
6. The issue can reach a clear closed state.
7. The experience feels like one continuous workflow.

The prototype should prioritize **clarity of the experience** over the number of features displayed.

---

# 15. Success Definition

The core success question for the concept is:

> **Can UMI make the journey from QA finding to verified closure clearer, faster, and more accountable?**

This can later be translated into measurable product metrics.

Potential measurement categories include:

### Engagement

- Number of participants actively reporting findings.
- Frequency of participant engagement.
- Completion rate of reporting workflows.

### Workflow efficiency

- Time from report to assignment.
- Time from assignment to fix.
- Time from fix to confirmation.
- Total time from report to closure.

### Accountability

- Percentage of issues with a clear owner.
- Percentage of issues with visible status.
- Percentage of issues reaching verified closure.

### Quality of resolution

- Percentage of fixes confirmed successfully.
- Number of issues reopened after failed verification.
- Completeness and usefulness of submitted findings.

These metrics are candidates for later validation and should not yet be treated as finalized KPIs.

---

# 16. Scope of the Current Baseline

The current baseline focuses on the **QA issue lifecycle**.

### In scope

- QA participant findings.
- Structured/focused reporting.
- Issue understanding and triage.
- Assignment.
- Fix workflow.
- Verification/confirmation.
- Closure.
- Visibility of issue state.
- The end-to-end management experience.

### Not yet finalized

The following areas remain implementation or research decisions rather than established baseline requirements:

- Exact AI models and model architecture.
- Exact integrations.
- Production infrastructure.
- Detailed database schema.
- Authentication and authorization design.
- Notification channels.
- Final analytics architecture.
- Exact prioritization algorithm.
- Exact SLA policy.
- Complete enterprise deployment model.

These should be specified after the core workflow and user requirements have been sufficiently validated.

---

# 17. Product Vision

## Short Vision

> **UMI aims to make QA management a continuous, accountable workflow from finding a problem to proving that it has been resolved.**

## Expanded Vision

UMI should evolve toward a QA environment where participant contributions do not disappear into reports, spreadsheets, or disconnected conversations.

Instead, each meaningful finding becomes a managed piece of work with:

- context,
- ownership,
- progress,
- verification,
- and a clear outcome.

The long-term opportunity is to make QA participation more rewarding because contributors can see that their findings lead to action, while giving managers a much clearer view of what is happening across the QA process.

---

# 18. Working Product Thesis

The project currently rests on the following thesis:

> **If QA findings are converted into clear, accountable workflows with explicit ownership, progress, verification, and closure, then the organization can reduce coordination friction and increase the likelihood that participant findings result in meaningful outcomes.**

The prototype exists to test whether this thesis is compelling and understandable from a user's perspective.

---

# 19. Current North Star

The current north-star concept for UMI is:

```text
More meaningful participation
             ↓
Better QA findings
             ↓
Clearer ownership
             ↓
Faster resolution
             ↓
Verified fixes
             ↓
More completed QA outcomes
```

The system should ultimately optimize for the **quality and completion of the QA lifecycle**, not merely the quantity of activity inside the system.

---

# 20. Baseline Summary

| Area | Current Baseline |
|---|---|
| Project | UMI |
| Core domain | QA management |
| Core problem | Low participant engagement and inefficient issue management |
| Primary gap | Findings do not consistently move cleanly from report to verified closure |
| Core solution | Connected QA issue lifecycle |
| Primary workflow | Focused Report → Assign → Fix → Confirm → Close |
| Primary users | QA participants, QA managers/coordinators, fix owners, verifiers |
| Prototype objective | Demonstrate one natural end-to-end QA lifecycle |
| Core value | Less coordination friction, clearer accountability, stronger closure |
| Long-term vision | Turn QA findings into measurable, verified outcomes |

---

# 21. What Comes Next

This baseline provides the foundation for the next project documents.

The logical next deliverables are:

1. **User and stakeholder definition**
2. **Detailed problem analysis**
3. **Current-state vs. future-state workflow**
4. **Functional requirements**
5. **Non-functional requirements**
6. **Detailed UMI user journey**
7. **Prototype screen specification**
8. **System architecture**
9. **AI/automation opportunities**
10. **Data model and workflow states**
11. **Success metrics and evaluation plan**
12. **Implementation roadmap**

These should build on this baseline rather than independently redefining the project.

---

# 22. Baseline Principle

The most important statement to carry forward is:

> **UMI is not simply a system for collecting QA reports. It is a system for turning QA findings into owned, resolved, verified, and closed outcomes.**
