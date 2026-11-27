# Shared-agent conversation examples
Forty project-authored synthetic examples: eight each for CEO, Finance, Marketing, Operations and Strategy. Six per role are development cases; two per role (ten total) are held out. The application does not load this corpus as business evidence or load held-out answers in prompts.

Money/date values describe specific test contexts, never facts about a live business. Image examples specify behavior; they do not constitute generated assets or publishing permission. Voice interruption is checked separately in browser tests. No OpenAssistant text was copied.

Run `python scripts/evaluate_agent_examples.py --split development` against the current configured model and record actual results before considering fine-tuning. If credentials are absent, the report must say model checks are blocked and distinguish structured fallback behavior.
