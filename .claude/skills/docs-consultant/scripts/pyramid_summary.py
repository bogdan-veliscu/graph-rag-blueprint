from pathlib import Path

LEVEL0 = Path('docs/00-portfolio-digest.md')
LEVEL1 = [
    Path('docs/10-build-process.md'),
    Path('docs/11-delegation-patterns.md'),
    Path('docs/12-claude-code-skills-and-tools.md'),
    Path('docs/20-reference-index.md'),
    Path('docs/22-root-data-index.md'),
]
DOMAINS = Path('docs/domains')


def tail(path: Path, lines: int = 20) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding='utf-8')
    split = text.strip().splitlines()
    return "\n".join(split[:lines])


def main() -> None:
    print("# Level 0 Snapshot\n")
    print(tail(LEVEL0, 80))
    print("\n# Level 1 Highlights\n")
    for path in LEVEL1:
        print(f"## {path.name}")
        print(tail(path, 20))
        print()
    print("# Domain Summaries\n")
    if DOMAINS.exists():
        for domain_file in sorted(DOMAINS.glob('*.md')):
            print(f"## {domain_file.stem}")
            print(tail(domain_file, 20))
            print()


if __name__ == "__main__":
    main()
