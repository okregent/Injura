# Injura Development Principles

## Purpose

The MVP is a milestone toward the final product, not the final goal.

Every implementation must: 1. Deliver the current MVP. 2. Preserve the
architecture required by the final product.

## Core Principles

### 1. Product-First Development

Order: 1. Product Requirement 2. Architecture Design 3. MVP Scope 4.
Implementation 5. Validation

### 2. MVP Without Architectural Debt

Temporary feature limitations are acceptable. Temporary architecture is
not.

### 3. Future Expansion by Default

Every module should assume future expansion: - More exercises - More
camera views - Better pose models - Personalisation

### 4. Document Deferred Features

Every omitted feature must record: - Purpose - Reason for exclusion -
Dependencies - Proposed algorithm - Future implementation notes

### 5. Record Technical Debt

Every limitation should be documented with: - Current implementation -
Reason - Future direction

## Standard Development Workflow

1.  Product Perspective
2.  Final Product Design
3.  MVP Scope
4.  Architecture Review
5.  Implementation
6.  Validation

## Recommended Documentation

docs/ - product/ - mvp-scope.md - product-capability-roadmap.md -
architecture/ - metric-catalog.md - architecture-decisions.md -
development/ - technical-debt.md - coding-principles.md - management/ -
roadmap.md

## Product Capability Roadmap

### MVP

-   Phase detection
-   Rep detection
-   Squat depth
-   Torso lean
-   Knee travel
-   Heel lift
-   Lumbar rounding proxy
-   Tempo
-   Movement smoothness
-   Explainable feedback

### Future

-   Personalisation
-   Multi-view analysis
-   Knee valgus
-   Hip shift
-   Pelvic tilt
-   Lumbar curvature estimation
-   Ankle mobility inference
-   Compensation-chain analysis
-   Fatigue detection
-   Additional exercises
-   Real-time coaching
-   Progress dashboard

## Metric Documentation Template

Each metric should contain: - Name - Product priority - Status -
Purpose - Required camera view - Required landmarks - Algorithm -
Output - Limitations - Future improvements - Dependencies

Status values: - IDEA - PLANNED - MVP_PROXY - IN_PROGRESS -
IMPLEMENTED - VALIDATED - DEFERRED

## Long-Term Rule

Every implementation should satisfy both: 1. Best choice for the MVP. 2.
Still appropriate for the final production system.
