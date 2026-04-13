# Document Setter Refactoring Plan

## Objective

Refactor "bare" setter operations from direct XQuery calls in `ApiClient` to in-memory mutations on the `Document` class, followed by explicit `Document.save()` to persist changes to MarkLogic.

**Current Flow**: `downstream_app → api_client.set_X() → MarkLogic via XQuery`
**Desired Flow**: `downstream_app → document.set_X() → document.save() → MarkLogic`

---

## Phase 1: Identify & Catalog Setter Methods

### Getters to Convert (from Client.py)

- `set_document_name(uri, content)` → `Document.set_name(name: str)`
- `set_document_work_expression_date(uri, content)` → `Document.set_date(date: str)`
- `set_judgment_citation(uri, content)` → `Document.set_citation(citation: str)`
- `set_document_court(uri, content)` → `Document.set_court(court: str)`
- `set_document_jurisdiction(uri, content)` → `Document.set_jurisdiction(jurisdiction: str)`
- `set_document_court_and_jurisdiction(uri, content)` → `Document.set_court_and_jurisdiction(combined: str)`
- `set_judgment_this_uri(uri)` → `Document.set_this_uri()` (auto-generates from URI)

**Note**: Metadata-only setters; not for core document content or version-tracked changes.

### Out of Scope (for now)

- `set_property()` / `set_boolean_property()` / `set_datetime_property()` - MarkLogic custom properties, not XML metadata
- `set_property_as_node()` - Custom node properties
- `set_published()` - Status flags, not XML content
- Locking/checkout operations
- Higher-level operations like `publish()`, `delete()`

---

## Phase 2: Extend DocumentBody/XML for In-Memory Mutation

### 2.1 Add Mutation Methods to XML class

Create low-level XPath-based mutation helpers:

```python
# In src/caselawclient/models/documents/xml.py

def set_xpath_element_value(
    self,
    xpath: str,
    value: str,
    element_name: str,
    namespaces: dict[str, str] = DEFAULT_NAMESPACES
) -> None:
    """
    Set or create an element value at a given XPath.
    If element exists, replace it; if not, insert as child of parent.
    """

def set_xpath_attribute(
    self,
    xpath: str,
    attribute_name: str,
    attribute_value: str,
    namespaces: dict[str, str] = DEFAULT_NAMESPACES
) -> None:
    """Set an attribute on an existing element."""

def get_or_create_element(
    self,
    parent_xpath: str,
    element_name: str,
    namespaces: dict[str, str] = DEFAULT_NAMESPACES
) -> etree._Element:
    """Get existing child element or create new one."""

@property
def xml_as_bytes(self) -> bytes:
    """Return XML tree as bytes (for save operations)."""
```

### 2.2 Add High-Level Setters to DocumentBody

```python
# In src/caselawclient/models/documents/body.py

def set_name(self, name: str) -> None:
    """Set FRBRname/@value in metadata."""

def set_date(self, date: str) -> None:
    """Set FRBRdate/@date in metadata."""

def set_citation(self, citation: str) -> None:
    """Set citation (likely in proprietary namespace)."""

def set_court(self, court: str) -> None:
    """Set uk:court in proprietary metadata."""

def set_jurisdiction(self, jurisdiction: str) -> None:
    """Set uk:jurisdiction in proprietary metadata."""

def set_court_and_jurisdiction(self, combined: str) -> None:
    """Parse combined 'court/jurisdiction' and set both."""

def set_this_uri(self, uri: DocumentURIString) -> None:
    """Set FRBR manifestion URIs."""
```

**Design Note**: Clear cached properties when setters are called

```python
def set_name(self, name: str) -> None:
    self._xml.set_xpath_element_value(...)
    # Clear any cached properties that depend on name
    self.__dict__.pop("name", None)
```

---

## Phase 3: Implement Document.save()

### 3.1 Signature & Responsibilities

```python
# In src/caselawclient/models/documents/__init__.py

def save(
    self,
    annotation: Optional[VersionAnnotation] = None,
) -> requests.Response:
    """
    Persist in-memory XML modifications back to MarkLogic.

    Uses MarkLogic's atomic dls:document-checkout-update-checkin operation,
    so no manual locking is required.

    Handles:
    - Content hash validation
    - Version creation
    - Atomic checkout-update-checkin

    :param annotation: Version annotation (calling function, agent, etc.)
    :raises InvalidContentHashError: Content hash validation failed (text content was modified, not just metadata)
    :return: MarkLogic response
    """
```

