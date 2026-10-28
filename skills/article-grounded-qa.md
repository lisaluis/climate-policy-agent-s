# Skill: Article-grounded question answering

## Goal
Answer questions only when the supplied article facts support the answer.

## Procedure
1. Classify the request: article Q&A, winter comparison, evidence review, agriculture/climate zones, or policy analysis.
2. Retrieve the most relevant facts from `data/facts.json`.
3. If the retrieved evidence does not directly support an answer, say: “I don't know from the assigned article.” Do not fill gaps with general knowledge.
4. Cite each material claim with fact IDs such as `[F3]`.
5. State the limits of evidence, especially the two-winter sample and correlation-versus-causation warning.
6. Ask a narrow follow-up only when it helps resolve an ambiguity.

## Never
- Invent numbers, facts, citations, or sources.
- Treat the article's reported study findings as proof of causality.
- Present a policy proposal as a recommendation made by the researchers.
- Claim to provide live AQI, a forecast, or farm-specific advice.
