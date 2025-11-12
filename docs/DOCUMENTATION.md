# Documentation Index - Single Source of Truth

**Last Updated:** 2025-01-XX  
**Purpose:** Central index for all project documentation with clear single sources of truth

---

## 🎯 Quick Navigation

- **Getting Started:** See `README.md`
- **Current Status:** See `memory-bank/progress.md` and `memory-bank/active-context.md`
- **Architecture:** See `memory-bank/system-patterns.md` and `docs/ARCHITECTURE.md`
- **Technical Details:** See `memory-bank/tech-context.md`
- **Project Requirements:** See `memory-bank/project-brief.md`

---

## 📚 Core Documentation (Single Sources of Truth)

### Memory Bank - Authoritative Project State

The `memory-bank/` directory contains the **single source of truth** for project state:

| File | Purpose | When to Read |
|------|---------|--------------|
| `project-brief.md` | Core requirements, goals, scope | Start here for project overview |
| `product-context.md` | Why project exists, problems solved | Understanding product goals |
| `active-context.md` | Current work focus, recent changes | **Current status** - read first |
| `system-patterns.md` | Architecture, technical decisions | Understanding system design |
| `tech-context.md` | Technologies, setup, constraints | Setup and dependencies |
| `progress.md` | What works, what's left, status | **Current progress** - read first |

**⚠️ Important:** Always check Memory Bank files first - they are maintained as the authoritative source.

---

## 📖 User-Facing Documentation

### Getting Started
- **`README.md`** - Main entry point, setup instructions, quick start
  - ⚠️ **Status:** Needs update (still mentions NetworkX)
  - **Single Source:** Setup and usage instructions

### Architecture & Design
- **`docs/ARCHITECTURE.md`** - Comprehensive system architecture
  - ⚠️ **Status:** Needs update (mentions NetworkX)
  - **Single Source:** System architecture overview
- **`docs/ARCHITECTURE_DECISIONS.md`** - Architecture Decision Records (ADRs)
  - ✅ **Status:** Current
  - **Single Source:** Technical decision rationale

### Execution Guides
- **`docs/MANUAL_EXECUTION_GUIDE.md`** - Step-by-step execution instructions
  - ✅ **Status:** Current
  - **Single Source:** How to run the system
- **`docs/QUICK_REFERENCE.md`** - Quick command reference
  - ✅ **Status:** Current
  - **Single Source:** Command cheat sheet
- **`docs/DEMO_GUIDE.md`** - Demo execution guide
  - ✅ **Status:** Current
  - **Single Source:** Demo preparation and execution

---

## 🔧 Implementation Documentation

### Best Practices
- **`docs/LESSONS_LEARNED_VALIDATION.md`** - Validated lessons learned
  - ✅ **Status:** Current
  - **Single Source:** Best practices and lessons

### Visual Reference
- **`docs/PIPELINE_DIAGRAMS.txt`** - Visual pipeline diagrams
  - ✅ **Status:** Current
  - **Single Source:** Visual architecture reference

---

## 📊 Status Documentation

### Current Status
- **`memory-bank/progress.md`** ⭐ **PRIMARY** - Current progress and status
- **`memory-bank/active-context.md`** ⭐ **PRIMARY** - Current work focus

**Note:** Memory Bank files are the single source of truth for project status. All status files have been consolidated.

---

## 🗂️ Reference Documentation

### Visual Diagrams
- **`docs/PIPELINE_DIAGRAMS.txt`** - Visual pipeline and architecture diagrams
  - ✅ **Status:** Current
  - **Single Source:** Visual reference

---

## 📁 Archived Documentation

Historical documentation has been moved to `docs/archive/`:

### Archive Structure
- **`docs/archive/implementation/`** - Completed implementation plans
  - NetworkX removal plans and implementation
  - FalkorDB migration and execution plans
  - Best practices implementation plans
  - Makefile simplification summary
  - Demo testing setup summary

- **`docs/archive/assessments/`** - Historical assessments and evaluations
  - Codebase evaluations
  - Best practices evaluations
  - Assumption verifications
  - Demo readiness assessments

- **`docs/archive/analysis/`** - Historical analysis documents
  - Codebase exploration summaries
  - Bottleneck analysis
  - Relationship extraction analysis
  - Timeout analysis
  - Architecture visual maps (outdated)

- **`docs/archive/handover/`** - Old handover notes
  - Technical handover notes
  - Client handover documentation

