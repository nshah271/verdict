**User:**

<task>Command 'init' (see below for command content)
</task>

<command name="init">
Description: Analyze codebase and create concise AGENTS.md files for AI assistants

<task>
Please analyze this codebase and create an AGENTS.md file containing:
1. Build/lint/test commands - especially for running a single test
2. Code style guidelines including imports, formatting, types, naming conventions, error handling, etc.
</task>

<initialization>
  <purpose>
    Create (or update) a concise AGENTS.md file that enables immediate productivity for AI assistants.
    Focus ONLY on project-specific, non-obvious information that you had to discover by reading files.
    
    CRITICAL: Only include information that is:
    - Non-obvious (couldn't be guessed from standard practices)
    - Project-specific (not generic to the framework/language)
    - Discovered by reading files (config files, code patterns, custom utilities)
    - Essential for avoiding mistakes or following project conventions
    
    Usage notes:
    - The file you create will be given to agentic coding agents (such as yourself) that operate in this repository
    - Keep the main AGENTS.md concise - aim for about 20 lines, but use more if the project complexity requires it
    - If there's already an AGENTS.md, improve it
    - If there are Claude Code rules (in CLAUDE.md), Cursor rules (in .cursor/rules/ or .cursorrules), or Copilot rules (in .github/copilot-instructions.md), make sure to include them
    - Be sure to prefix the file with: "# AGENTS.md\n\nThis file provides guidance to agents when working with code in this repository."
  </purpose>
  
  <todo_list_creation>
    If the update_todo_list tool is available, create a todo list with these focused analysis steps:
    
    1. Check for existing AGENTS.md files
       CRITICAL - Check these EXACT paths IN THE PROJECT ROOT:
       - AGENTS.md (in project root directory)
       - .bob/rules-code/AGENTS.md (relative to project root)
       - .bob/rules-advanced/AGENTS.md (relative to project root)
       - .bob/rules-ask/AGENTS.md (relative to project root)
       - .bob/rules-plan/AGENTS.md (relative to project root)
       
       IMPORTANT: All paths are relative to the project/workspace root, NOT system root!
       
       If ANY of these exist:
       - Read them thoroughly
       - CRITICALLY EVALUATE: Remove ALL obvious information
       - DELETE entries that are standard practice or framework defaults
       - REMOVE anything that could be guessed without reading files
       - Only KEEP truly non-obvious, project-specific discoveries
       - Then add any new non-obvious patterns you discover
       
       Also check for other AI assistant rules:
       - .cursorrules, CLAUDE.md, .roorules
       - .cursor/rules/, .github/copilot-instructions.md
    
    2. Identify stack
       - Language, framework, build tools
       - Package manager and dependencies
    
    3. Extract commands
       - Build, test, lint, run
       - Critical directory-specific commands
    
    4. Map core architecture
       - Main components and flow
       - Key entry points
    
    5. Document critical patterns
       - Project-specific utilities (that you discovered by reading code)
       - Non-standard approaches (that differ from typical patterns)
       - Custom conventions (that aren't obvious from file structure)
    
    6. Extract code style
       - From config files only
       - Key conventions
    
    7. Testing specifics
       - Framework and run commands
       - Directory requirements
    
    8. Compile/Update AGENTS.md files
       - If files exist: AGGRESSIVELY clean them up
         * DELETE all obvious information (even if it was there before)
         * REMOVE standard practices, framework defaults, common patterns
         * STRIP OUT anything derivable from file structure or names
         * ONLY KEEP truly non-obvious discoveries
         * Then add newly discovered non-obvious patterns
         * Result should be SHORTER and MORE FOCUSED than before
       - If creating new: Follow the non-obvious-only principle
       - Create mode-specific files in .bob/rules-*/ directories (IN PROJECT ROOT)
       
    Note: If update_todo_list is not available, proceed with the analysis workflow directly without creating a todo list.
  </todo_list_creation>
</initialization>

<analysis_workflow>
  Follow the comprehensive analysis workflow to:
  
  1. **Discovery Phase**:
     CRITICAL - First check for existing AGENTS.md files at these EXACT locations IN PROJECT ROOT:
     - AGENTS.md (in project/workspace root)
     - .bob/rules-code/AGENTS.md (relative to project root)
     - .bob/rules-advanced/AGENTS.md (relative to project root)
     - .bob/rules-ask/AGENTS.md (relative to project root)
     - .bob/rules-plan/AGENTS.md (relative to project root)
     
     IMPORTANT: The .roo folder should be created in the PROJECT ROOT, not system root!
     
     If found, perform CRITICAL analysis:
     - What information is OBVIOUS and must be DELETED?
     - What violates the non-obvious-only principle?
     - What would an experienced developer already know?
     - DELETE first, then consider what to add
     - The file should get SHORTER, not longer
     
     Also find other AI assistant rules and documentation
     
  2. **Project Identification**: Identify language, stack, and build system
  3. **Command Extraction**: Extract and verify essential commands
  4. **Architecture Mapping**: Create visual flow diagrams of core processes
  5. **Component Analysis**: Document key components and their interactions
  6. **Pattern Analysis**: Identify project-specific patterns and conventions
  7. **Code Style Extraction**: Extract formatting and naming conventions
  8. **Security & Performance**: Document critical patterns if relevant
  9. **Testing Discovery**: Understand testing setup and practices
  10. **Example Extraction**: Find real examples from the codebase
</analysis_workflow>

<output_structure>
  <main_file>
    Create or deeply improve AGENTS.md with ONLY non-obvious information:
    
    If AGENTS.md exists:
    - FIRST: Delete ALL obvious information
    - REMOVE: Standard commands, framework defaults, common patterns
    - STRIP: Anything that doesn't require file reading to know
    - EVALUATE: Each line - would an experienced dev be surprised?
    - If not surprised, DELETE IT
    - THEN: Add only truly non-obvious new discoveries
    - Goal: File should be SHORTER and MORE VALUABLE
    
    Content should include:
    - Header: "# AGENTS.md\n\nThis file provides guidance to agents when working with code in this repository."
    - Build/lint/test commands - ONLY if they differ from standard package.json scripts
    - Code style - ONLY project-specific rules not covered by linter configs
    - Custom utilities or patterns discovered by reading the code
    - Non-standard directory structures or file organizations
    - Project-specific conventions that violate typical practices
    - Critical gotchas that would cause errors if not followed
    
    EXCLUDE obvious information like:
    - Standard npm/yarn commands visible in package.json
    - Framework defaults (e.g., "React uses JSX")
    - Common patterns (e.g., "tests go in __tests__ folders")
    - Information derivable from file extensions or directory names
    
    Keep it concise (aim for ~20 lines, but expand as needed for complex projects).
    Include existing AI assistant rules from CLAUDE.md, Cursor rules (.cursor/rules/ or .cursorrules), or Copilot rules (.github/copilot-instructions.md).
  </main_file>
  
  <mode_specific_files>
    Create or deeply improve mode-specific AGENTS.md files IN THE PROJECT ROOT.
    
    CRITICAL: For each of these paths (RELATIVE TO PROJECT ROOT), check if the file exists FIRST:
    - .bob/rules-code/AGENTS.md (create .roo in project root, not system root!)
    - .bob/rules-advanced/AGENTS.md (relative to project root)
    - .bob/rules-ask/AGENTS.md (relative to project root)
    - .bob/rules-plan/AGENTS.md (relative to project root)
    
    IMPORTANT: The .roo directory must be created in the current project/workspace root directory,
    NOT at the system root (/) or home directory. All paths are relative to where the project is located.
    
    If files exist:
    - AGGRESSIVELY DELETE obvious information
    - Remove EVERYTHING that's standard practice
    - Strip out framework defaults and common patterns
    - Each remaining line must be surprising/non-obvious
    - Only then add new non-obvious discoveries
    - Files should become SHORTER, not longer
    
    Example structure (ALL IN PROJECT ROOT):
    ```
    project-root/
    ├── AGENTS.md                    # General project guidance
    ├── .bob/                        # IN PROJECT ROOT, NOT SYSTEM ROOT!
    │   ├── rules-code/
    │   │   └── AGENTS.md           # Code mode specific instructions
    │   ├── rules-advanced/
    │   │   └── AGENTS.md           # Advanced mode specific instructions
    │   ├── rules-ask/
    │   │   └── AGENTS.md           # Ask mode specific instructions
    │   └── rules-plan/
    │       └── AGENTS.md           # Plan mode specific instructions
    ├── src/
    ├── package.json
    └── ... other project files
    ```
    
    .bob/rules-code/AGENTS.md - ONLY non-obvious coding rules discovered by reading files:
    - Custom utilities that replace standard approaches
    - Non-standard patterns unique to this project
    - Hidden dependencies or coupling between components
    - Required import orders or naming conventions not enforced by linters
    - No access to tools like MCP and Browser
    
    Example of non-obvious rules worth documenting:
    ```
    # Project Coding Rules (Non-Obvious Only)
    - Always use safeWriteJson() from src/utils/ instead of JSON.stringify for file writes (prevents corruption)
    - API retry mechanism in src/api/providers/utils/ is mandatory (not optional as it appears)
    - Database queries MUST use the query builder in packages/evals/src/db/queries/ (raw SQL will fail)
    - Provider interface in packages/types/src/ has undocumented required methods
    - Test files must be in same directory as source for vitest to work (not in separate test folder)
    ```
    
    .bob/rules-advanced/AGENTS.md - ONLY non-obvious advanced coding rules discoveries:
    - Custom utilities that replace standard approaches
    - Non-standard patterns unique to this project
    - Hidden dependencies or coupling between components
    - Required import orders or naming conventions not enforced by linters
    - Access to tools like MCP and Browser
    
    Example of non-obvious rules worth documenting:
    ```
    # Project Coding Rules (Non-Obvious Only)
    - Always use safeWriteJson() from src/utils/ instead of JSON.stringify for file writes (prevents corruption)
    - API retry mechanism in src/api/providers/utils/ is mandatory (not optional as it appears)
    - Database queries MUST use the query builder in packages/evals/src/db/queries/ (raw SQL will fail)
    - Provider interface in packages/types/src/ has undocumented required methods
    - Test files must be in same directory as source for vitest to work (not in separate test folder)
    ```
    
    .bob/rules-ask/AGENTS.md - ONLY non-obvious documentation context:
    - Hidden or misnamed documentation
    - Counterintuitive code organization
    - Misleading folder names or structures
    - Important context not evident from file structure
    
    Example of non-obvious documentation rules worth documenting:
    ```
    # Project Documentation Rules (Non-Obvious Only)
    - "src/" contains VSCode extension code, not source for web apps (counterintuitive)
    - Provider examples in src/api/providers/ are the canonical reference (docs are outdated)
    - UI runs in VSCode webview with restrictions (no localStorage, limited APIs)
    - Package.json scripts must be run from specific directories, not root
    - Locales in root are for extension, webview-ui/src/i18n for UI (two separate systems)
    ```
    
    .bob/rules-plan/AGENTS.md - ONLY non-obvious architectural constraints:
    - Hidden coupling between components
    - Undocumented architectural decisions
    - Non-standard patterns that must be followed
    - Performance bottlenecks discovered through investigation
    
    Example of non-obvious architecture rules worth documenting:
    ```
    # Project Architecture Rules (Non-Obvious Only)
    - Providers MUST be stateless - hidden caching layer assumes this
    - Webview and extension communicate through specific IPC channel patterns only
    - Database migrations cannot be rolled back - forward-only by design
    - React hooks required because external state libraries break webview isolation
    - Monorepo packages have circular dependency on types package (intentional)
    ```
  </mode_specific_files>
</output_structure>

<quality_criteria>
  - ONLY include non-obvious information discovered by reading files
  - Exclude anything that could be guessed from standard practices
  - Focus on gotchas, hidden requirements, and counterintuitive patterns
  - Include specific file paths when referencing custom utilities
  - Be extremely concise - if it's obvious, don't include it
  - Every line should prevent a potential mistake or confusion
  - Test: Would an experienced developer be surprised by this information?
  - If updating existing files: DELETE obvious info first, files should get SHORTER
  - Measure success: Is the file more concise and valuable than before?
</quality_criteria>

Remember: The goal is to create documentation that enables AI assistants to be immediately productive in this codebase, focusing on project-specific knowledge that isn't obvious from the code structure alone.
</command>
<environment_details>
# VSCode Visible Files
verdict\types.py

# VSCode Open Tabs
verdict/types.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T17:30:10.624Z
User time zone: America/Toronto, UTC-4:00

# Current Cost
$0.00

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>plan</slug>
<name>📝 Plan</name>


# Current Workspace Directory (c:/Users/TestF/Desktop/Research/verdict) Files
.gitignore
pyproject.toml
README.md
TEAM.md
verdict-spec.md
verdict/
verdict/__init__.py
verdict/types.py
You have not created a todo list yet. Create one with `update_todo_list` if your task is complicated or involves multiple steps.
</environment_details>

---

**Assistant:**

I'll analyze this codebase and create a concise AGENTS.md file with non-obvious, project-specific information. Let me start by gathering context about the project.

<update_todo_list>
<todos>
[-] Check for existing AGENTS.md files and AI assistant rules
[ ] Identify project stack and structure
[ ] Extract build/test/lint commands
[ ] Analyze code patterns and conventions
[ ] Document non-obvious project-specific information
[ ] Create/update AGENTS.md files
</todos>
</update_todo_list>

<read_file>
<args>
  <file>
    <path>AGENTS.md</path>
  </file>
  <file>
    <path>.bob/rules-code/AGENTS.md</path>
  </file>
  <file>
    <path>.bob/rules-advanced/AGENTS.md</path>
  </file>
  <file>
    <path>.bob/rules-ask/AGENTS.md</path>
  </file>
  <file>
    <path>.bob/rules-plan/AGENTS.md</path>
  </file>
</args>
</read_file>

---

**User:**

[update_todo_list] Result:
Todo list updated successfully.
Tool [read_file] was not executed because a tool has already been used in this message. Only one tool may be used per message. You must assess the first tool's result before proceeding to use the next tool.
<environment_details>
# VSCode Visible Files
verdict\types.py

# VSCode Open Tabs
verdict/types.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T17:30:22.246Z
User time zone: America/Toronto, UTC-4:00

# Current Cost
$0.04

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>plan</slug>
<name>📝 Plan</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Check for existing AGENTS.md files and AI assistant rules | In Progress |
| 2 | Identify project stack and structure | Pending |
| 3 | Extract build/test/lint commands | Pending |
| 4 | Analyze code patterns and conventions | Pending |
| 5 | Document non-obvious project-specific information | Pending |
| 6 | Create/update AGENTS.md files | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<read_file>
<args>
  <file>
    <path>AGENTS.md</path>
  </file>
  <file>
    <path>.bob/rules-code/AGENTS.md</path>
  </file>
  <file>
    <path>.bob/rules-advanced/AGENTS.md</path>
  </file>
  <file>
    <path>.bob/rules-ask/AGENTS.md</path>
  </file>
  <file>
    <path>.bob/rules-plan/AGENTS.md</path>
  </file>
</args>
</read_file>

---

**User:**

[read_file for 5 files] Result:
<files>
<file><path>AGENTS.md</path><error>File not found</error><notice>The file was not found. Consider using list_files to find available files before attempting to read them.</notice></file>
<file><path>.bob/rules-code/AGENTS.md</path><error>File not found</error><notice>The file was not found. Consider using list_files to find available files before attempting to read them.</notice></file>
<file><path>.bob/rules-advanced/AGENTS.md</path><error>File not found</error><notice>The file was not found. Consider using list_files to find available files before attempting to read them.</notice></file>
<file><path>.bob/rules-ask/AGENTS.md</path><error>File not found</error><notice>The file was not found. Consider using list_files to find available files before attempting to read them.</notice></file>
<file><path>.bob/rules-plan/AGENTS.md</path><error>File not found</error><notice>The file was not found. Consider using list_files to find available files before attempting to read them.</notice></file>
</files>
<environment_details>
# VSCode Visible Files
verdict\types.py

# VSCode Open Tabs
verdict/types.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T17:30:28.148Z
User time zone: America/Toronto, UTC-4:00

# Current Cost
$0.08

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>plan</slug>
<name>📝 Plan</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Check for existing AGENTS.md files and AI assistant rules | In Progress |
| 2 | Identify project stack and structure | Pending |
| 3 | Extract build/test/lint commands | Pending |
| 4 | Analyze code patterns and conventions | Pending |
| 5 | Document non-obvious project-specific information | Pending |
| 6 | Create/update AGENTS.md files | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<read_file>
<args>
  <file>
    <path>.cursorrules</path>
  </file>
  <file>
    <path>CLAUDE.md</path>
  </file>
  <file>
    <path>.roorules</path>
  </file>
  <file>
    <path>.github/copilot-instructions.md</path>
  </file>
</args>
</read_file>

---

**User:**

[read_file for 4 files] Result:
<files>
<file><path>.cursorrules</path><error>File not found</error><notice>The file was not found. Consider using list_files to find available files before attempting to read them.</notice></file>
<file><path>CLAUDE.md</path><error>File not found</error><notice>The file was not found. Consider using list_files to find available files before attempting to read them.</notice></file>
<file><path>.roorules</path><error>File not found</error><notice>The file was not found. Consider using list_files to find available files before attempting to read them.</notice></file>
<file><path>.github/copilot-instructions.md</path><error>File not found</error><notice>The file was not found. Consider using list_files to find available files before attempting to read them.</notice></file>
</files>
<environment_details>
# VSCode Visible Files
verdict\types.py

# VSCode Open Tabs
verdict/types.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T17:30:32.581Z
User time zone: America/Toronto, UTC-4:00

# Current Cost
$0.12

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>plan</slug>
<name>📝 Plan</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Check for existing AGENTS.md files and AI assistant rules | In Progress |
| 2 | Identify project stack and structure | Pending |
| 3 | Extract build/test/lint commands | Pending |
| 4 | Analyze code patterns and conventions | Pending |
| 5 | Document non-obvious project-specific information | Pending |
| 6 | Create/update AGENTS.md files | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<update_todo_list>
<todos>
[x] Check for existing AGENTS.md files and AI assistant rules
[-] Identify project stack and structure
[ ] Extract build/test/lint commands
[ ] Analyze code patterns and conventions
[ ] Document non-obvious project-specific information
[ ] Create/update AGENTS.md files
</todos>
</update_todo_list>

---

**User:**

[update_todo_list] Result:
Todo list updated successfully.
<environment_details>
# VSCode Visible Files
verdict\types.py

# VSCode Open Tabs
verdict/types.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T17:30:40.523Z
User time zone: America/Toronto, UTC-4:00

# Current Cost
$0.16

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>plan</slug>
<name>📝 Plan</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Check for existing AGENTS.md files and AI assistant rules | Completed |
| 2 | Identify project stack and structure | In Progress |
| 3 | Extract build/test/lint commands | Pending |
| 4 | Analyze code patterns and conventions | Pending |
| 5 | Document non-obvious project-specific information | Pending |
| 6 | Create/update AGENTS.md files | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<read_file>
<args>
  <file>
    <path>pyproject.toml</path>
  </file>
  <file>
    <path>README.md</path>
  </file>
  <file>
    <path>verdict-spec.md</path>
  </file>
  <file>
    <path>TEAM.md</path>
  </file>
</args>
</read_file>

---

**User:**

[read_file for 4 files] Result:
<files>
<file><path>pyproject.toml</path>
<content lines="1-34">
 1 | [build-system]
 2 | requires = ["setuptools>=68"]
 3 | build-backend = "setuptools.build_meta"
 4 | 
 5 | [project]
 6 | name = "verdict-ai"
 7 | version = "0.1.0.dev0"
 8 | description = "A lie detector for AI coding agents: audits diffs and traces what actually runs."
 9 | readme = "README.md"
10 | requires-python = ">=3.10"
11 | license = { text = "MIT" }
12 | authors = [{ name = "verdict contributors" }]
13 | classifiers = [
14 |   "Programming Language :: Python :: 3",
15 |   "Programming Language :: Python :: 3.10",
16 |   "Programming Language :: Python :: 3.11",
17 |   "Programming Language :: Python :: 3.12",
18 |   "License :: OSI Approved :: MIT License",
19 |   "Operating System :: OS Independent",
20 | ]
21 | dependencies = []
22 | 
23 | [project.optional-dependencies]
24 | dev = ["ruff", "pytest", "pre-commit"]
25 | 
26 | [tool.setuptools.packages.find]
27 | include = ["verdict*"]
28 | 
29 | [tool.ruff]
30 | line-length = 100
31 | target-version = "py310"
32 | 
33 | [tool.ruff.lint]
34 | select = ["E", "F", "I", "B", "UP"]
</content>
</file>
<file><path>README.md</path>
<content lines="1-18">
 1 | # verdict
 2 | 
 3 | A lie detector for AI coding agents. Audits an AI-generated diff statically and traces what actually runs when the tests execute, then returns a single scorecard: `PASS`, `SUSPICIOUS`, or `LIED`.
 4 | 
 5 | Built for the IBM Bob hackathon (May 2026). Repo bootstrap in progress; the real README lands as part of P3.5.
 6 | 
 7 | ## Status
 8 | 
 9 | | Priority | Owner | Status |
10 | |----------|-------|--------|
11 | | P0.1 foundation (diff + AST) | Neel | not started |
12 | | P0.2 dead function detection | Jacob | not started |
13 | | P0.3 vacuous test detection | Alexie | not started |
14 | | P0.4 CLI + scorecard | Neel | not started |
15 | | P1.1 execution tracer | Neel | not started |
16 | | P1.2 MCP server | Ben | not started |
17 | 
18 | See `verdict-spec.md` and `TEAM.md` (local to the team, not in this repo) for the full plan.
</content>
</file>
<file><path>verdict-spec.md</path>
<content lines="1-403">
  1 | # verdict — a lie detector for AI coding agents
  2 | 
  3 | **One-line pitch:** verdict catches the moment an AI coding agent says "done ✅" when it isn't — by auditing the diff statically and tracing what actually runs when the tests execute.
  4 | 
  5 | ---
  6 | 
  7 | ## 1. The problem (in plain words)
  8 | 
  9 | AI coding agents — Cursor, Claude Code, Bob, Replit, etc. — have a consistency problem. You ask one to add a feature. It writes some code, runs some commands, and confidently says "done, tests passing, all good."
 10 | 
 11 | You check, and:
 12 | - the new function it added is never called from anywhere
 13 | - the "tests" it wrote are `assert True` or asserts on mocks that prove nothing
 14 | - the file it said it created doesn't exist
 15 | - the imported method doesn't exist in that library
 16 | - the diff doesn't actually do what the task asked for
 17 | 
 18 | This isn't a hallucination problem. The agent produced *something*. It just didn't verify any of it worked before claiming victory. And the tools sitting between the agent and your `main` branch don't catch it either, because they verify by reading the agent's transcript — which is the very thing that's lying.
 19 | 
 20 | Industry signal in mid-2026:
 21 | - Berkeley researchers got 100% on SWE-bench by gaming the eval pipeline without solving any task
 22 | - A real-time hallucination tracker has logged 12,000+ documented agent failures across the major tools
 23 | - Recurring HN threads ("Don't trust AI agents", "When AI writes the software, who verifies it?", the Replit production-DB-deletion incident)
 24 | - The RubberDuckBench academic paper found models hallucinate "lies" in 58% of responses on average
 25 | 
 26 | The industry's answer is **outcome-based verification** — instead of trusting the agent's transcript, check what actually happened on disk and in the test run. No canonical OSS tool exists for it yet. That's what verdict is.
 27 | 
 28 | ---
 29 | 
 30 | ## 2. The solution (in plain words)
 31 | 
 32 | verdict audits an AI-generated diff and tells you whether the agent did what it claimed.
 33 | 
 34 | **Static checks** look at the code without running it. Are added functions unused? Are new tests vacuous? Are imports hallucinated?
 35 | 
 36 | **Dynamic checks** actually run the tests with instrumentation. Did the new code execute when the test suite ran? Or did it sit there untouched while pre-existing code paths made the tests pass?
 37 | 
 38 | Output is a single **scorecard**: `PASS`, `SUSPICIOUS`, or `LIED` — plus inline annotations.
 39 | 
 40 | Ships as a CLI, an MCP server (so Bob or any agent can call verdict on itself), and eventually a GitHub Action.
 41 | 
 42 | ---
 43 | 
 44 | ## 3. How to use this doc
 45 | 
 46 | Features are ordered by priority. **Build straight down the list. Stop where you stop.** Each priority tier is a coherent product on its own — you can ship after P0 and have something demoable, ship after P1 and have a hackathon winner, ship after P2 and have a real OSS project.
 47 | 
 48 | - **P0** = MVP. Without these, there is no product. ~18 hours.
 49 | - **P1** = the hackathon target. Includes the showstopper demo and Bob integration. ~12 more hours (30h cumulative).
 50 | - **P2** = full hackathon vision. More check types, polish. ~12 more hours (42h cumulative).
 51 | - **P3** = polish and extra surfaces (GitHub Action, hooks). ~6 more hours (48h cumulative).
 52 | - **P4** = post-hackathon roadmap. The OSS-growth phase.
 53 | 
 54 | For each feature you'll see: **what it does**, **why it matters**, **user workflow**, **how it works under the hood**. P0–P2 are in full detail. P3 is concise. P4 is sketched.
 55 | 
 56 | ---
 57 | 
 58 | ## P0 — Minimum viable product (target: hours 0–18)
 59 | 
 60 | ### P0.1 — Foundation: diff parser + AST helpers
 61 | 
 62 | **What it does:** the shared library every check sits on top of. Given a git diff, returns changed files, added/removed line ranges, and added function/class definitions per file.
 63 | 
 64 | **Why it matters:** every other feature consumes this. Get it right and everything downstream is easy. Get it wrong and everything is wobbly.
 65 | 
 66 | **User workflow:** internal — users don't touch this directly.
 67 | 
 68 | **How it works:**
 69 | 1. Shell out to `git diff --unified=0 HEAD` (or a user-specified range). Parse the unified diff format into a list of `ChangedFile` records.
 70 | 2. For each Python file in the diff, parse with `ast` to get all function/class definitions and their line ranges.
 71 | 3. Cross-reference: a function is "added" if its definition lines fall inside the diff's added-line ranges.
 72 | 4. Expose three primitives: `get_changed_files()`, `get_added_functions()`, `get_added_tests()` (test functions are functions whose name starts with `test_` or whose file matches a test path pattern).
 73 | 
 74 | ### P0.2 — F1: Dead function detection (static)
 75 | 
 76 | **What it does:** finds functions added in the diff that nothing in the codebase calls.
 77 | 
 78 | **Why it matters:** the most common AI bluff is "I added `validate_jwt()`." The function exists, looks plausible, but nothing in the repo actually invokes it. Legitimate new functions almost always have at least one caller (tests, routes, other modules). Catching this is high-signal.
 79 | 
 80 | **User workflow:**
 81 | 1. User finishes an AI-assisted session where the agent claims to have implemented something.
 82 | 2. User runs `verdict run` in the repo root.
 83 | 3. For each added function, verdict reports its caller count across the repo.
 84 | 4. Functions with zero callers (and that aren't framework hooks like fixtures or exported handlers) get flagged.
 85 | 
 86 | **How it works:**
 87 | 1. From P0.1, get the list of added functions.
 88 | 2. Walk the entire repo's ASTs and look for `Call` nodes whose `.func` resolves to that name (with attribute-chain awareness: `module.func()` counts).
 89 | 3. Exclude known framework patterns: `@pytest.fixture`, `@app.route`, `@click.command`, presence in `__all__`, dunder methods, names matching `test_*`, names listed as imports in `__init__.py`.
 90 | 4. Anything left with 0 callers → flagged with a `Finding`.
 91 | 
 92 | ### P0.3 — F2: Vacuous test detection (static)
 93 | 
 94 | **What it does:** finds tests in the diff that don't actually test anything meaningful.
 95 | 
 96 | **Why it matters:** second-most-common AI bluff is "I added tests and they pass." Tests with no assertions always pass. Tests asserting `mock.called == True` after you set `mock.called = True` always pass. This catches "tests passing" being technically true but substantively empty.
 97 | 
 98 | **User workflow:** same entry as P0.2 — verdict locates added test functions, scores them, flags low-substance tests with a specific reason.
 99 | 
100 | **How it works:** heuristic checks via AST per added test function:
101 | - **Empty body:** body is `pass`, `...`, `return`, or only a docstring → flagged.
102 | - **No assertions:** zero `Assert` nodes and zero calls to `self.assertEqual` / `assertTrue` / etc. → flagged.
103 | - **Mock-only assertions:** all `Assert` nodes operate on names assigned from `Mock()`, `MagicMock()`, or `patch()` → flagged "asserts only on mocks".
104 | - **Doesn't reach new code:** test doesn't import or call any of the new functions from P0.2 → flagged "test doesn't exercise new code".
105 | 
106 | Substance score = inverse of how many checks fired.
107 | 
108 | ### P0.4 — F3: CLI + scorecard
109 | 
110 | **What it does:** ties checks together behind a single `verdict run` command. Produces human-readable terminal output + machine-readable JSON.
111 | 
112 | **Why it matters:** dev tools live or die on first-30-seconds friction. One command, no config, useful output. This is the README's first GIF.
113 | 
114 | **User workflow:**
115 | 1. `pip install verdict-ai`
116 | 2. From any git repo: `verdict run`
117 | 3. Colored terminal summary with the overall verdict + one line per finding.
118 | 4. `verdict-report.json` also written.
119 | 
120 | **How it works:**
121 | - Click or Typer for CLI.
122 | - Default: diff = `HEAD` vs working tree, all checks, print + JSON.
123 | - Flags: `--diff <range>`, `--static-only`, `--dynamic-only`, `--json`, `--fail-on suspicious|lied`.
124 | - Overall verdict: `LIED` if any finding has confidence > 0.8, `SUSPICIOUS` if any findings, `PASS` otherwise.
125 | 
126 | **At end of P0 you have:** a working CLI that catches the two most common bluffs. Already demoable. Already useful. Already releasable as OSS v0.1.
127 | 
128 | ---
129 | 
130 | ## P1 — Hackathon target (target: hours 18–30)
131 | 
132 | ### P1.1 — F4: Execution trace verification (the showstopper)
133 | 
134 | **What it does:** runs the project's test suite with execution tracing, then reports which new code from the diff was reached (or not) during the run.
135 | 
136 | **Why it matters:** the check that's impossible to fool. Agents can write code that looks right and tests that look right and pass static analysis. But if the test suite runs and the new function never actually fires, the agent was bluffing. This is the dynamic counterpart to F1 — "even when tests run, this never executes." Demos beautifully. This is also Ben's contribution to the design.
137 | 
138 | **User workflow:**
139 | 1. `verdict run --dynamic` (or it runs by default if pytest is detected).
140 | 2. verdict invokes the project's test suite (`pytest`) with verdict's tracer plugin attached.
141 | 3. As tests run, every function entry in diff'd files is recorded.
142 | 4. Scorecard reports: `5 new functions, 2 executed during tests, 3 never reached`.
143 | 
144 | **How it works:**
145 | 1. Build a set of `(file, function_name, line_range)` tuples for added functions from P0.1.
146 | 2. Hook `sys.settrace` (or `sys.monitoring` on Python 3.12+) via a small pytest plugin.
147 | 3. The trace callback fires on every function entry; check if `(co_filename, co_name)` matches the "new functions" set.
148 | 4. After pytest finishes, compute `new_functions - executed_functions`. Anything left is "defined but never executed."
149 | 5. Bonus output: per-function call count.
150 | 
151 | ### P1.2 — F5: MCP server for Bob
152 | 
153 | **What it does:** exposes verdict's checks as MCP tools so Bob (or any MCP-aware agent) can call them as a self-check before claiming "done."
154 | 
155 | **Why it matters:** the long-term play. If Bob calls `verdict.check_diff` mid-session, Bob catches its own lies before the human ever sees them. This also directly satisfies the hackathon's "clearly demonstrate how Bob is used" criterion — we plug into Bob's actual extension surface as IBM designed it.
156 | 
157 | **User workflow:**
158 | 1. `verdict mcp install` writes the right config into Bob's MCP config.
159 | 2. In a Bob session: user prompts, Bob makes changes.
160 | 3. Before Bob says "done," it calls `verdict.check_diff` via MCP. verdict returns the scorecard.
161 | 4. If `LIED`, Bob sees its own bluff, self-corrects, retries. If `PASS`, Bob reports completion confidently.
162 | 
163 | **How it works:**
164 | - Use the official Python MCP SDK to expose check functions as tools.
165 | - Tools: `check_diff(diff_range="HEAD")`, `check_static(diff_range="HEAD")`, `trace_test_run(test_command="pytest")`.
166 | - Each returns the same JSON schema as the CLI's report.
167 | - Run as local stdio MCP server.
168 | 
169 | ### P1.3 — The Bob loop demo
170 | 
171 | **What it does:** the demo we hand the judges. Not a feature per se but a scripted scenario that uses everything in P0 + P1.
172 | 
173 | **Why it matters:** this is the moment that wins the hackathon. The pitch line: *"Bob just learned how to not lie to itself."*
174 | 
175 | **Demo script:**
176 | 1. Open a small repo in Bob.
177 | 2. Prompt Bob: "add JWT validation to the auth module and write tests."
178 | 3. Bob makes changes, says "done, tests passing."
179 | 4. Run `verdict run` from terminal. Scorecard exposes lies (dead function, vacuous test, never-executed function).
180 | 5. Now show the same loop with verdict registered as an MCP server.
181 | 6. Re-prompt Bob. Bob makes changes, calls `verdict.check_diff` *itself*, sees its bluff, self-corrects, retries.
182 | 7. Final verdict: `PASS`. Bob legitimately did the work.
183 | 
184 | **At end of P1 you have:** a hackathon-winning demo. The showstopper dynamic check + the self-correcting Bob loop. This is the natural stopping point if you're behind.
185 | 
186 | ---
187 | 
188 | ## P2 — Full hackathon vision (target: hours 30–42)
189 | 
190 | ### P2.1 — F6: Hallucinated API call detection
191 | 
192 | **What it does:** flags calls in the diff to methods/attributes that don't exist on the objects they're called on.
193 | 
194 | **Why it matters:** agents invent APIs that don't exist (`requests.get_json()` instead of `.json()`, `pd.read_excel(parse_dates=True)` when that arg was renamed two versions ago). Static type checkers can catch some of this but most projects don't enforce strict typing.
195 | 
196 | **User workflow:** runs as part of `verdict run`. Findings include the line, the called expression, and "no such attribute on `<type>`".
197 | 
198 | **How it works:**
199 | 1. From P0.1, get all `Call` and `Attribute` nodes in the diff.
200 | 2. For each, attempt to resolve the type of the object via local AST analysis + Jedi or `inspect` for installed packages.
201 | 3. If the attribute doesn't exist on the resolved type, flag.
202 | 4. Confidence is low for dynamic types (`Any`, `object`) and high for concrete types from typed libraries. Don't fire if confidence is low.
203 | 
204 | ### P2.2 — F7: Suppressed exception detection
205 | 
206 | **What it does:** flags `try/except` blocks added in the diff whose `except` body is `pass`, `...`, or a bare logger call — i.e., the feature was wrapped in a "swallow everything" block.
207 | 
208 | **Why it matters:** classic agent bluff is wrapping the actual feature in `try: ... except: pass`. Tests pass because nothing ever raises. Feature doesn't work because every error is silently eaten.
209 | 
210 | **User workflow:** part of `verdict run`. Findings point at the line and the exception type being suppressed.
211 | 
212 | **How it works:** AST walk over added code. For each `Try` node, if any `ExceptHandler` body is `[Pass]`, `[Expr(Constant(...))]`, or only a single `Expr` that's a logger call — flag. Confidence drops if it's a narrow exception type (`except KeyError`) vs broad (`except Exception` / `except:`).
213 | 
214 | ### P2.3 — F8: Phantom file detection
215 | 
216 | **What it does:** flags files mentioned in the agent's transcript or the diff metadata that don't actually exist on disk.
217 | 
218 | **Why it matters:** rare but devastating. Agent says "created `src/auth/jwt.py`" — file isn't there. Easy check, high signal.
219 | 
220 | **User workflow:** part of `verdict run`. Optionally takes a transcript file via `--transcript path/to/log.txt` to extract claimed-created paths from agent output.
221 | 
222 | **How it works:**
223 | 1. From the diff: list of "added" file paths (Git's perspective).
224 | 2. Check each path exists with `os.path.exists`. If a path is in the diff as `+++ b/path` but doesn't exist on disk, flag (rare but catches git-index corruption cases).
225 | 3. If a transcript is provided: regex out paths of the form `created file: <path>` / similar; flag any that don't exist.
226 | 
227 | ### P2.4 — Scorecard polish
228 | 
229 | **What it does:** better human-readable output and a stable JSON schema.
230 | 
231 | **Why it matters:** scorecard is what people screenshot. It needs to look sharp.
232 | 
233 | **Workflow improvements:**
234 | - Color-coded terminal output (rich library): red for `LIED`, yellow for `SUSPICIOUS`, green for `PASS`.
235 | - Markdown report mode (`--format md`) for pasting into PR comments.
236 | - Stable, versioned JSON schema in `verdict/schema/v1.json`.
237 | - Findings grouped by file with line-by-line annotations.
238 | 
239 | ### P2.5 — Bob Custom Mode + Slash Command
240 | 
241 | **What it does:** ships a verdict-flavored Custom Mode for Bob (config file users drop in) + a `/verify` slash command.
242 | 
243 | **Why it matters:** second integration surface into Bob. Even users who don't set up MCP can drop the Custom Mode into their Bob config and get one-click verification. Hackathon points for using more of Bob's extension surface.
244 | 
245 | **Workflow:**
246 | 1. `verdict bob-mode install` writes the Custom Mode definition into Bob's config.
247 | 2. In Bob, user switches to "Verifier" mode after a coding session.
248 | 3. Bob (in Verifier mode) runs verdict internally and reports findings inline in chat.
249 | 
250 | **How it works:**
251 | - A Custom Mode definition is a YAML/JSON file (per Bob docs) that pins a role + a set of allowed tools.
252 | - The Verifier mode has access to: file read, terminal run, and the verdict MCP tools from P1.2.
253 | - The system prompt for the mode says: "You are an auditor. Run `verdict run`. Report findings literally. Do not write code."
254 | 
255 | **At end of P2 you have:** a polished, multi-check tool with three Bob integration surfaces (MCP, Custom Mode, slash command). Ready to submit and with a strong shot at winning.
256 | 
257 | ---
258 | 
259 | ## P3 — Polish and extra surfaces (target: hours 42–48)
260 | 
261 | ### P3.1 — GitHub Action wrapper
262 | 
263 | A single `action.yml` plus a Dockerfile that wraps the CLI. PRs get auto-audited; verdict score posted as a PR comment; configurable failure threshold. Workflow is dead simple because the CLI already exists — mostly packaging. *~1 hour.*
264 | 
265 | ### P3.2 — pre-commit hook
266 | 
267 | A `.pre-commit-hooks.yaml` entry so users can add verdict to their pre-commit config. Runs `verdict run --fail-on lied` against staged changes. *~30 minutes.*
268 | 
269 | ### P3.3 — F9: Coverage delta on new lines
270 | 
271 | After the trace run from P1.1, also compute line-level coverage on added lines. Findings include "of 47 new lines, 12 (25%) were exercised by tests." Lower threshold → suspicious. *~2 hours.*
272 | 
273 | ### P3.4 — F10: Bob Skill packaging
274 | 
275 | Bob has a "Skills" feature analogous to Claude skills. Package verdict as a Bob Skill with a `SKILL.md` that tells Bob when to invoke verdict (e.g., "after claiming task complete, run verdict on the diff"). *~1 hour.*
276 | 
277 | ### P3.5 — Fixture repo + demo GIF + README
278 | 
279 | The README is the most important file in OSS-land. A good README has: one-line pitch, animated GIF of the demo, install instructions, "how it works in 30 seconds" diagram, link to the hackathon submission. Spend real time here. *~2 hours.*
280 | 
281 | **At end of P3 you have:** a complete v0.1 OSS release. README, CI, hooks, four Bob integration surfaces, six check types. This is what gets stars on launch day.
282 | 
283 | ---
284 | 
285 | ## P4 — Post-hackathon roadmap (the OSS-growth phase)
286 | 
287 | Listed without full detail; these are what verdict becomes if it gets traction:
288 | 
289 | - **F11 — TS/JS support** via tree-sitter + Node tracing (CRITICAL for stars; half the AI-codegen user base is JS).
290 | - **F12 — Go and Java support** (Bob is positioned as Java-first per IBM's marketing — strong fit).
291 | - **F13 — Task-vs-diff alignment** using an LLM to compare the original task description against the actual diff for semantic match (when the task text is available).
292 | - **F14 — Team scorecard / dashboard** — track which agents lie most, which devs override the most findings, drift over time. This is the SaaS hook if monetization ever matters.
293 | - **F15 — Custom check rules** — let teams write their own checks in Python and register them as plugins.
294 | - **F16 — Drift detection** — alert when an agent's lie rate suddenly increases (a sign the underlying model changed silently).
295 | - **F17 — VS Code extension** — inline verdict findings in the editor, not just the terminal.
296 | - **F18 — Self-improvement loop** — when humans override a finding (mark it as a false positive), use that signal to tune the heuristics.
297 | - **F19 — Verdict for verdict** — recursive joke that should ship at v1.0. Run verdict on the verdict repo itself.
298 | 
299 | ---
300 | 
301 | ## 4. Scorecard output (the demo asset)
302 | 
303 | ```
304 | verdict v0.1.0 — auditing HEAD vs working tree
305 | 
306 |   ✓ 12 files changed
307 |   ✓ 5 new functions detected
308 |   ✓ 3 new test functions detected
309 | 
310 | Static checks:
311 |   ✗ DEAD FUNCTION       src/auth.py:42      validate_jwt() has 0 callers
312 |   ✗ VACUOUS TEST        tests/test_auth.py:18  test_validate_jwt — no assertions
313 |   ✓ no hallucinated imports detected
314 |   ✓ no suppressed exceptions detected
315 | 
316 | Dynamic checks:
317 |   ✗ NEVER EXECUTED      src/auth.py:42      validate_jwt() not reached during pytest
318 |                                             (test_validate_jwt ran but didn't call it)
319 | 
320 | Verdict: LIED
321 | 
322 | The agent claims to have implemented JWT validation, but:
323 |   - the function it added is never called from anywhere
324 |   - the test it added doesn't actually call the function
325 |   - the test passes because it does nothing
326 | ```
327 | 
328 | ---
329 | 
330 | ## 5. Architecture
331 | 
332 | ```
333 | verdict/
334 | ├── pyproject.toml
335 | ├── README.md
336 | ├── verdict/
337 | │   ├── __init__.py
338 | │   ├── cli.py                  # P0.4 — Click/Typer entry point
339 | │   ├── diff.py                 # P0.1 — git diff parsing
340 | │   ├── ast_utils.py            # P0.1 — added-function extraction
341 | │   ├── checks/
342 | │   │   ├── __init__.py
343 | │   │   ├── dead_functions.py   # P0.2
344 | │   │   ├── vacuous_tests.py    # P0.3
345 | │   │   ├── trace.py            # P1.1 — pytest plugin + sys.settrace
346 | │   │   ├── hallucinated_api.py # P2.1
347 | │   │   ├── suppressed_exc.py   # P2.2
348 | │   │   └── phantom_files.py    # P2.3
349 | │   ├── report.py               # P0.4 + P2.4 — scorecard formatting
350 | │   ├── mcp_server.py           # P1.2
351 | │   └── bob_integration/
352 | │       ├── custom_mode.yaml    # P2.5
353 | │       └── skill/              # P3.4
354 | └── tests/
355 |     └── fixtures/
356 |         ├── lying_repo/         # canonical "agent lied" example
357 |         └── honest_repo/        # canonical "PASS" example
358 | ```
359 | 
360 | Data shapes:
361 | - `ChangedFile = {path: str, added_lines: list[int], removed_lines: list[int]}`
362 | - `AddedFunction = {file: str, name: str, line: int, end_line: int, is_test: bool, decorators: list[str]}`
363 | - `Finding = {kind: str, file: str, line: int, message: str, confidence: float}`
364 | - `Scorecard = {verdict: Literal["PASS"|"SUSPICIOUS"|"LIED"], findings: list[Finding], summary: dict}`
365 | 
366 | **Important — interfaces ship to `main` before any implementation.** These shapes live in `verdict/types.py` as `TypedDict`s and `Protocol`s and must be pushed to `main` within the first hour of the project. Every check, the CLI, and the MCP server all code against the interface — not against each other's implementations. This is what unblocks parallel work across the team. See `TEAM.md` §4 for the exact `types.py` contents and the workflow around it.
367 | 
368 | External deps (minimal):
369 | - `click` or `typer` (CLI)
370 | - standard library `ast`, `subprocess` (git shell-out)
371 | - `pytest` is invoked but user-side, not ours
372 | - `rich` (P2.4 only, for colored output)
373 | - `mcp` Python SDK (P1.2 only)
374 | - `jedi` (P2.1 only, for type resolution)
375 | 
376 | ---
377 | 
378 | ## 6. Working with Bob on this build
379 | 
380 | Practical notes from someone about to be ironically reliant on AI agents to ship a tool that catches AI agents lying:
381 | 
382 | **Don't paste this whole doc into a single prompt.** Work feature by feature. The chain that works:
383 | 1. Paste the feature's section + the architecture summary.
384 | 2. Ask for a *technical plan* first — files, function signatures, key data shapes, one happy-path example.
385 | 3. Review the plan in 60 seconds.
386 | 4. Then ask for code, file by file.
387 | 5. Run partial verdict on the agent's own output as soon as P0.2 works. Recursive joke; also catches problems.
388 | 
389 | The data shapes in the Architecture section are written so an agent can adopt them verbatim. The priority order is also a build order — feed the agent priorities in sequence, not all at once.
390 | 
391 | **Failure mode to watch for:** the agent confidently saying "implemented and tested ✓" when it's not. Which is, of course, the entire reason this product exists. The recursion isn't funny if you don't notice.
392 | 
393 | ---
394 | 
395 | ## 7. Build a fixture repo first (30 minutes well spent)
396 | 
397 | Before writing any verdict code: spend 30 minutes making a tiny "lying agent" example repo. Three or four files. One `validate_jwt()` that's never called. One test that's `assert True`. One try/except that swallows the actual feature. This becomes:
398 | 
399 | 1. Your test fixture (how do you know dead-function-detection works? You run it on this repo).
400 | 2. Your demo asset (this is what you show Bob; this is what verdict catches; this is what's in the GIF).
401 | 3. The example in your README.
402 | 
403 | Highest-leverage 30 minutes of the whole hackathon. Do it before P0.1.
</content>
</file>
<file><path>TEAM.md</path>
<content lines="1-327">
  1 | # TEAM.md — how we work together on verdict
  2 | 
  3 | Quick context: 4 people. 48 hours. None of us have worked in a team before. This doc is the working agreement. Read it once at hour 0, refer back as needed.
  4 | 
  5 | ---
  6 | 
  7 | ## 1. The roles
  8 | 
  9 | The work splits into four domains. Each person owns their domain end-to-end. Domains are scoped so that work happens mostly in parallel — nobody is waiting on anyone else for very long.
 10 | 
 11 | ### Ben — Bob integration & presentation
 12 | 
 13 | Ben owns every surface where verdict touches Bob, plus everything the judges and OSS audience actually see. This is the part of the project with the most taste calls — what the demo looks like, how the Bob loop reads on screen, how the Custom Mode prompts sound, what the README's hero section feels like.
 14 | 
 15 | - **P1.2** MCP server for Bob
 16 | - **P2.5** Bob Custom Mode + slash command
 17 | - **P3.4** Bob Skill packaging
 18 | - **P1.3** The Bob loop demo — script it, run it, record it, polish it
 19 | - **P3.5** README + demo GIF + hackathon submission writeup
 20 | 
 21 | ### Neel — Core engine
 22 | 
 23 | Neel owns the internal spine of verdict — the foundation everyone else's checks plug into, and the dynamic tracer that makes the demo a showstopper. Heavy planning work with crisp specs.
 24 | 
 25 | - **P0.1** Foundation: diff parser + AST helpers
 26 | - **P0.4** CLI + scorecard plumbing
 27 | - **P1.1** Execution tracer (the showstopper dynamic check)
 28 | - **P2.4** Scorecard polish (colors, markdown output, stable JSON schema)
 29 | 
 30 | ### Jacob — Audit checks (family A)
 31 | 
 32 | Jacob owns the fixture repo (which unblocks everyone else's local testing) plus a coherent family of static analysis checks. Also owns the CI integration.
 33 | 
 34 | - **fixture-repo build** — done early so everyone can test locally
 35 | - **P0.2** Dead function detection
 36 | - **P2.1** Hallucinated API call detection
 37 | - **P2.2** Suppressed exception detection
 38 | - **P3.1** GitHub Action wrapper
 39 | 
 40 | ### Alexie — Audit checks (family B)
 41 | 
 42 | Alexie owns the other family of checks plus the lighter integration surfaces. Also keeps the fixture's ground-truth file in sync as checks evolve.
 43 | 
 44 | - **P0.3** Vacuous test detection
 45 | - **P2.3** Phantom file detection
 46 | - **P3.2** pre-commit hook
 47 | - **P3.3** Coverage delta on new lines
 48 | - Fixture repo maintenance (keep `EXPECTED_FINDINGS.md` accurate)
 49 | 
 50 | **If anyone finishes early:** pull the next-most-valuable item from the spec, post in the channel so others know.
 51 | 
 52 | ---
 53 | 
 54 | ## 2. Sync schedule
 55 | 
 56 | Three syncs a day. 10 minutes max each. Voice on Discord. Everyone says:
 57 | 
 58 | 1. What I shipped since last sync.
 59 | 2. What I'm working on now.
 60 | 3. What's blocking me.
 61 | 
 62 | Schedule (assuming an 11am start Friday):
 63 | 
 64 | | When | Time | What |
 65 | |---|---|---|
 66 | | Hour 0 | 11am Fri | Kickoff: read spec, confirm roles, types file pushed (see §4) |
 67 | | Hour 6 | 5pm Fri | Sync 1: P0 in progress check |
 68 | | Hour 12 | 11pm Fri | Sync 2: P0 must be close to done |
 69 | | Hour 18 | 5am Sat | Async only (sleep). Anyone awake posts a status. |
 70 | | Hour 24 | 11am Sat | Sync 3: P1 in progress check |
 71 | | Hour 30 | 5pm Sat | Sync 4: P1 demo must be working |
 72 | | Hour 36 | 11pm Sat | Sync 5: P2 in progress |
 73 | | Hour 42 | 5am Sun | Async only. |
 74 | | Hour 46 | 9am Sun | Final sync: integration, submission |
 75 | | Hour 48 | 11am Sun | Submit. |
 76 | 
 77 | Sleep is not optional. Stagger sleep — at least one person should be awake-ish during the 18–24 and 42–46 windows, but no one pulls a true all-nighter. Tired people write bugs that look like agent lies, which is exactly what we don't need.
 78 | 
 79 | ---
 80 | 
 81 | ## 3. Communication norms
 82 | 
 83 | - **One Discord channel** for the team. All real-time talk happens there.
 84 | - **One Discord voice channel** open during syncs.
 85 | - **Asynchronous default.** Don't expect instant replies. If something is urgent, say `@blocking` in the channel and tag the person.
 86 | - **Status emoji on your messages:** 🚧 working, ✅ done, ❓ need help, 🐛 found a bug, 🔥 blocking everyone.
 87 | - **Don't DM.** Everything in the channel so others can search later. If something is sensitive, that's an in-person convo after the hackathon.
 88 | - **No silent struggle.** If you're stuck for >30 min, post `❓`. Two hours of silent struggle is two hours we don't get back.
 89 | - **Disagreements:** present both views in the channel, pick the simpler option that unblocks the most people, move on. If it's a 50/50 call, default to the option that touches less code.
 90 | 
 91 | ---
 92 | 
 93 | ## 4. Git workflow
 94 | 
 95 | ### Repo & branches
 96 | 
 97 | - One GitHub repo: `verdict-ai/verdict` (or whatever we name it).
 98 | - `main` is sacred. It always works. CI runs on every PR.
 99 | - One branch per feature: `feat/<priority-id>-<short-name>`. Examples:
100 |   - `feat/p0.1-foundation`
101 |   - `feat/p0.2-dead-functions`
102 |   - `feat/p1.1-execution-tracer`
103 | - Branch off `main`, push early, open a Draft PR within the first hour of work so others can see what you're doing.
104 | 
105 | ### Interfaces published at hour 0
106 | 
107 | Before anyone writes implementation code, the typed interfaces get pushed to `main`. This unblocks parallel work — everyone codes against the interface, not the implementation. Neel publishes `verdict/types.py` within the first hour.
108 | 
109 | ```python
110 | # verdict/types.py — on main by hour 1
111 | from typing import Literal, Protocol, TypedDict
112 | 
113 | 
114 | class ChangedFile(TypedDict):
115 |     path: str
116 |     added_lines: list[int]
117 |     removed_lines: list[int]
118 | 
119 | 
120 | class AddedFunction(TypedDict):
121 |     file: str
122 |     name: str
123 |     line: int
124 |     end_line: int
125 |     is_test: bool
126 |     decorators: list[str]
127 | 
128 | 
129 | class Finding(TypedDict):
130 |     kind: str   # e.g. "dead_function", "vacuous_test"
131 |     file: str
132 |     line: int
133 |     message: str
134 |     confidence: float
135 | 
136 | 
137 | VerdictLevel = Literal["PASS", "SUSPICIOUS", "LIED"]
138 | 
139 | 
140 | class Scorecard(TypedDict):
141 |     verdict: VerdictLevel
142 |     findings: list[Finding]
143 |     summary: dict
144 | 
145 | 
146 | class Check(Protocol):
147 |     """All checks implement this interface."""
148 |     name: str
149 |     def run(self, diff_root: str, added_functions: list[AddedFunction]) -> list[Finding]: ...
150 | ```
151 | 
152 | If you need to extend a shape, ping the channel. Don't modify these silently — everyone is coding against them.
153 | 
154 | ### Pull requests
155 | 
156 | - Title format: `[P0.2] dead function detection — heuristics for caller search`
157 | - Description template (also lives in `.github/PULL_REQUEST_TEMPLATE.md`):
158 |   ```
159 |   ## What
160 |   One-sentence summary.
161 | 
162 |   ## Priority section
163 |   P0.2 from verdict-spec.md.
164 | 
165 |   ## How I tested
166 |   - Ran on fixtures/lying_repo: found N findings as expected
167 |     (see EXPECTED_FINDINGS.md row X)
168 |   - Ran on fixtures/honest_repo: returned PASS
169 | 
170 |   ## Anything I'm unsure about
171 |   Optional.
172 |   ```
173 | - **Review pairs:** Ben ↔ Neel review each other's PRs. Jacob ↔ Alexie review each other's PRs. Cross-pair review is welcome but not required.
174 | - One approval is enough. Don't sit on green PRs.
175 | - Squash-merge to `main`.
176 | 
177 | ### Conflicts
178 | 
179 | - Rebase, don't merge: `git fetch origin main && git rebase origin/main`.
180 | - If you can't resolve in 10 minutes, post in the channel — whoever's free pairs with you.
181 | 
182 | ---
183 | 
184 | ## 5. Definition of done
185 | 
186 | A feature is "done" when **all** of these are true:
187 | 
188 | 1. The code is on `main` (merged PR).
189 | 2. It passes its own tests (you wrote unit tests for the check).
190 | 3. It produces the expected output on `fixtures/lying_repo` (matching the relevant rows in `EXPECTED_FINDINGS.md`).
191 | 4. It produces `PASS` (no false positives) on `fixtures/honest_repo`.
192 | 5. It's wired into the CLI — `verdict run` actually invokes it.
193 | 6. The README has at least one sentence about it (post in the channel when ready — README updates as features land).
194 | 
195 | If any of those is false, the feature is not done. "Done on my machine" is not done.
196 | 
197 | ---
198 | 
199 | ## 6. Code style & conventions
200 | 
201 | - **Python 3.10+** (use modern syntax: `list[X]`, `X | None`, `match` where it fits).
202 | - **Formatter:** `ruff format` (faster than black, opinions identical).
203 | - **Linter:** `ruff check`. Run before pushing.
204 | - **Type hints:** required on all public functions. `mypy --strict` is the goal but don't let it block you.
205 | - **Imports:** absolute (`from verdict.types import Finding`), never relative.
206 | - **Naming:** snake_case for functions/variables, PascalCase for classes, SCREAMING_SNAKE for constants. File names lowercase with underscores.
207 | - **Docstrings:** one-line summary on every public function. Triple-quoted, imperative mood ("Return X" not "Returns X").
208 | - **No mystery dependencies.** Want to add a package? Post in the channel — anyone gives a quick yes/no based on whether it's reasonable.
209 | 
210 | ### Pre-commit (everyone installs this in hour 0)
211 | 
212 | ```bash
213 | pip install pre-commit
214 | pre-commit install
215 | ```
216 | 
217 | Hooks (in `.pre-commit-config.yaml`):
218 | - ruff format
219 | - ruff check (with fix)
220 | - trailing whitespace
221 | - end-of-file fixer
222 | 
223 | This catches dumb stuff before it hits CI.
224 | 
225 | ---
226 | 
227 | ## 7. Integration plan — how the work fits together
228 | 
229 | This is the bit teams usually mess up. Here's how the pieces hook in.
230 | 
231 | ### Hour 0–6 (foundation phase)
232 | 
233 | ```
234 | Neel → P0.1 foundation (verdict/diff.py, verdict/ast_utils.py)
235 |        ↓ publishes verdict/types.py within hour 1
236 | Ben → reads spec, drafts MCP server design, sets up demo repo
237 | Jacob → fixture-repo build (lying_repo + honest_repo)
238 | Alexie → reads spec, writes empty stub for P0.3, sets up local env
239 | ```
240 | 
241 | End of hour 6: foundation merged. Fixture exists. Everyone can run `pytest` on the fixtures locally.
242 | 
243 | ### Hour 6–18 (parallel checks phase)
244 | 
245 | ```
246 | Neel → P0.4 CLI + scorecard plumbing — wire up checks as they land
247 | Ben → starts P1.2 MCP server scaffolding against the CLI's JSON output
248 | Jacob → P0.2 dead function detection
249 | Alexie → P0.3 vacuous test detection
250 | ```
251 | 
252 | Each check follows the same shape: implements the `Check` protocol from `verdict/types.py`, takes `(diff_root, added_functions)`, returns `list[Finding]`. The CLI imports all checks and runs them in sequence.
253 | 
254 | End of hour 18: all P0 checks merged. `verdict run` on `fixtures/lying_repo` produces a real scorecard with multiple findings.
255 | 
256 | ### Hour 18–30 (P1 phase)
257 | 
258 | ```
259 | Neel → P1.1 execution tracer (the showstopper)
260 | Ben → P1.2 MCP server finishes, then P1.3 Bob loop demo
261 | Jacob → P2.1 hallucinated API detection (gets ahead on P2)
262 | Alexie → P2.3 phantom file detection (small, quick win)
263 | ```
264 | 
265 | The MCP server doesn't need new checks — it wraps the CLI. Ben builds it in parallel with the tracer.
266 | 
267 | End of hour 30: Bob loop demo working end-to-end. **This is the hackathon submission's minimum viable state.** If we stop here we still win something.
268 | 
269 | ### Hour 30–42 (P2 phase — depth)
270 | 
271 | Everyone executes their P2 items. Ben starts evolving the README. Neel starts P2.4 scorecard polish so the demo looks sharp.
272 | 
273 | ### Hour 42–48 (P3 + submission)
274 | 
275 | Everyone executes their P3 items in parallel. Ben finalizes the README, records the demo GIF, writes the hackathon submission. Final sync at hour 46. Submit by hour 48.
276 | 
277 | ---
278 | 
279 | ## 8. Emergency protocol — what if we're behind
280 | 
281 | Triggers and actions:
282 | 
283 | **At hour 12: P0 isn't done.**
284 | - Pause Jacob and Alexie on later checks; pair up on whatever's stuck in P0.1.
285 | - Drop one of the P0 checks if forced. Keep P0.2 (dead-function) because it's the most common lie pattern. Cut P0.3 (vacuous tests) only if absolutely necessary.
286 | 
287 | **At hour 24: P1.1 (tracer) isn't working.**
288 | - Dynamic check is the hardest. Acceptable fallback: ship a stub dynamic check that just runs pytest and reports coverage delta on diff lines (no `sys.settrace`).
289 | - Demo pivots to "two static checks + coverage delta" — less dramatic but still works.
290 | 
291 | **At hour 36: MCP server isn't working.**
292 | - Cut P1.2 entirely. Demo verdict as a CLI Bob calls via shell, not via MCP.
293 | - We lose one hackathon point on "Application of Technology" but the demo is still strong.
294 | 
295 | **At hour 44: behind on P2/P3.**
296 | - Cut everything below the line. Final state: P0 + P1 only. Still a winning project.
297 | 
298 | **Universal rule:** never cut README/demo polish for more features. A great demo of 3 features beats a janky demo of 8. The demo and submission are Ben's domain — those stay intact no matter what gets cut.
299 | 
300 | ---
301 | 
302 | ## 9. Decision-making
303 | 
304 | - **Technical disagreements:** present both views in the channel, pick the simpler option, move on. If it's a 50/50 call, default to whatever touches less code or unblocks the most people.
305 | - **Scope questions ("should we add X?"):** default no. The spec is the spec. New items require all-four agreement.
306 | - **Naming questions:** lowest-stakes thing in the world. Whoever wrote the code picks. Move on.
307 | - **"Is this a bug?":** if it produces the wrong output on `fixtures/lying_repo`, yes. Otherwise, write it up as an issue and continue.
308 | 
309 | ---
310 | 
311 | ## 10. After the hackathon
312 | 
313 | Submit by hour 48. Then:
314 | 
315 | - One team retro on Monday — what worked, what didn't.
316 | - Decide whether anyone wants to keep building. The OSS-growth phase (P4 in the spec) is real and worth doing if any of us has the energy.
317 | - If we keep going: TS/JS support is the single highest-leverage next move for stars. Don't do anything else first.
318 | 
319 | ---
320 | 
321 | ## 11. The actual goal
322 | 
323 | Stars on GitHub. Not just hackathon prize.
324 | 
325 | The hackathon is the forcing function. The real win is: when this is on Hacker News on Monday, do people on HN go "yes, I want this"? That's the test for every decision.
326 | 
327 | If a feature wouldn't survive an HN front-page reading, cut it. If a feature would make someone hit star, ship it.
</content>
</file>
</files>
<environment_details>
# VSCode Visible Files
verdict\types.py

# VSCode Open Tabs
verdict/types.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T17:30:50.193Z
User time zone: America/Toronto, UTC-4:00

# Current Cost
$0.20

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>plan</slug>
<name>📝 Plan</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Check for existing AGENTS.md files and AI assistant rules | Completed |
| 2 | Identify project stack and structure | In Progress |
| 3 | Extract build/test/lint commands | Pending |
| 4 | Analyze code patterns and conventions | Pending |
| 5 | Document non-obvious project-specific information | Pending |
| 6 | Create/update AGENTS.md files | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<read_file>
<args>
  <file>
    <path>verdict/__init__.py</path>
  </file>
  <file>
    <path>verdict/types.py</path>
  </file>
  <file>
    <path>.gitignore</path>
  </file>
</args>
</read_file>

---

**User:**

[read_file for 'verdict/__init__.py', 'verdict/types.py', '.gitignore'] Result:
<files>
<file><path>verdict/__init__.py</path>
<content/><notice>File is empty</notice>
</file>
<file><path>verdict/types.py</path>
<content lines="1-50">
 1 | """Shared type contracts for verdict.
 2 | 
 3 | Every check, the CLI, and the MCP server code against these interfaces so the
 4 | four-person team can build in parallel without blocking on each other's
 5 | implementations. Do not modify these shapes silently; discuss in Discord first.
 6 | """
 7 | 
 8 | from typing import Literal, Protocol, TypedDict
 9 | 
10 | 
11 | class ChangedFile(TypedDict):
12 |     path: str
13 |     added_lines: list[int]
14 |     removed_lines: list[int]
15 | 
16 | 
17 | class AddedFunction(TypedDict):
18 |     file: str
19 |     name: str
20 |     line: int
21 |     end_line: int
22 |     is_test: bool
23 |     decorators: list[str]
24 | 
25 | 
26 | class Finding(TypedDict):
27 |     kind: str  # e.g. "dead_function", "vacuous_test"
28 |     file: str
29 |     line: int
30 |     message: str
31 |     confidence: float
32 | 
33 | 
34 | VerdictLevel = Literal["PASS", "SUSPICIOUS", "LIED"]
35 | 
36 | 
37 | class Scorecard(TypedDict):
38 |     verdict: VerdictLevel
39 |     findings: list[Finding]
40 |     summary: dict
41 | 
42 | 
43 | class Check(Protocol):
44 |     """All checks implement this interface."""
45 | 
46 |     name: str
47 | 
48 |     def run(
49 |         self, diff_root: str, added_functions: list[AddedFunction]
50 |     ) -> list[Finding]: ...
</content>
</file>
<file><path>.gitignore</path>
<content lines="1-45">
 1 | # Local handoff log, never push (per TEAM workflow)
 2 | onboarding.md
 3 | 
 4 | # Byte-compiled / optimized
 5 | __pycache__/
 6 | *.py[cod]
 7 | *$py.class
 8 | *.so
 9 | 
10 | # Distribution / packaging
11 | .Python
12 | build/
13 | dist/
14 | *.egg-info/
15 | *.egg
16 | .eggs/
17 | wheels/
18 | pip-wheel-metadata/
19 | share/python-wheels/
20 | 
21 | # Virtual envs
22 | .venv/
23 | venv/
24 | env/
25 | ENV/
26 | 
27 | # Tooling caches
28 | .pytest_cache/
29 | .mypy_cache/
30 | .ruff_cache/
31 | .tox/
32 | .nox/
33 | .coverage
34 | .coverage.*
35 | htmlcov/
36 | coverage.xml
37 | 
38 | # verdict's own output (don't commit reports generated during dev)
39 | verdict-report.json
40 | 
41 | # Editor / OS
42 | .vscode/
43 | .idea/
44 | *.swp
45 | .DS_Store
</content>
</file>
</files>
<environment_details>
# VSCode Visible Files
verdict\types.py

# VSCode Open Tabs
verdict/types.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T17:30:57.861Z
User time zone: America/Toronto, UTC-4:00

# Current Cost
$0.28

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>plan</slug>
<name>📝 Plan</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Check for existing AGENTS.md files and AI assistant rules | Completed |
| 2 | Identify project stack and structure | In Progress |
| 3 | Extract build/test/lint commands | Pending |
| 4 | Analyze code patterns and conventions | Pending |
| 5 | Document non-obvious project-specific information | Pending |
| 6 | Create/update AGENTS.md files | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<update_todo_list>
<todos>
[x] Check for existing AGENTS.md files and AI assistant rules
[x] Identify project stack and structure
[x] Extract build/test/lint commands
[-] Analyze code patterns and conventions
[ ] Document non-obvious project-specific information
[ ] Create/update AGENTS.md files
</todos>
</update_todo_list>

---

**User:**

[update_todo_list] Result:
Todo list updated successfully.
<environment_details>
# VSCode Visible Files
verdict\types.py

# VSCode Open Tabs
verdict/types.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T17:31:08.147Z
User time zone: America/Toronto, UTC-4:00

# Current Cost
$0.37

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>plan</slug>
<name>📝 Plan</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Check for existing AGENTS.md files and AI assistant rules | Completed |
| 2 | Identify project stack and structure | Completed |
| 3 | Extract build/test/lint commands | Completed |
| 4 | Analyze code patterns and conventions | In Progress |
| 5 | Document non-obvious project-specific information | Pending |
| 6 | Create/update AGENTS.md files | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<list_files>
<path>.</path>
<recursive>false</recursive>
</list_files>

---

**User:**

[list_files for '.'] Result:
.gitignore
pyproject.toml
README.md
TEAM.md
verdict-spec.md
verdict/
<environment_details>
# VSCode Visible Files
verdict\types.py

# VSCode Open Tabs
verdict/types.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T17:31:14.335Z
User time zone: America/Toronto, UTC-4:00

# Current Cost
$0.45

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>plan</slug>
<name>📝 Plan</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Check for existing AGENTS.md files and AI assistant rules | Completed |
| 2 | Identify project stack and structure | Completed |
| 3 | Extract build/test/lint commands | Completed |
| 4 | Analyze code patterns and conventions | In Progress |
| 5 | Document non-obvious project-specific information | Pending |
| 6 | Create/update AGENTS.md files | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<update_todo_list>
<todos>
[x] Check for existing AGENTS.md files and AI assistant rules
[x] Identify project stack and structure
[x] Extract build/test/lint commands
[x] Analyze code patterns and conventions
[-] Document non-obvious project-specific information
[ ] Create/update AGENTS.md files
</todos>
</update_todo_list>

---

**User:**

[update_todo_list] Result:
Todo list updated successfully.
<environment_details>
# VSCode Visible Files
verdict\types.py

# VSCode Open Tabs
verdict/types.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T17:31:20.556Z
User time zone: America/Toronto, UTC-4:00

# Current Cost
$0.54

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>plan</slug>
<name>📝 Plan</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Check for existing AGENTS.md files and AI assistant rules | Completed |
| 2 | Identify project stack and structure | Completed |
| 3 | Extract build/test/lint commands | Completed |
| 4 | Analyze code patterns and conventions | Completed |
| 5 | Document non-obvious project-specific information | In Progress |
| 6 | Create/update AGENTS.md files | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<ask_followup_question>
<question>I've analyzed the codebase and identified several non-obvious, project-specific patterns. Before creating the AGENTS.md files, I want to confirm which aspects are most critical to document:

**Key non-obvious discoveries:**
1. **Types-first workflow** - [`verdict/types.py`](verdict/types.py:1) must be modified via team consensus (Discord) before implementation changes
2. **Parallel work contract** - All checks implement [`Check` Protocol](verdict/types.py:43) with exact signature: `run(diff_root: str, added_functions: list[AddedFunction]) -> list[Finding]`
3. **Fixture-driven testing** - Tests must validate against `fixtures/lying_repo` (expected findings in `EXPECTED_FINDINGS.md`) and `fixtures/honest_repo` (must return PASS)
4. **Definition of done** - Feature incomplete until: merged to main, passes tests, matches fixture expectations, wired into CLI, documented in README
5. **Import style** - Absolute imports only (`from verdict.types import Finding`), never relative
6. **Scorecard thresholds** - `LIED` if confidence > 0.8, `SUSPICIOUS` if any findings, `PASS` otherwise

Should I focus the AGENTS.md on these workflow/architecture constraints, or would you prefer emphasis on different aspects?</question>
<follow_up>
<suggest>Focus on the types-first workflow and Check Protocol contract - these are critical for parallel development</suggest>
<suggest>Include all six discoveries - they're all non-obvious and prevent common mistakes</suggest>
<suggest>Add testing requirements (fixture validation) but skip the team workflow details</suggest>
<suggest>Keep it minimal - just the Check Protocol signature and import style</suggest>
</follow_up>
</ask_followup_question>

---

**User:**

[ask_followup_question for 'I've analyzed the codebase and identified several non-obvious, project-specific patterns. Before creating the AGENTS.md files, I want to confirm which aspects are most critical to document:

**Key non-obvious discoveries:**
1. **Types-first workflow** - [`verdict/types.py`](verdict/types.py:1) must be modified via team consensus (Discord) before implementation changes
2. **Parallel work contract** - All checks implement [`Check` Protocol](verdict/types.py:43) with exact signature: `run(diff_root: str, added_functions: list[AddedFunction]) -> list[Finding]`
3. **Fixture-driven testing** - Tests must validate against `fixtures/lying_repo` (expected findings in `EXPECTED_FINDINGS.md`) and `fixtures/honest_repo` (must return PASS)
4. **Definition of done** - Feature incomplete until: merged to main, passes tests, matches fixture expectations, wired into CLI, documented in README
5. **Import style** - Absolute imports only (`from verdict.types import Finding`), never relative
6. **Scorecard thresholds** - `LIED` if confidence > 0.8, `SUSPICIOUS` if any findings, `PASS` otherwise

Should I focus the AGENTS.md on these workflow/architecture constraints, or would you prefer emphasis on different aspects?'] Result:
<answer>
Include all six discoveries - they're all non-obvious and prevent common mistakes
</answer>
<environment_details>
# VSCode Visible Files
verdict\types.py

# VSCode Open Tabs
verdict/types.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T17:34:07.660Z
User time zone: America/Toronto, UTC-4:00

# Current Cost
$0.62

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>plan</slug>
<name>📝 Plan</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Check for existing AGENTS.md files and AI assistant rules | Completed |
| 2 | Identify project stack and structure | Completed |
| 3 | Extract build/test/lint commands | Completed |
| 4 | Analyze code patterns and conventions | Completed |
| 5 | Document non-obvious project-specific information | In Progress |
| 6 | Create/update AGENTS.md files | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<update_todo_list>
<todos>
[x] Check for existing AGENTS.md files and AI assistant rules
[x] Identify project stack and structure
[x] Extract build/test/lint commands
[x] Analyze code patterns and conventions
[x] Document non-obvious project-specific information
[-] Create/update AGENTS.md files
</todos>
</update_todo_list>

---

**User:**

[update_todo_list] Result:
Todo list updated successfully.
<environment_details>
# VSCode Visible Files
verdict\types.py

# VSCode Open Tabs
verdict/types.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T17:34:15.075Z
User time zone: America/Toronto, UTC-4:00

# Current Cost
$0.71

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>plan</slug>
<name>📝 Plan</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Check for existing AGENTS.md files and AI assistant rules | Completed |
| 2 | Identify project stack and structure | Completed |
| 3 | Extract build/test/lint commands | Completed |
| 4 | Analyze code patterns and conventions | Completed |
| 5 | Document non-obvious project-specific information | Completed |
| 6 | Create/update AGENTS.md files | In Progress |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<write_to_file>
<path>AGENTS.md</path>
<content># AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Build & Test Commands

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Format code
ruff format

# Lint code
ruff check

# Run tests
pytest

# Run pre-commit hooks
pre-commit run --all-files
```

## Critical Architecture Constraints

**Types-first workflow:** [`verdict/types.py`](verdict/types.py) defines all shared interfaces. DO NOT modify these types without team consensus - all parallel work depends on interface stability.

**Check Protocol contract:** All checks MUST implement the [`Check` Protocol](verdict/types.py:43-50):
```python
class Check(Protocol):
    name: str
    def run(self, diff_root: str, added_functions: list[AddedFunction]) -> list[Finding]: ...
```

**Fixture-driven testing:** Tests MUST validate against two fixture repos:
- `fixtures/lying_repo` - must produce findings matching `EXPECTED_FINDINGS.md`
- `fixtures/honest_repo` - must return `PASS` verdict (no false positives)

**Definition of done:** A feature is incomplete until ALL of:
1. Merged to `main`
2. Passes unit tests
3. Produces expected output on `fixtures/lying_repo`
4. Returns `PASS` on `fixtures/honest_repo`
5. Wired into CLI (`verdict run` invokes it)
6. Documented in README

**Scorecard verdict thresholds:**
- `LIED` if any finding has `confidence > 0.8`
- `SUSPICIOUS` if any findings exist
- `PASS` otherwise

## Code Style (Non-Obvious)

**Imports:** Absolute imports ONLY (`from verdict.types import Finding`). Never use relative imports.

**Type hints:** Required on all public functions. Target `mypy --strict` compliance.

**Naming:** Framework hooks exempt from dead-function detection: `@pytest.fixture`, `@app.route`, `@click.command`, presence in `__all__`, dunder methods, `test_*` functions, names in `__init__.py` imports.
</content>
<line_count>60</line_count>
</write_to_file>

---

**User:**

[write_to_file for 'AGENTS.md'] Result:
<file_write_result>
<path>AGENTS.md</path>
<operation>created</operation>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<environment_details>
# VSCode Visible Files
AGENTS.md

# VSCode Open Tabs
verdict/types.py,AGENTS.md

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T17:35:29.984Z
User time zone: America/Toronto, UTC-4:00

# Current Cost
$0.80

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>plan</slug>
<name>📝 Plan</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Check for existing AGENTS.md files and AI assistant rules | Completed |
| 2 | Identify project stack and structure | Completed |
| 3 | Extract build/test/lint commands | Completed |
| 4 | Analyze code patterns and conventions | Completed |
| 5 | Document non-obvious project-specific information | Completed |
| 6 | Create/update AGENTS.md files | In Progress |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<write_to_file>
<path>.bob/rules-code/AGENTS.md</path>
<content># Project Coding Rules (Non-Obvious Only)

## Check Implementation Contract

All checks MUST implement [`Check` Protocol](../../verdict/types.py:43-50) with exact signature:
```python
def run(self, diff_root: str, added_functions: list[AddedFunction]) -> list[Finding]: ...
```

## Testing Requirements

- Tests MUST validate against `fixtures/lying_repo` (produce expected findings)
- Tests MUST validate against `fixtures/honest_repo` (return PASS, no false positives)
- Feature incomplete until wired into CLI and produces correct fixture output

## Import Rules

Absolute imports ONLY: `from verdict.types import Finding`
Never use relative imports (`.types`, `..types`)

## Framework Hook Exemptions

These patterns exempt functions from dead-function detection:
- `@pytest.fixture`, `@app.route`, `@click.command`
- Presence in `__all__`
- Dunder methods (`__init__`, `__str__`, etc.)
- `test_*` function names
- Names imported in `__init__.py`

## Scorecard Thresholds

- `LIED`: any finding with `confidence > 0.8`
- `SUSPICIOUS`: any findings exist
- `PASS`: no findings

## Critical Constraint

DO NOT modify [`verdict/types.py`](../../verdict/types.py) without team consensus - all parallel work depends on interface stability.
</content>
<line_count>37</line_count>
</write_to_file>

---

**User:**

[write_to_file for '.bob/rules-code/AGENTS.md'] Result:
<file_write_result>
<path>.bob/rules-code/AGENTS.md</path>
<operation>created</operation>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<environment_details>
# VSCode Visible Files
.bob\rules-code\AGENTS.md

# VSCode Open Tabs
verdict/types.py,AGENTS.md,.bob/rules-code/AGENTS.md

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T17:35:47.759Z
User time zone: America/Toronto, UTC-4:00

# Current Cost
$0.90

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>plan</slug>
<name>📝 Plan</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Check for existing AGENTS.md files and AI assistant rules | Completed |
| 2 | Identify project stack and structure | Completed |
| 3 | Extract build/test/lint commands | Completed |
| 4 | Analyze code patterns and conventions | Completed |
| 5 | Document non-obvious project-specific information | Completed |
| 6 | Create/update AGENTS.md files | In Progress |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<write_to_file>
<path>.bob/rules-advanced/AGENTS.md</path>
<content># Project Advanced Coding Rules (Non-Obvious Only)

## Check Implementation Contract

All checks MUST implement [`Check` Protocol](../../verdict/types.py:43-50) with exact signature:
```python
def run(self, diff_root: str, added_functions: list[AddedFunction]) -> list[Finding]: ...
```

## Testing Requirements

- Tests MUST validate against `fixtures/lying_repo` (produce expected findings)
- Tests MUST validate against `fixtures/honest_repo` (return PASS, no false positives)
- Feature incomplete until wired into CLI and produces correct fixture output

## Import Rules

Absolute imports ONLY: `from verdict.types import Finding`
Never use relative imports (`.types`, `..types`)

## Framework Hook Exemptions

These patterns exempt functions from dead-function detection:
- `@pytest.fixture`, `@app.route`, `@click.command`
- Presence in `__all__`
- Dunder methods (`__init__`, `__str__`, etc.)
- `test_*` function names
- Names imported in `__init__.py`

## Scorecard Thresholds

- `LIED`: any finding with `confidence > 0.8`
- `SUSPICIOUS`: any findings exist
- `PASS`: no findings

## Critical Constraint

DO NOT modify [`verdict/types.py`](../../verdict/types.py) without team consensus - all parallel work depends on interface stability.

## Advanced Mode Tools

This mode has access to MCP and Browser tools for enhanced capabilities.
</content>
<line_count>40</line_count>
</write_to_file>

---

**User:**

[write_to_file for '.bob/rules-advanced/AGENTS.md'] Result:
<file_write_result>
<path>.bob/rules-advanced/AGENTS.md</path>
<operation>created</operation>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<environment_details>
# VSCode Visible Files
.bob\rules-advanced\AGENTS.md

# VSCode Open Tabs
verdict/types.py,AGENTS.md,.bob/rules-code/AGENTS.md,.bob/rules-advanced/AGENTS.md

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T17:36:02.322Z
User time zone: America/Toronto, UTC-4:00

# Current Cost
$0.99

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>plan</slug>
<name>📝 Plan</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Check for existing AGENTS.md files and AI assistant rules | Completed |
| 2 | Identify project stack and structure | Completed |
| 3 | Extract build/test/lint commands | Completed |
| 4 | Analyze code patterns and conventions | Completed |
| 5 | Document non-obvious project-specific information | Completed |
| 6 | Create/update AGENTS.md files | In Progress |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<write_to_file>
<path>.bob/rules-ask/AGENTS.md</path>
<content># Project Documentation Rules (Non-Obvious Only)

## Architecture Documentation

- [`verdict-spec.md`](../../verdict-spec.md) - Complete feature specification with priorities P0-P4
- [`TEAM.md`](../../TEAM.md) - Team workflow, roles, and integration plan (local to team)
- [`verdict/types.py`](../../verdict/types.py) - Canonical interface definitions (types-first workflow)

## Non-Obvious Project Structure

**Types-first development:** All shared interfaces in [`verdict/types.py`](../../verdict/types.py) must be stable before implementation. Changes require team consensus.

**Fixture repos are canonical:** 
- `fixtures/lying_repo` - Expected to produce findings (ground truth in `EXPECTED_FINDINGS.md`)
- `fixtures/honest_repo` - Expected to return `PASS` (validates no false positives)

**Check architecture:** All checks implement [`Check` Protocol](../../verdict/types.py:43-50) and return `list[Finding]`. This enables parallel development across team members.

## Scorecard Verdict Logic

Non-obvious thresholds (not configurable):
- `LIED` if ANY finding has `confidence > 0.8`
- `SUSPICIOUS` if ANY findings exist (regardless of confidence)
- `PASS` only if zero findings

## Framework Hook Patterns

Functions exempt from dead-function detection (non-obvious list):
- `@pytest.fixture`, `@app.route`, `@click.command` decorators
- Names in `__all__` exports
- Dunder methods
- `test_*` prefixed functions
- Names imported in `__init__.py`

## Build System

Python 3.10+ required. Uses `ruff` (not black) for formatting. Install with `pip install -e ".[dev]"` to get dev dependencies.
</content>
<line_count>40</line_count>
</write_to_file>

---

**User:**

[write_to_file for '.bob/rules-ask/AGENTS.md'] Result:
<file_write_result>
<path>.bob/rules-ask/AGENTS.md</path>
<operation>created</operation>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<environment_details>
# VSCode Visible Files
.bob\rules-ask\AGENTS.md

# VSCode Open Tabs
verdict/types.py,AGENTS.md,.bob/rules-code/AGENTS.md,.bob/rules-advanced/AGENTS.md,.bob/rules-ask/AGENTS.md

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T17:36:17.498Z
User time zone: America/Toronto, UTC-4:00

# Current Cost
$1.09

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>plan</slug>
<name>📝 Plan</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Check for existing AGENTS.md files and AI assistant rules | Completed |
| 2 | Identify project stack and structure | Completed |
| 3 | Extract build/test/lint commands | Completed |
| 4 | Analyze code patterns and conventions | Completed |
| 5 | Document non-obvious project-specific information | Completed |
| 6 | Create/update AGENTS.md files | In Progress |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<write_to_file>
<path>.bob/rules-plan/AGENTS.md</path>
<content># Project Architecture Rules (Non-Obvious Only)

## Types-First Architecture Constraint

[`verdict/types.py`](../../verdict/types.py) defines ALL shared interfaces and MUST remain stable. Changes require team consensus because all parallel work depends on these contracts.

Critical interfaces:
- `Check` Protocol - all checks implement this
- `AddedFunction`, `Finding`, `Scorecard` - data shapes passed between components
- `VerdictLevel` - literal type for verdict outcomes

## Parallel Work Dependencies

**Foundation layer** ([`verdict-spec.md`](../../verdict-spec.md) P0.1):
- `diff.py` - git diff parsing
- `ast_utils.py` - AST analysis for added functions
- Must be merged FIRST - all checks depend on this

**Check layer** (P0.2, P0.3, P2.1-P2.3):
- Each check is independent, implements `Check` Protocol
- All consume `list[AddedFunction]`, return `list[Finding]`
- Can be developed in parallel once foundation exists

**Integration layer** (P0.4, P1.2):
- CLI wires checks together
- MCP server wraps CLI output
- Both depend on checks being complete

## Fixture-Driven Validation

Non-obvious requirement: Features incomplete until validated against BOTH:
- `fixtures/lying_repo` - must produce expected findings (documented in `EXPECTED_FINDINGS.md`)
- `fixtures/honest_repo` - must return `PASS` (validates no false positives)

This dual-fixture approach catches both false negatives and false positives.

## Scorecard Verdict Thresholds

Non-configurable logic (hardcoded in scorecard):
- `LIED`: ANY finding with `confidence > 0.8`
- `SUSPICIOUS`: ANY findings exist
- `PASS`: zero findings

## Framework Hook Exemptions

Dead-function detection must skip these patterns (non-obvious list):
- `@pytest.fixture`, `@app.route`, `@click.command`
- Names in `__all__`
- Dunder methods
- `test_*` functions
- Names in `__init__.py` imports
</content>
<line_count>53</line_count>
</write_to_file>

---

**User:**

[write_to_file for '.bob/rules-plan/AGENTS.md'] Result:
<file_write_result>
<path>.bob/rules-plan/AGENTS.md</path>
<operation>created</operation>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<environment_details>
# VSCode Visible Files
.bob\rules-plan\AGENTS.md

# VSCode Open Tabs
verdict/types.py,AGENTS.md,.bob/rules-code/AGENTS.md,.bob/rules-advanced/AGENTS.md,.bob/rules-ask/AGENTS.md,.bob/rules-plan/AGENTS.md

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T17:36:34.117Z
User time zone: America/Toronto, UTC-4:00

# Current Cost
$1.19

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>plan</slug>
<name>📝 Plan</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Check for existing AGENTS.md files and AI assistant rules | Completed |
| 2 | Identify project stack and structure | Completed |
| 3 | Extract build/test/lint commands | Completed |
| 4 | Analyze code patterns and conventions | Completed |
| 5 | Document non-obvious project-specific information | Completed |
| 6 | Create/update AGENTS.md files | In Progress |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<update_todo_list>
<todos>
[x] Check for existing AGENTS.md files and AI assistant rules
[x] Identify project stack and structure
[x] Extract build/test/lint commands
[x] Analyze code patterns and conventions
[x] Document non-obvious project-specific information
[x] Create/update AGENTS.md files
</todos>
</update_todo_list>

---

**User:**

[update_todo_list] Result:
Todo list updated successfully.
<environment_details>
# VSCode Visible Files
.bob\rules-plan\AGENTS.md

# VSCode Open Tabs
verdict/types.py,AGENTS.md,.bob/rules-code/AGENTS.md,.bob/rules-advanced/AGENTS.md,.bob/rules-ask/AGENTS.md,.bob/rules-plan/AGENTS.md

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T17:36:41.588Z
User time zone: America/Toronto, UTC-4:00

# Current Cost
$1.30

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>plan</slug>
<name>📝 Plan</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Check for existing AGENTS.md files and AI assistant rules | Completed |
| 2 | Identify project stack and structure | Completed |
| 3 | Extract build/test/lint commands | Completed |
| 4 | Analyze code patterns and conventions | Completed |
| 5 | Document non-obvious project-specific information | Completed |
| 6 | Create/update AGENTS.md files | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<attempt_completion>
<result>
Created comprehensive AGENTS.md files for the verdict project:

**Main file:** [`AGENTS.md`](AGENTS.md) - General guidance with build commands, critical architecture constraints, and code style rules

**Mode-specific files in `.bob/` directory:**
- [`rules-code/AGENTS.md`](.bob/rules-code/AGENTS.md) - Check implementation contract, testing requirements, import rules
- [`rules-advanced/AGENTS.md`](.bob/rules-advanced/AGENTS.md) - Same as code mode plus MCP/Browser tool access
- [`rules-ask/AGENTS.md`](.bob/rules-ask/AGENTS.md) - Documentation structure, non-obvious project organization
- [`rules-plan/AGENTS.md`](.bob/rules-plan/AGENTS.md) - Types-first architecture, parallel work dependencies, fixture validation

**Key non-obvious patterns documented:**
1. Types-first workflow - [`verdict/types.py`](verdict/types.py) requires team consensus before changes
2. Check Protocol contract - exact signature required for all checks
3. Dual-fixture testing - must validate against both `lying_repo` and `honest_repo`
4. Scorecard thresholds - `LIED` at confidence > 0.8, `SUSPICIOUS` if any findings
5. Absolute imports only - never use relative imports
6. Framework hook exemptions - specific patterns that skip dead-function detection

All files focus exclusively on non-obvious, project-specific information discovered by reading the codebase, spec, and team documentation.
</result>
</attempt_completion>

