# Agent Guidelines

**Purpose**: Guidelines for AI agents working on this codebase to maintain clean project structure and avoid clutter.

## Temporary Files and Scratchpad

### Scratchpad Directory

**Location**: `scratchpad/` (in project root)

**Purpose**: All temporary files, scripts, markdown files, and other output files created during development should be placed in the `scratchpad/` directory.

### What Goes in Scratchpad

✅ **DO Place in Scratchpad**:
- Temporary markdown files (analysis, notes, drafts)
- One-off scripts for testing/debugging
- Temporary output files (JSON, CSV, logs)
- Experimental code snippets
- Debugging artifacts
- Temporary documentation drafts
- Test data files
- Any file that can be safely deleted after an epic/task is complete

❌ **DON'T Place in Scratchpad**:
- Source code files (`src/`)
- Test files (`tests/`)
- Configuration files (`pyproject.toml`, `.env`, etc.)
- Documentation files (`docs/`)
- Data files (`data/`)
- Permanent scripts (`scripts/`)

### File Naming Convention

Use descriptive names with timestamps or task identifiers:

```
scratchpad/
├── analysis_2025-01-20_graph_structure.md
├── test_batch_edges_2025-01-20.py
├── debug_output_entity_resolution.json
├── temp_ingestion_logs.txt
└── experimental_query_optimization.md
```

### Cleanup Policy

**When to Clean**: After completing an epic or major task, review and clean up scratchpad files.

**What to Keep**:
- Files that document important decisions or findings
- Scripts that might be useful for future debugging
- Analysis that provides insights for future work

**What to Delete**:
- Temporary test files
- Debug output files
- One-off scripts that are no longer needed
- Duplicate or outdated analysis files

### Example Workflow

1. **During Development**:
   ```bash
   # Create temporary analysis file
   echo "# Graph Structure Analysis" > scratchpad/graph_analysis_$(date +%Y-%m-%d).md
   
   # Create test script
   cat > scratchpad/test_batch_performance.py << 'EOF'
   # Temporary test script
   ...
   EOF
   ```

2. **After Epic Completion**:
   ```bash
   # Review scratchpad contents
   ls -la scratchpad/
   
   # Archive important findings to docs/
   mv scratchpad/important_findings.md docs/ARCHITECTURE_DECISIONS.md
   
   # Delete temporary files
   rm scratchpad/temp_*.{py,json,md,txt}
   ```

## Project Structure

### Permanent Directories

- `src/` - Source code (never put temporary files here)
- `tests/` - Test files (never put temporary files here)
- `docs/` - Documentation (only final, reviewed docs)
- `data/` - Data files (source data, never modify)
- `scripts/` - Permanent utility scripts
- `scratchpad/` - Temporary files (safe to delete)

### Git Ignore

The `scratchpad/` directory should be in `.gitignore`:

```gitignore
# Temporary files
scratchpad/
*.tmp
*.temp
```

## Code Changes

### When Making Code Changes

1. **Always test** with `make ingest-fast` after implementing changes
2. **Update tests** when fixing bugs (add regression tests)
3. **Document** significant changes in appropriate `docs/` files
4. **Clean up** scratchpad files after epic completion

### Milestone Completion Workflow

When a **significant milestone** is reached (e.g., completing a major feature, fixing critical bugs, implementing a plan phase):

1. **Run Tests**:
   ```bash
   make test
   # Or: python3 -m pytest tests/ -v
   ```

2. **Run Smoke/Fast Test**:
   ```bash
   make ingest-fast
   # Verify ingestion completes successfully
   ```

3. **If Tests Pass**:
   ```bash
   # Stage changes
   git add .
   
   # Commit with descriptive message
   git commit -m "Milestone: [Brief description of what was completed]"
   
   # Push to remote
   git push
   ```

4. **If Tests Fail**:
   - Fix failing tests
   - Re-run tests until all pass
   - Then proceed with commit and push

**What Constitutes a Significant Milestone:**
- Completing a major feature or phase
- Fixing critical bugs or issues
- Implementing a complete plan phase
- Adding comprehensive error handling
- Completing documentation deliverables
- Performance optimizations

**What Does NOT Require Commit:**
- Minor refactoring (unless part of milestone)
- Debugging attempts
- Work-in-progress changes

### Code Review Checklist

Before marking work complete:
- [ ] All tests pass (`make test`)
- [ ] Smoke test passes (`make ingest-fast`)
- [ ] No temporary files in `src/`, `tests/`, or `docs/`
- [ ] Temporary files moved to `scratchpad/` or deleted
- [ ] Important findings documented in `docs/`
- [ ] No debug code left in production files
- [ ] Changes committed and pushed (if milestone reached)

## Documentation

### When to Create Documentation

**Create in `docs/`**:
- Architecture decisions
- Implementation guides
- Performance analysis
- Bug fixes with impact
- API documentation
- User guides

**Create in `scratchpad/`**:
- Draft documentation
- Temporary analysis
- Notes during development
- Debugging notes

### Documentation Naming

Use descriptive names:
- `docs/PERFORMANCE_OPTIMIZATIONS.md` ✅
- `docs/GRAPH_STRUCTURE_VALIDATION.md` ✅
- `scratchpad/draft_performance_notes.md` ✅
- `scratchpad/temp_analysis.md` ✅

## Best Practices

1. **Always use scratchpad** for temporary files
2. **Test before committing** - use `make ingest-fast` for quick validation
3. **Clean up after epics** - review and delete unnecessary scratchpad files
4. **Document important work** - move findings from scratchpad to `docs/` when complete
5. **Follow existing patterns** - check `docs/` for naming conventions

## Examples

### ✅ Good Practice

```bash
# Create temporary analysis
cat > scratchpad/entity_resolution_analysis.md << 'EOF'
# Entity Resolution Performance Analysis
...
EOF

# After completing epic, if findings are important:
mv scratchpad/entity_resolution_analysis.md docs/ENTITY_RESOLUTION_ANALYSIS.md

# Otherwise, delete:
rm scratchpad/entity_resolution_analysis.md
```

### ❌ Bad Practice

```bash
# Don't create temporary files in docs/
cat > docs/temp_analysis.md << 'EOF'
...

# Don't leave temporary scripts in scripts/
cat > scripts/debug_test.py << 'EOF'
...

# Don't create files in project root
cat > analysis.md << 'EOF'
...
```

## Questions?

If unsure where to place a file:
1. Is it temporary/debugging? → `scratchpad/`
2. Is it source code? → `src/`
3. Is it a test? → `tests/`
4. Is it final documentation? → `docs/`
5. Is it a permanent script? → `scripts/`

When in doubt, use `scratchpad/` - it's better to have temporary files there than scattered throughout the project.

