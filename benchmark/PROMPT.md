Assess this repository for India's Digital Personal Data Protection Act, 2023 and DPDP Rules, 2025. Decide whether and how the Act applies to what the code does, and find the privacy and security problems in the code. Do not modify the application code.

Write your result to `dpdp-submission.yaml` in the current directory, exactly in this format:

```yaml
overall_status: applicable | partially-applicable | potentially-applicable | not-currently-applicable | undetermined
citations: ["Act s.3(a)"]            # provisions your applicability conclusion relies on
findings:
  - title: "short description"
    file: path/relative/to/repo.py
    line: 42                         # or lines: [40, 45]
    category: legal-gap | security-vulnerability | operational-weakness | best-practice
    severity: critical | high | medium | low
    mandatory: true                  # true only if it is a DPDP obligation that applies here
    citations: ["Act s.8(5)", "Rules r.6(1)(b)"]
legal_questions: ["questions a lawyer must answer, if any"]
summary: "two or three sentences"
```

Cite provisions as `Act s.N(x)` or `Rules r.N(x)`. Then give me a short summary.
