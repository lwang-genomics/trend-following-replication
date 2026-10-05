"""Compile report/report.typ into the PDF report (run the study first)."""

import typst

from .config import REPORT_DIR, ROOT

PDF = REPORT_DIR / "trend_following_replication.pdf"


def main() -> None:
    typst.compile(str(REPORT_DIR / "report.typ"), output=str(PDF), root=str(ROOT))
    print(f"Saved {PDF.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
