## Committing

The process for committing in this repository is:

1. `git add` files to be committed
2. Run `pre-commit` to check linting etc
   - `pre-commit` may make its own formatting changes which need to be added
3. Fix any warnings which haven't been automatically solved
4. Repeat the `git add`/`pre-commit` cycle until there are no warnings
5. Provide the user a commitizen-friendly commit message, and wait for them to manually commit to meet commit signing requirements

## Testing

We prefer test-driven development. Each commit should include a suite of tests for changes made, covering all new features. Where changes are made tests should include a regression test. The entire test suite should be run prior to committing.

Tests can be run using `poetry run pytest`
