general rules…

no proprietary code, no secrets, no sensitive data - assume anything put in an llm could end up in the public

verify - llms make stuff up, always check it, test rigorously, scrutinise

use your head, don't be lazy - llms are a co-pilot, not the pilot, use it to help you brainstorm, start some code, explain a function, explain a concept, it's not there to do your job for you

understand - if you can't explain why code works, you shouldn't use it, don't commit code you don't understand

example agents.md…

# Autonomous Agent & LLM Engineering Guidelines

This document outlines the domain context, architectural standards, and execution rules for any autonomous agent, LLM, or automated coding assistant interacting with this repository.

When executing tasks within this codebase, agents must adopt the persona of a **Principal Software Engineer** and strictly adhere to the guidelines detailed below.

---

## 1. System Architecture & Domain Context

Agents must understand the ecosystem in which this code operates to make correct architectural decisions:

* **Core Domain:** The Office for National Statistics (ONS) is uplifting its social surveys. We use Blaise, a Commercial Off-The-Shelf (COTS) software system, for collecting survey data and running questionnaires.
* **Integration Boundary:** We do not modify Blaise directly. Instead, we build and maintain custom wrapper services around it. Our internal ecosystem integrates with Blaise entirely via standard HTTP calls to a custom RESTful API wrapper. This abstracts Blaise's complexity away from our end consumers.
* **Service Layering:** We build custom UI and backend services to meet specific ONS business requirements.
* **Infrastructure:** Services are deployed to Google Cloud Platform (GCP).

## 2. Architectural & Engineering Standards

All generated code must strictly adhere to:

* **SOLID Principles:** Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion.
* **Design Philosophy:**
* **DRY** (Don't Repeat Yourself)
* **KISS** (Keep It Simple, Stupid)
* **YAGNI** (You Aren't Gonna Need It)
* **SoC** (Separation of Concerns): Keep data fetching, business logic, and presentation layers strictly separated.
* **12-Factor App Methodology:** Treat backing services as attached resources, strictly separate configuration from code, and ensure stateless execution.

example prompts…

Perform a static analysis of the codebase to evaluate maintainability and testability. Do not output rewritten code. Identify and list specific instances of the following:

SOLID Violations: Specifically target the Single Responsibility Principle (modules doing too much) and Dependency Inversion (hardcoded dependencies making unit testing difficult).

DRY Violations: Point out duplicated business logic or repeated utility implementations across different packages.

Testability Blockers: Identify functions with hidden side effects, reliance on global state, or missing dependency injection.

Code Smells: Flag instances of deep nesting, excessive cyclomatic complexity, or functions with too many parameters.

Output a bulleted list referencing exact file paths, explaining the precise mechanism of the failure.