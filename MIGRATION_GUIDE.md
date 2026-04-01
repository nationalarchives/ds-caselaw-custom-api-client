# Migration Guide: v2.0.0 Breaking Changes

## Overview

Version 2.0.0 introduces a **breaking change** to how document metadata is updated. The old "bare" setter methods on `MarklogicApiClient` are being removed in favor of a more explicit, safer pattern: **load document → mutate in-memory → save atomically**.

This guide shows how to migrate your code.

---

## Why This Change?

**Old Pattern Issues:**

- Mutation and persistence were conflated into one method call
- No way to batch multiple mutations into a single atomic save
- No optimistic locking support (vulnerable to lost updates if document modified elsewhere)
- Difficult to test in isolation (required mocking MarkLogic calls)

**New Pattern Benefits:**

- **Explicit intent**: Load document, mutate locally, then save
- **Atomic saves**: Multiple mutations persist together in a single MarkLogic operation
- **Optimistic locking**: Prevent lost updates with optional `from_version` parameter
- **Testable**: Mutations work on in-memory XML without MarkLogic access
- **Batch-friendly**: Combine multiple metadata changes in one save

---

## Migration Examples

### 1. Setting Document Name

**Old Code (v1.x):**

```python
api_client.set_document_name(
    uri="[2024] EWHC 123",
    content="Smith v Jones"
)
```

**New Code (v2.0+):**

```python
doc = api_client.get_document_by_uri("[2024] EWHC 123")
doc.body.set_name("Smith v Jones")
doc.save()
```

---

### 2. Setting Work Expression Date

**Old Code (v1.x):**

```python
api_client.set_document_work_expression_date(
    uri="[2024] EWHC 123",
    content="2024-01-15"
)
```

**New Code (v2.0+):**

```python
doc = api_client.get_document_by_uri("[2024] EWHC 123")
doc.body.set_date("2024-01-15")
doc.save()
```

---

### 3. Setting Judgment Citation

**Old Code (v1.x):**

```python
api_client.set_judgment_citation(
    uri="[2024] EWHC 123",
    content="[2024] EWHC 123 (QB)"
)
```

**New Code (v2.0+):**

```python
doc = api_client.get_document_by_uri("[2024] EWHC 123")
doc.body.set_citation("[2024] EWHC 123 (QB)")
doc.save()
```

---

### 4. Setting Court

**Old Code (v1.x):**

```python
api_client.set_document_court(
    uri="[2024] EWHC 123",
    content="High Court"
)
```

**New Code (v2.0+):**

```python
doc = api_client.get_document_by_uri("[2024] EWHC 123")
doc.body.set_court("High Court")
doc.save()
```

---

### 5. Setting Jurisdiction

**Old Code (v1.x):**

```python
api_client.set_document_jurisdiction(
    uri="[2024] EWHC 123",
    content="England and Wales"
)
```

**New Code (v2.0+):**

```python
doc = api_client.get_document_by_uri("[2024] EWHC 123")
doc.body.set_jurisdiction("England and Wales")
doc.save()
```

---

### 6. Setting Court and Jurisdiction Together

**Old Code (v1.x):**

```python
api_client.set_document_court_and_jurisdiction(
    uri="[2024] EWHC 123",
    content="High Court/England and Wales"
)
```

**New Code (v2.0+):**

```python
doc = api_client.get_document_by_uri("[2024] EWHC 123")
doc.body.set_court_and_jurisdiction("High Court/England and Wales")
doc.save()
```

---

### 7. Setting This URI

**Old Code (v1.x):**

```python
api_client.set_judgment_this_uri("[2024] EWHC 123")
```

**New Code (v2.0+):**

```python
doc = api_client.get_document_by_uri("[2024] EWHC 123")
doc.body.set_this_uri("[2024] EWHC 123")
doc.save()
```

---

## Batch Mutations (New Capability)

One of the key benefits of v2.0.0 is the ability to batch multiple mutations and save them atomically:

```python
# Load document once
doc = api_client.get_document_by_uri("[2024] EWHC 123")

# Perform multiple mutations in memory (no MarkLogic calls yet)
doc.body.set_name("Smith v Jones")
doc.body.set_date("2024-01-15")
doc.body.set_court("High Court")
doc.body.set_jurisdiction("England and Wales")

# Save all mutations in a single atomic operation
doc.save()
```

This is much more efficient than the old pattern, which would require 4 separate MarkLogic calls.

---

## Custom Version Annotations (Optional)

By default, `save()` creates a version annotation with type `EDIT` and an automated message. You can customize this:

```python
from caselawclient.models.documents.versions import VersionAnnotation, VersionType

doc = api_client.get_document_by_uri("[2024] EWHC 123")
doc.body.set_name("Smith v Jones")

# Create custom annotation
annotation = VersionAnnotation(
    version_type=VersionType.EDIT,
    automated=False,
    message="Updated judgment title to match published version",
    calling_function="bulk_import_service",
    calling_agent="import-agent-v3"
)

doc.save(annotation=annotation)
```

