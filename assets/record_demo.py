"""
Script to generate the SemShift terminal demo.

Run this script, then pipe the output through a GIF recorder:

  python assets/record_demo.py

To record a demo GIF:
  1. Install asciinema: pip install asciinema
  2. Run: asciinema rec demo.cast
  3. Inside the recording, run: python assets/record_demo.py
  4. Exit (Ctrl+D), then convert:
       pip install agg
       agg demo.cast assets/demo.gif
"""

import sys
import time

from semshift import compare_text
from semshift.core.report import print_rich_report
from rich.console import Console


def main() -> None:
    console = Console()

    console.print("\n[bold cyan]$ semshift compare examples/old_policy.md examples/new_policy.md --mode policy[/bold cyan]\n")
    time.sleep(0.5)

    result = compare_text(
        old=(
            "We do not share personal data with third parties.\n"
            "We retain logs for 30 days.\n"
            "Users can opt out of analytics at any time in Settings."
        ),
        new=(
            "We may share personal data with selected partners.\n"
            "We retain logs for 180 days.\n"
            "Analytics tracking is required to use the service."
        ),
        mode="policy",
        model="tfidf",
        old_label="examples/old_policy.md",
        new_label="examples/new_policy.md",
    )

    print_rich_report(result, console=console, top=3)


if __name__ == "__main__":
    main()