### 3.2 Implementation Strategy

**Recommended: Use MarkLogic Atomic Operation**

MarkLogic provides `dls:document-checkout-update-checkin`, an atomic operation that handles checkout, update, and checkin in a single transaction. This is already exposed via `api_client.update_document_xml()`.

```python
def save(self, annotation: Optional[VersionAnnotation] = None) -> requests.Response:
    """
    Persist in-memory XML modifications back to MarkLogic using atomic checkout-update-checkin.

    This uses MarkLogic's dls:document-checkout-update-checkin for atomicity and to avoid
    manual lock management.
    """
    if annotation is None:
        annotation = VersionAnnotation()

    return self.api_client.update_document_xml(
        self.uri,
        self.body._xml.xml_as_tree,  # Send lxml Element tree
        annotation=annotation
    )
```

**Benefits**:

- Atomic operation: no race conditions between checkout and update
- Automatically creates version
- No manual lock management needed
- Existing `update_document.xqy` XQuery already implements this pattern
- Callers don't need to know about locking details

**Callers don't need to pre-checkout** — the atomic operation handles all locking internally.

### 3.3 VersionAnnotation Handling

- Document need access to `VersionAnnotation` class (may already be imported in versions.py)
- Allow callers to provide custom annotation
- Provide sensible defaults (calling function = "set_X" → "document_save")

### 3.4 Optimistic Locking via from_version Parameter

Optional `from_version` parameter enables optimistic locking to prevent lost updates:

```python
def save(
    self,
    annotation: Optional[VersionAnnotation] = None,
    from_version: Optional[int] = None,
) -> requests.Response:
    """
    Persist in-memory XML modifications back to MarkLogic.

    :param annotation: Version annotation (calling function, agent, etc.)
    :param from_version: If provided, only save if document version matches this.
                        Prevents lost updates if document was modified elsewhere.
                        Raises VersionMismatchError if version doesn't match.
    :raises InvalidContentHashError: Content hash validation failed (text content was modified)
    :raises VersionMismatchError: from_version provided but document version doesn't match
    :return: MarkLogic response
    """
```

**Implementation**: Modify `update_document.xqy` to accept optional `from_version` parameter and check atomically before applying update. If versions don't match, XQuery rejects the operation without modifying the document.

**Usage**:

```python
doc = api_client.get_document_by_uri(uri)
current_version = doc.version_number  # Store for later

# ... time passes, other edits might happen ...

doc.set_name("Updated Name")
# Fails if document was modified elsewhere since we loaded it
doc.save(from_version=current_version)
```

### 3.5 XQuery Changes

The existing `update_document.xqy` will need modification to support optional `from_version` checking:

```xquery
declare variable $from_version as xs:integer? external;
(: current version checking logic :)
(: if $from_version is provided and doesn't match current, return error :)
(: otherwise proceed with checkout-update-checkin as normal :)
```

This ensures the version check and update are atomic — MarkLogic will not allow another process to modify the document between the version check and the actual update.

---

## Phase 4: Testing Strategy

### 5.1 Unit Tests (MockLogic)

- Test XML mutation without MarkLogic calls
- Verify XPath resolution and element creation
- Test cached property invalidation
- Test error cases (missing parent elements, invalid XPath)

### 5.2 Integration Tests (requires MarkLogic)

**Not currently possible** — no MarkLogic testing harness available. Accepting this risk given:

- Robust unit tests of XML mutation catch the most common issues
- `update_document_xml()` is already tested by existing codebase
- Manual testing in staging environment for final validation
- Breaking change means downstream teams will rapidly surface any issues

### 5.3 Test Files to Create

```
tests/models/documents/
  test_document_setters.py          # Unit tests for new setter methods
  test_document_xml_mutation.py     # Unit tests for XML/DocumentBody mutations
  test_document_save.py             # Integration tests for save()
```

---

## Phase 5: Implementation Priority & Sequencing

