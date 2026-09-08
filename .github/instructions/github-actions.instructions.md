---
description: "GitHub Actions naming, permissions, reusable workflow, and security conventions"
applyTo: ".github/workflows/**,**/action.yml,**/action.yaml"
---

# GitHub Actions

* Set workflow-level `permissions: {}` and grant the minimum permissions per job.
* Pin actions to major version tags and use `fetch-depth: 0` when GitVersion runs.
* Keep cross-repository build logic in reusable workflows under `gha-workflows`.
* Use kebab-case for inputs, uppercase snake case for environment variables, and
  short single-line descriptions.
* Use two-space YAML indentation and one blank line between steps.
* Keep the `lint`, `versioning`, `app`, `image`, and `release` job topology aligned
  with the sibling repositories.
