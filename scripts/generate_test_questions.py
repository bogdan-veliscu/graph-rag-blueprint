"""Generate test questions for benchmarking."""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def generate_questions(count: int = 400, output_file: str = "data/test_questions_400.json") -> None:
    """Generate test questions for benchmarking.
    
    Args:
        count: Number of questions to generate
        output_file: Path to save questions JSON file
    """
    # Template questions covering various legal topics
    templates = [
        "What is the maximum duration of a commercial lease?",
        "What is the filing fee for an appeal in civil court?",
        "What are the requirements for a valid contract?",
        "What is the statute of limitations for breach of contract?",
        "What are the penalties for non-compliance?",
        "What is the procedure for filing a lawsuit?",
        "What are the rights of tenants?",
        "What is the process for obtaining a license?",
        "What are the tax obligations for businesses?",
        "What is the legal framework for employment?",
        "What are the regulations for environmental protection?",
        "What is the procedure for dispute resolution?",
        "What are the requirements for data protection?",
        "What is the legal status of intellectual property?",
        "What are the rules for international trade?",
        "What is the procedure for company registration?",
        "What are the labor law requirements?",
        "What is the process for property transfer?",
        "What are the banking regulations?",
        "What is the legal framework for insurance?",
    ]
    
    questions = []
    for i in range(count):
        # Cycle through templates
        template = templates[i % len(templates)]
        # Add variation to make questions unique
        if i >= len(templates):
            questions.append({
                "question": f"{template} (Question {i+1})",
                "type": "objective",
                "category": "factual"
            })
        else:
            questions.append({
                "question": template,
                "type": "objective",
                "category": "factual"
            })
    
    # Save to file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)
    
    print(f"Generated {count} questions and saved to {output_file}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate test questions for benchmarking")
    parser.add_argument(
        "--count",
        type=int,
        default=400,
        help="Number of questions to generate (default: 400)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/test_questions_400.json",
        help="Output file path (default: data/test_questions_400.json)"
    )
    
    args = parser.parse_args()
    generate_questions(count=args.count, output_file=args.output)

