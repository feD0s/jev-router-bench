# Review package for the owner

Status: **pending**. AI-authored rules and labels, not human-approved ground truth.
Review [business rules](business-rules.md) first and the [dataset](dataset-card.md).

Design choices requiring judgment:

1. Unknown number / missing order / multiple numbers → operator for clarification.
2. Active change or human request wins over status and FAQ; valid status wins over FAQ.
3. General «how to return/cancel» → answer; actual refund/cancellation → operator.
4. Anger/delay without requested remedy may remain status; compensation → operator.
5. Negation, quotation and completed history are not current actions.
6. Prompt injection without a real shop request → operator; otherwise ignore injection.
7. Fixtures assume authorized access to known orders; ownership is outside this experiment.

Concrete cases to inspect in `data/final-v1.jsonl`:

| ID | Boundary | AI label |
|---|---|---|
| final-020 | Selected order + short assembly question | status |
| final-036 | Lost number, no selection | operator |
| final-039 | Two known orders, one-route constraint | operator |
| final-065 | Status + storage FAQ | status |
| final-067 | Angry delay with no remedy | status |
| final-068 | Current number overrides selected one | status |
| final-072 | Conditional cancellation alongside status | operator |
| final-074 | Letter O inside order ID | operator |
| final-077 | «Да, сделайте» resolves prior address change | operator |
| final-081 | Cancellation procedure, action negated | answer |
| final-088 | Why cash is unavailable, operator negated | answer |
| final-090 | Selected order irrelevant to product FAQ | answer |
| final-097 | Only instruction to classifier, no shop request | operator |

Review all labels as desired; this shortlist highlights business ambiguity, not
measured model errors. Semantic similarity across splits also needs a human look.

After actual confirmation, update `data/owner-review.json`: approved, reviewer,
reviewed_on, decisions/label corrections, exact sha256 from freeze. Agent must not
mark approval on its own. Budget is a separate explicit human decision.
Proposal: one final paired pass, **up to $1 including retries/errors**, at most
400 HTTP attempts. Dev is estimated separately; agree whether it shares that cap.
No money has been spent. [Concrete planning estimate](budget-proposal.json).
