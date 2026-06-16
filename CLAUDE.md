# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Build a FastAPI proxy that serves customer traffic using a primary LLM mock, while asynchronously shadowing requests to a candidate LLM and logging mismatches.

## working style
Think before coding. State assumptions; if multiple interpretations exist, present them. When something is unclear, stop and ask.
Simplicity first. Minimum code that solves the problem. No abstractions for single-use code, no flexibility that wasn't requested. If 200 lines could be 50, rewrite.
Surgical changes. Touch only what the task requires. Match existing style. Don't refactor what isn't broken. Every changed line should trace to the request.
Verify before claiming done. Define a check before implementing — a test, a runnable command, a measurement. Loop until the check passes.
Small steps, documented. Each meaningful change traces to a spec or decision record. If you can't write the spec, the change isn't ready.
Restructure top-down and end-to-end. When moving, renaming, adding, or removing structure, trace the change from the repo root through every subproject and through the build/deploy path (Dockerfile, CI, Makefiles, configs, docs). Re-derive what the surrounding structure was for — if its reason no longer holds, remove it in the same pass. Don't leave orphaned root-level files, vestigial config, or stale build steps as follow-ups.