# Commit Message Convention

This document describes the commit message format used in this project. All commits should follow this convention to maintain consistency and enable automated changelog generation.

## Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type (Required)

Must be one of the following:

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **build**: Changes that affect the build system or external dependencies
- **ci**: Changes to our CI configuration files and scripts
- **chore**: Other changes that don't modify src or test files
- **revert**: Reverts a previous commit

### Scope (Optional)

The scope should be the name of the module/component affected:

- **frontend**: React frontend changes
- **backend**: API server changes
- **agent**: Multi-agent system changes
- **tools**: Tool-related changes
- **tests**: Test suite changes
- **docs**: Documentation changes

### Subject (Required)

The subject contains a succinct description of the change:

- Use the imperative, present tense: "change" not "changed" nor "changes"
- Don't capitalize the first letter
- No dot (.) at the end
- Maximum 50 characters

### Body (Optional)

The body should include the motivation for the change and contrast this with previous behavior:

- Use the imperative, present tense
- Should include "why" not just "what"
- Wrap at 72 characters

### Footer (Optional)

The footer should contain any information about Breaking Changes and is also the place to reference GitHub issues:

- Breaking changes should start with `BREAKING CHANGE:`
- Reference issues like `Closes #123` or `Fixes #456`

## Examples

### Simple feature addition
```
feat(frontend): add markdown support for chat messages

Add react-markdown library to render GitHub-flavored markdown in AI responses.
This improves readability of formatted content like code blocks and lists.
```

### Bug fix with issue reference
```
fix(agent): correct model ID for gemini flash

The test files were using an invalid model ID 'google/gemini-flash-2.5'.
Updated to use the correct ID 'google/gemini-2.5-flash' to match the
environment configuration.

Fixes #234
```

### Breaking change
```
refactor(frontend)!: restructure message components

Split monolithic ChatInterface into modular components:
- BaseMessageCard for common functionality
- AIMessageCard for AI responses
- ToolCallCard for tool executions
- FileOperationCard for file operations

BREAKING CHANGE: ChatInterface component API has changed.
Components importing ChatInterface need to update their imports.
```

### Documentation update
```
docs: update README with new frontend features

Document the enhanced message rendering components and markdown support
added in v0.2.0.
```

### Multiple changes (use multiple commits instead)
❌ **Bad:**
```
feat: add markdown support and fix tests
```

✅ **Good:** Create separate commits:
```
feat(frontend): add markdown support for chat messages
```
```
test: fix model ID in test files
```

## Commit Message Template

You can set up a commit message template in your local git configuration:

```bash
git config commit.template .gitmessage
```

Create `.gitmessage` file:
```
# <type>(<scope>): <subject>
# 
# <body>
# 
# <footer>
# 
# Type: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
# Scope: frontend, backend, agent, tools, tests, docs
# Subject: imperative mood, no capitalization, no period, max 50 chars
# Body: explain what and why, not how, wrap at 72 chars
# Footer: breaking changes, issue references
```