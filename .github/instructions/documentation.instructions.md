---
description: "README synchronization, Markdown style, and Mermaid diagram conventions"
applyTo: "**/*.md"
---

# Documentation

* Keep the README synchronized with runtime behavior, image bases, configuration,
  validation commands, and all four sibling repositories.
* Keep README headings, ordering, and wording identical across the four sibling
  repositories; they exist to be diffed against each other.
* Only document what exists. Do not describe behavior until it is implemented.
* Use exactly one H1 and do not add YAML frontmatter to README files.
* Lead with a one- or two-sentence summary under the H1 stating what the repository
  is and who it is for.
* Do not skip heading levels; keep headings unique and tables pipe-spaced.
* Use descriptive link text, alt text on every image, and synthetic values in
  examples.
* Write one line per paragraph rather than hard-wrapping, matching the sibling
  repositories.
* Use Mermaid flowcharts for build and deployment flows and update them with code.
* Run the repository's pinned markdownlint command before committing Markdown changes.
