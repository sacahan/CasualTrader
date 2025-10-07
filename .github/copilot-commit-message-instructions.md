# Conventional Commits 1.0.0

## Summary

The Conventional Commits specification is a lightweight convention on top of commit messages.
It provides an easy set of rules for creating an explicit commit history;
which makes it easier to write automated tools on top of.

This convention dovetails with SemVer, by describing the features, fixes, and breaking changes made in commit messages.

### Commit Message Structure

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

The commit contains the following structural elements, to communicate intent to the consumers of your library:

- `fix:` a commit of the type **fix** patches a bug in your codebase
  ⤷ (correlates with **PATCH** in Semantic Versioning)
- `feat:` a commit of the type **feat** introduces a new feature
  ⤷ (correlates with **MINOR** in Semantic Versioning)
- `BREAKING CHANGE:`
  A commit with a `BREAKING CHANGE:` footer, or with a `!` after the type/scope,
  indicates a breaking API change
  ⤷ (correlates with **MAJOR** in Semantic Versioning)

Other allowed types include (as recommended by `@commitlint/config-conventional`, based on Angular):

`build:`, `chore:`, `ci:`, `docs:`, `style:`, `refactor:`, `perf:`, `test:`, and others.

Footers other than `BREAKING CHANGE: <description>` may follow the [git trailer format](https://git-scm.com/docs/git-interpret-trailers).

Additional types are allowed but **have no effect on SemVer** unless `BREAKING CHANGE` is involved.
A **scope** may be provided in parentheses to give context:

```text
feat(parser): add ability to parse arrays
```

---

## Examples

### Commit message with description and breaking change footer

```text
feat: allow provided config object to extend other configs

BREAKING CHANGE: `extends` key in config file is now used for extending other config files
```

### Commit message with `!` to draw attention to breaking change

```text
feat!: send an email to the customer when a product is shipped
```

### Commit message with scope and `!` to draw attention to breaking change

```text
feat(api)!: send an email to the customer when a product is shipped
```

### Commit message with both `!` and `BREAKING CHANGE` footer

```text
chore!: drop support for Node 6

BREAKING CHANGE: use JavaScript features not available in Node 6.
```

### Commit message with no body

```text
docs: correct spelling of CHANGELOG
```

### Commit message with scope

```text
feat(lang): add Polish language
```

### Commit message with multi-paragraph body and multiple footers

```text
fix: prevent racing of requests

Introduce a request id and a reference to latest request. Dismiss
incoming responses other than from latest request.

Remove timeouts which were used to mitigate the racing issue but are
obsolete now.

Reviewed-by: Z
Refs: #123
```

---

## Specification

The keywords **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **MAY**, and **OPTIONAL** in this document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

### Commit message rules

- Commits **MUST** be prefixed with a **type** (e.g. `feat`, `fix`)
- Type **MAY** be followed by **scope** in parentheses and optional `!`
- Type/scope prefix **MUST** be followed by `:` and a description
- The type `feat` **MUST** be used for new features
- The type `fix` **MUST** be used for bug fixes
- Scope **MAY** describe a code section in the format:
  `fix(parser): ...`
- Description **MUST** immediately follow the colon and space
  ⤷ e.g. `fix: array parsing issue when multiple spaces were contained in string`

### Commit body

- A longer body **MAY** follow after one blank line
- Body **MUST** start one blank line after description
- Body **MAY** contain multiple newline-separated paragraphs

### Footers

- One or more footers **MAY** follow after one blank line
- Each footer **MUST** follow format:
  `<token>: <value>` or `<token> #<issue>`
- Footer `token` **MUST** use `-` instead of spaces (e.g. `Acked-by`)
- Exception: `BREAKING CHANGE` **MAY** include spaces
- Footer value **MAY** contain newlines; parsing **MUST** stop at next valid token

### Breaking Changes

- Breaking changes **MUST** be indicated by:
  - `!` in type/scope
  - or `BREAKING CHANGE: <description>` in the footer
- `BREAKING CHANGE:` **MUST** be uppercase and followed by colon, space, and description
  ⤷ e.g. `BREAKING CHANGE: environment variables now take precedence over config files`
- If `!` is used, footer MAY omit `BREAKING CHANGE:` and use the main description instead

### Additional rules

- Types other than `feat` and `fix` **MAY** be used, e.g., `docs: update ref docs`
- Commit types and tokens (except `BREAKING CHANGE`) **MUST NOT** be case sensitive
- `BREAKING-CHANGE` is **equivalent** to `BREAKING CHANGE`
- 使用`繁體中文`撰寫message。

---