---

## Optimistic Locking (Advanced)

To prevent "lost updates" when multiple processes modify the same document, use the `from_version` parameter:

```python
# Load document and capture version
doc = api_client.get_document_by_uri("[2024] EWHC 123")
current_version = doc.version_number

# ... time passes, other processes might modify the document ...

# Make changes
doc.body.set_name("Updated Name")

# Save only if version hasn't changed
try:
    doc.save(from_version=current_version)
except caselawclient.errors.VersionMismatchError:
    # Document was modified by another process
    print(f"Document changed. Was at version {current_version}, now at {doc.version_number}")

    # Reload and retry
    doc = api_client.get_document_by_uri("[2024] EWHC 123")
    doc.body.set_name("Updated Name")
    doc.save(from_version=doc.version_number)
```

---

## Error Handling

### `InvalidContentHashError`

Thrown if you attempt to modify the document's _text content_ (not just metadata). The new API only supports metadata mutations. For text content changes, use XQuery directly or contact the server team.

```python
doc = api_client.get_document_by_uri("[2024] EWHC 123")

# This is OK (metadata-only)
doc.body.set_name("Updated Name")
doc.save()  # ✅ Works

# This would fail (text content mutation)
doc.body._xml._tree.text = "New judgment text"  # Don't do this!
doc.save()  # ❌ Raises InvalidContentHashError
```

### `VersionMismatchError`

Thrown if you use `from_version` and the document's current version doesn't match:

```python
doc = api_client.get_document_by_uri("[2024] EWHC 123")
doc.body.set_name("Updated Name")

# If document was modified elsewhere, this fails
try:
    doc.save(from_version=42)  # Passed version doesn't match current
except caselawclient.errors.VersionMismatchError as e:
    print(f"Cannot save: {e}")
```

---

## Troubleshooting

### "AttributeError: 'MarklogicApiClient' object has no attribute 'set_document_name'"

You're using v2.0+. Switch to the new pattern:

```python
# ❌ Old API removed
api_client.set_document_name(uri, content)

# ✅ New API
doc = api_client.get_document_by_uri(uri)
doc.body.set_name(content)
doc.save()
```

### "Document returns version None after loading"

Some documents (e.g., ingested via import) may not have version information. You can still mutate and save, but you cannot use `from_version`:

```python
doc = api_client.get_document_by_uri(uri)
doc.body.set_name("Updated Name")
doc.save()  # ✅ Works without from_version

# But this will fail:
doc.save(from_version=doc.version_number)  # ❌ version_number is None
```

### "Pre-commit checks fail after saving"

Ensure you've imported the correct types at the top of your file:

```python
from caselawclient import MarklogicApiClient
from caselawclient.models.documents.versions import VersionAnnotation, VersionType
```

---

## Timeline

- **v2.0.0 released**: [Release date]
- **Old APIs deprecated**: v1.x users should migrate immediately
- **Support period**: Old API removed entirely in v2.0.0 (no deprecation period)

---

## Questions?

If you encounter issues migrating, please:

1. Check that you're using v2.0+ (`pip show caselawclient`)
2. Verify the document URI is valid and the document exists
3. Review the examples above for your specific use case
4. Contact the server team for complex edge cases

---

## Summary of Changes

| Capability                   | Old API                                                        | New API                                        |
| ---------------------------- | -------------------------------------------------------------- | ---------------------------------------------- |
| **Set name**                 | `api_client.set_document_name(uri, content)`                   | `doc.body.set_name(content)`                   |
| **Set date**                 | `api_client.set_document_work_expression_date(uri, content)`   | `doc.body.set_date(content)`                   |
| **Set citation**             | `api_client.set_judgment_citation(uri, content)`               | `doc.body.set_citation(content)`               |
| **Set court**                | `api_client.set_document_court(uri, content)`                  | `doc.body.set_court(content)`                  |
| **Set jurisdiction**         | `api_client.set_document_jurisdiction(uri, content)`           | `doc.body.set_jurisdiction(content)`           |
| **Set court & jurisdiction** | `api_client.set_document_court_and_jurisdiction(uri, content)` | `doc.body.set_court_and_jurisdiction(content)` |
| **Set this URI**             | `api_client.set_judgment_this_uri(uri)`                        | `doc.body.set_this_uri(uri)`                   |
| **Batch mutations**          | Not supported (separate calls)                                 | Fully supported (single `doc.save()`)          |
| **Custom annotations**       | Not supported                                                  | `doc.save(annotation=custom_annotation)`       |
| **Optimistic locking**       | Not supported                                                  | `doc.save(from_version=version)`               |
