# Sample contracts

Real contracts from public SEC EDGAR filings, for testing parsing and chunking.
Each is available as the original `.htm` exhibit plus converted `.docx` / `.pdf`.

| File | Type | Source |
|---|---|---|
| `employment_agreement.*` | Employment agreement (with non-compete) | Citizens Independent Bancorp — [EDGAR](https://www.sec.gov/Archives/edgar/data/1553830/000114420416076808/v429593_ex10-1.htm) |
| `nda.*` | Non-disclosure agreement | Dorman Products — [EDGAR](https://www.sec.gov/Archives/edgar/data/868780/000156459022005966/dorm-ex1016_838.htm) |
| `credit_agreement.*` | Credit agreement (with Events of Default) | BioTime Inc — [EDGAR](https://www.sec.gov/Archives/edgar/data/876343/000087634308000004/ex10_1.htm) |
| `license_agreement.*` | License agreement (with indemnification) | Talis Biomedical — [EDGAR](https://www.sec.gov/Archives/edgar/data/1584751/000095017023009197/tlis-ex10_22.htm) |
| `services_agreement.*` | Technical services agreement | Energy Exploration Technologies — [EDGAR](https://www.sec.gov/Archives/edgar/data/1009922/000113717107000050/technicalagree.htm) |

Notes:
- `.docx` files were converted from the EDGAR HTML with macOS `textutil` and keep heading/paragraph structure.
- `.pdf` files were converted via plain text (`cupsfilter`), so they are text-only PDFs — good for text extraction tests,
  but for layout-heavy PDF tests (tables, multi-column) add a few scanned/native contract PDFs later (CUAD_v1.zip has 500+).
- The NDA uses deep hierarchical clause numbering (`1.` → `1.1` → `6.1.1.1`) — a good stress test for structure-aware chunking.
- The credit agreement is the long one (~280 KB) — use it to test chunk-size limits and section-label carrying.

## Chunking test questions (for manual eval)

- Employment: "What are the non-compete restrictions and how long do they last?"
- NDA: "What counts as Confidential Information, and what are the exclusions?"
- Credit: "What are the Events of Default?"
- License: "Who indemnifies whom, and what triggers it?"
- Services: "How can the agreement be terminated?"
- Any: "What is the governing law?" / "What happens on breach?"
- Negative test (should answer 'Not found in the document'): "What is the purchase price of the aircraft?"
