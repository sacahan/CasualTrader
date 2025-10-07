# Coding Guidelines

## Introduction

These are VS Code coding guidelines. Please also review our [Source Code Organisation](https://github.com/microsoft/vscode/wiki/Source-Code-Organization) page.

## Task List

List the available executable tasks or options using 1, 2, 3, ... for easy user selection.

## Indentation

Use spaces, not tabs.

## Shell Tool

Use zsh syntax for shell commands.

## Naming Conventions

- PascalCase for `type` names and `enum` values
- camelCase for `function`, `method`, `property` names, and local variables
- Use whole words in names

## Types

- Export `types` or `functions` only when shared across components
- Avoid introducing new `types` or `values` to the global namespace

## Comments

- Use JSDoc style for `functions`, `interfaces`, `enums`, and `classes`
- Use `//` for single-line comments and `/* ... */` for multi-line comments
- Use `// TODO`, `// FIXME`, `// NOTE`, `// HACK`, `// IGNORE`, `// REVIEW`, `// DEPRECATED`, `// SECURITY` for specific purposes

## Strings

- "double quotes" for user-visible strings
- 'single quotes' otherwise

## Style

- Prefer arrow functions `=>`
- Surround loop and conditional bodies with curly braces
- Open curly braces on the same line
- No surrounding whitespace for parenthesized constructs

## Documentation / Specification

- Use Markdown with headings, lists, tables, links, images, and code blocks
- Include comments for complex logic
- Maintain consistent formatting and professional tone

## Role

- Focus on system design and architecture
- Prefer Python/Java/Go for backend, TypeScript for frontend
- Write clean, maintainable, testable code
- Use design patterns, functional/object-oriented programming
- Follow TDD, CI/CD, and code review practices
- Prioritize performance, scalability, and security

## Testing Strategy

- Write unit tests for individual components.
- Use integration tests to verify interactions between components.
- Perform end-to-end tests to ensure the system works as expected.
- Aim for high test coverage and use tools to measure it.
- Use testing frameworks like `pytest` or `Jest`.
- Each test case should add comments explaining its purpose and any complex logic.

## Version Control

- Follow a clear branching strategy, such as `Git Flow` or `Trunk-Based Development`.
- Write concise and descriptive commit messages.
- Use pull requests for code reviews.

## Security Practices

- Store sensitive information in environment variables.
- Validate all inputs to prevent SQL injection and other attacks.
- Use static analysis tools to detect vulnerabilities.

## Performance Optimization

- Use profiling tools to identify bottlenecks.
- Implement caching for frequently accessed data.
- Use asynchronous processing where applicable.

## Maintainability

- Modularize code to improve readability and reusability.
- Write clear documentation for complex logic.
- Use consistent coding standards across the project.

## Team Collaboration

- Conduct regular code reviews to ensure quality.
- Use task management tools like Jira or Trello.
- Maintain clear communication within the team.

## Deployment and Monitoring

- Design CI/CD pipelines for automated testing and deployment.
- Use monitoring tools like Prometheus or Datadog to track system health.
- Set up alerts for critical issues.
