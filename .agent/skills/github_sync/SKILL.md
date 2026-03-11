---
name: github_sync
description: Skill for automating GitHub updates and ensuring repository state consistency.
---

# GitHub Sync Skill (cglobal)

This skill provides a standard procedure for updating the GitHub repository, handling common pitfalls, and maintaining a clean git state.

## Core Responsibilities

1. **Repository Synchronization**: Ensure the local repository is correctly linked to the GitHub remote `muranja/ultrafiles`.
2. **Email Privacy Management**: Ensure commits use the GitHub no-reply email (`81810021+muranja@users.noreply.github.com`) to avoid push rejections.
3. **Branch Consistency**: Maintain `main` as the default branch and ensure it tracks `origin/main`.

## Usage Patterns

### Standard Update Flow

When tasked with "updating GitHub" or "pushing changes":

1. **Check Status**: Run `git status` to identify modified and untracked files.
2. **Stage Files**: Add files relevant to the current task using `git add`.
3. **Commit with Context**: Create a descriptive commit message. If the author email is incorrect, use:
    ```bash
    git config user.email "81810021+muranja@users.noreply.github.com"
    git commit --amend --reset-author --no-edit
    ```
4. **Push to Main**: Execute `git push origin main`.

### Handling Push Rejections (Email Privacy)

If a push is declined with error `GH007: Your push would publish a private email address`:

1. Update local git config:
    ```bash
    git config user.email "81810021+muranja@users.noreply.github.com"
    ```
2. Reset author on the latest commit:
    ```bash
    git commit --amend --reset-author --no-edit
    ```
3. Retry the push.

### Repository Restoration

If the `.git` directory is missing but the files exist:

1. Initialize git: `git init`.
2. Add remote: `git remote add origin https://github.com/muranja/ultrafiles.git`.
3. Fetch and reset:
    ```bash
    git fetch origin
    git reset --hard origin/main
    ```

## Guardrails

- **NEVER** push directly to `master` if `main` is the primary branch.
- **ALWAYS** check `git status` before adding all files (`git add .`) to avoid committing temporary or sensitive data.
- **VERIFY** that `muranja/ultrafiles` is the intended target.