- **`docs/archive/results/`** - Historical benchmark results
  - Day 3.5 breakthrough (NetworkX results, not reproducible)

- **`docs/archive/planning/`** - Historical planning documents
  - Phase plans and execution summaries
  - Gap analysis documents
  - Explainability design (implemented)

**Note:** Archived files are kept for historical reference only. For current information, see Memory Bank files.

---

## 🔄 Documentation Maintenance Rules

### Single Source of Truth Principle

1. **Memory Bank is authoritative** for:
   - Current project status
   - Active work focus
   - System patterns and architecture
   - Technical context

2. **User-facing docs** (`README.md`, `docs/ARCHITECTURE.md`) should:
   - Reference Memory Bank for current status
   - Be kept up-to-date with major changes
   - Not duplicate Memory Bank content

3. **Status files** should:
   - Point to Memory Bank as primary source
   - Be archived when superseded
   - Not duplicate Memory Bank content

### When to Update Documentation

- **Memory Bank:** After every significant change
- **README.md:** When setup/usage changes
- **ARCHITECTURE.md:** When architecture changes
- **Status files:** Archive when superseded by Memory Bank

### Documentation Update Checklist

- [ ] Update Memory Bank files first
- [ ] Update README.md if setup/usage changed
- [ ] Update ARCHITECTURE.md if architecture changed
- [ ] Archive outdated status files
- [ ] Update this index if structure changes

---

## 📝 Documentation Gaps & TODOs

### Immediate Actions Needed

1. **Update README.md**
   - [ ] Remove NetworkX references
   - [ ] Update to FalkorDB-only architecture
   - [ ] Point to Memory Bank for current status

2. **Update ARCHITECTURE.md**
   - [ ] Remove NetworkX references
   - [ ] Update to FalkorDB architecture
   - [ ] Reference Memory Bank for current patterns

3. **Documentation Consolidation** ✅
   - [x] Archive completed implementation plans
   - [x] Archive historical analysis documents
   - [x] Remove redundant status files
   - [x] Remove non-project documentation
   - [x] Update documentation index

---

## 🔍 Finding Documentation

### By Topic

**Project Overview:**
- `memory-bank/project-brief.md` (requirements)
- `memory-bank/product-context.md` (why it exists)

**Current Status:**
- `memory-bank/progress.md` ⭐
- `memory-bank/active-context.md` ⭐

**Architecture:**
- `memory-bank/system-patterns.md` ⭐
- `docs/ARCHITECTURE.md`
- `docs/ARCHITECTURE_DECISIONS.md`

**Setup & Usage:**
- `README.md`
- `docs/MANUAL_EXECUTION_GUIDE.md`
- `docs/QUICK_REFERENCE.md`

**LLM Configuration:**
- Supports three providers: Ollama (local), Anthropic (cloud), OpenRouter (cloud)
- See `README.md` section "Configure LLM Provider" for setup instructions
- Configuration in `src/config.py` (`LLMConfig` class)

**Best Practices:**
- `docs/LESSONS_LEARNED_VALIDATION.md`

**Visual Reference:**
- `docs/PIPELINE_DIAGRAMS.txt`

### By Audience

**New Developers:**
1. `README.md` (setup)
2. `memory-bank/project-brief.md` (overview)
3. `memory-bank/system-patterns.md` (architecture)
4. `docs/MANUAL_EXECUTION_GUIDE.md` (how to run)

**Current Developers:**
1. `memory-bank/active-context.md` (what's happening now)
2. `memory-bank/progress.md` (what's done)
3. `docs/QUICK_REFERENCE.md` (commands)

**Architects/Reviewers:**
1. `memory-bank/system-patterns.md` (patterns)
2. `docs/ARCHITECTURE_DECISIONS.md` (decisions)
3. `docs/ARCHITECTURE.md` (overview)

**Project Managers:**
1. `memory-bank/progress.md` (status)
2. `memory-bank/active-context.md` (current focus)
3. `docs/DOCUMENTATION.md` (documentation index)

---

## 📌 Key Principles

1. **Memory Bank is authoritative** - Always check Memory Bank first
2. **Single source of truth** - Don't duplicate, reference instead
3. **Archive outdated content** - Move to `docs/archive/` when superseded
4. **Update this index** - When documentation structure changes
5. **Link, don't duplicate** - Reference Memory Bank rather than copying

---

**Last Updated:** 2025-01-XX  
**Maintained By:** Project team  
**Questions?** Check Memory Bank first, then this index.

