# Paper2Code Technical One-Pager

## Overview

Paper2Code is a multi-agent research engineering system that converts an arXiv paper into a local implementation workspace. It automates the high-friction path from paper reading to initial code scaffolding by parsing the paper, extracting architecture signals from figures, generating an implementation plan, producing code modules, and packaging the results into inspectable artifacts.

## The Problem

Modern ML and AI papers are rich in ideas but expensive to operationalize. Engineers and researchers still spend significant manual effort:

- reading long PDFs to identify the core architecture
- mapping theory sections to software modules
- interpreting architecture diagrams by hand
- writing initial implementation scaffolding
- checking whether generated code actually matches the paper

This slows down research reproduction, prototype building, and technical evaluation. The manual process is repetitive, error-prone, and hard to scale across multiple papers.

## Current Manual Solution

Today, teams usually solve this problem through a highly manual workflow:

1. A researcher reads the paper and highlights the method sections.
2. An engineer interprets diagrams and equations into components.
3. The team breaks the architecture into files, classes, and dependencies.
4. Code is written module by module.
5. Someone reviews whether the implementation still matches the paper.
6. Artifacts are organized manually for sharing or further work.

This approach works, but it requires repeated expert attention and creates a long delay between reading a paper and testing a prototype.

## What We Built

We built a production-style LangGraph pipeline that automates this workflow into a repeatable system.

Core capabilities:

- fetches and parses an arXiv paper PDF
- extracts full text, metadata, and figure data
- analyzes architecture-related figures with a vision model
- produces a structured implementation plan
- generates Python modules in sequence
- runs a coder-critic validation loop
- creates tests and local artifacts
- exports a zipped run package for review and sharing

The system is optimized to run locally and store outputs directly in the selected project folder.

## How It Works

Paper2Code uses a shared typed state and a LangGraph workflow to coordinate multiple stages:

1. Parser stage
   Fetches the paper from arXiv, extracts raw text, metadata, and figures, and persists source artifacts.

2. Vision stage
   Selects architecture-relevant figures and asks a vision-capable LLM to describe implementation-oriented components and data flow.

3. Planner stage
   Uses paper text plus figure analysis to create an ordered JSON implementation plan of modules, dependencies, and references.

4. Coder-Critic stage
   Generates one module at a time and checks it against the module spec and paper excerpt before accepting it.

5. Test stage
   Produces a lightweight test artifact and final report.

6. Packaging stage
   Writes all outputs to a run directory and creates a zip export for easy distribution.

## What Exactly the System Produces

For each paper run, the system creates:

- source paper artifacts
- extracted metadata
- figure metadata
- architecture analysis
- implementation plan
- generated Python modules
- review files
- generated tests
- run report
- zipped artifact bundle

These outputs are stored in a timestamped run folder under `data/runs/`.

## Who It Helps

Paper2Code is useful for:

- ML engineers who need fast implementation scaffolding from papers
- research teams validating whether a paper is worth reproducing
- students learning how papers map into code structure
- technical leads evaluating architectures before assigning build effort
- developer tooling teams building research-to-engineering workflows

## Business and Engineering Impact

Paper2Code reduces the time between paper discovery and runnable implementation artifacts. Instead of starting from a blank notebook, teams begin with a structured, reviewable workspace.

Key impact areas:

- faster research reproduction
- lower manual interpretation effort
- more consistent module planning
- better traceability from paper sections to code
- easier sharing of outputs across engineers and reviewers

Even when the generated code is not final production code, it accelerates the first 60 to 70 percent of the implementation setup process.

## Why This Approach Is Valuable

Most paper-to-code attempts rely only on text. Paper2Code improves on that by using both text and figures. Architecture diagrams often contain the clearest representation of module relationships, data flow, and implementation structure, so including vision analysis makes the pipeline more useful and more realistic.

The coder-critic loop also reflects how real engineering teams work: generation followed by review against a specification. That makes the system more robust than single-pass code generation.

## Current Scope

The current implementation is optimized for Groq free-tier usage and local execution:

- smaller default text model
- limited architecture figure analysis
- capped module planning
- reduced critic retries
- local artifact persistence
- CLI, API, and Streamlit interfaces

This makes the system practical for prototyping without paid infrastructure.

## Future Extensions

Potential next steps include:

- GitHub PR creation
- richer equation grounding
- stronger testing and runtime validation
- checkpointed resume for long runs
- multiple provider backends
- ranking and selecting the best generated implementation variant

## Summary

Paper2Code turns paper understanding into engineering momentum. It automates a manual, expert-heavy workflow into a structured, inspectable pipeline that helps teams move faster from research papers to practical implementation assets.