### Step 1: XML & DocumentBody Mutation Layer

- Add `XML.set_xpath_*()` methods
- Add `DocumentBody.set_*()` methods
- **Estimated**: 1–2 days
- **Deliverable**: Tests pass, mutations work in isolation

### Step 2: Document.save()

- Implement Document.save() using atomic `dls:document-checkout-update-checkin`
- Add version annotation integration
- Add optional `from_version` parameter for optimistic locking
- Modify `update_document.xqy` to support atomic version checking (if `from_version` provided)
- No manual locking needed (MarkLogic handles atomically)
- **Estimated**: 1 day (includes XQuery modification)
- **Deliverable**: save() works with and without version checking

### Step 3: Documentation & Examples

- Update README with new pattern
- Add docstrings to all new methods
- Create migration guide for downstream teams (will be a breaking change notice)
- Document optimistic locking pattern and when to use `from_version`
- **Estimated**: 0.5 days

**Total Estimated Time**: ~3 days

---

## Phase 6: Rollout Strategy

### 6.1 Release: Hard Breaking Change

This is a **breaking change release**. The old bare `ApiClient.set_*()` methods are removed entirely.

**Migration Path for Downstream**:

1. Old code: `api_client.set_document_name(uri, "New Name")`
2. New code:
   ```python
   doc = api_client.get_document_by_uri(uri)
   doc.set_name("New Name")
   doc.save()
   ```

**Communication**:

- Major version bump (e.g., v2.0.0)
- CHANGELOG clearly documents breaking change and migration path
- Migration guide in README
- Consider sending notice to downstream teams before release

**Advantage**: Forces immediate adoption of safer, more maintainable pattern. No lingering old code paths.

---

## Phase 8: Risks & Mitigation

### Risk 1: Data Loss

**Scenario**: Caller modifies document, calls save(), but MarkLogic rejects or validation fails.
**Mitigation**:

- Atomic operation ensures consistency (checkout-update-checkin all succeed or all fail)
- Content hash validation (`InvalidContentHashError`) catches unintended text changes pre-save
- Strong unit tests of XML mutation
- Handle exceptions explicitly

### Risk 2: XML Structure Assumptions

**Scenario**: New document types or XSD versions break XPath expressions.
**Mitigation**:

- Each setter validates parent element exists before mutation
- Use try/except in mutation helpers
- Log warnings if elements not found

### Risk 3: Concurrent Modifications

**Scenario**: Two processes load same document, both modify, both save (lost updates).
**Mitigation**:

- Optional `from_version` parameter enables optimistic locking
- Version check happens atomically inside XQuery (no race window)
- If version mismatch, `VersionMismatchError` raised, no update applied
- Callers can retry: re-fetch document, re-apply changes, save again
- Default behavior (no `from_version`) allows unconditional overwrites for simple cases
- Document clearly that concurrent modifications require version checking

### Risk 4: Performance

**Scenario**: Mutating large XML trees in Python slower than XQuery.
**Mitigation**:

- Benchmark before/after
- lxml is highly optimized
- Expect minimal impact for metadata-only changes
- Profile if issues emerge

---

## Alternatives Considered

### Alt 1: Hybrid Approach

Keep XQuery for some operations, Python for others.
**Rejected**: Added complexity, inconsistent patterns.

### Alt 2: Automatic Versioning (via Atomic Operation)

Use MarkLogic's `dls:document-checkout-update-checkin` for atomicity and automatic versioning.
**Adopted**: This is the recommended approach since MarkLogic provides it as an atomic built-in.

### Alt 3: Immutable Pattern

Return new Document instead of mutating.
**Rejected**: Inconsistent with API expectations; higher memory overhead.

---

## Phase 9: Success Criteria

- [ ] All setter methods work on Document class
- [ ] XML mutations preserve well-formedness (lxml validates)
- [ ] Document.save() persists to MarkLogic correctly
- [ ] Optimistic locking via `from_version` parameter works (no lost updates)
- [ ] Old ApiClient setters completely removed (hard break)
- [ ] Tests cover happy path + error cases (including version mismatch)
- [ ] No performance regression
- [ ] Downstream teams successfully migrate to new API
- [ ] Breaking change clearly documented in CHANGELOG and migration guide
