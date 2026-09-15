# FastAPI Service Notes — Phase 4

## What we built
A FastAPI service (/score endpoint) wrapping the trained XGBoost model
and SHAP explainer, returning a risk score, flag decision (using our
Phase 3 chosen threshold of 0.8485), and top contributing features for
any transaction sent to it.

## Validation approach and a real lesson learned
Initial testing used a hand-crafted "suspicious-looking" synthetic
transaction, which scored surprisingly low (0.005). Investigated two
hypotheses: column ordering mismatch (ruled out -- verified identical to
training order) and a genuine API bug (ruled out -- reproduced the exact
known score, 0.9949, and exact known SHAP contributions for a real,
verified test-set transaction, transaction_id 5115795).

Conclusion: the API was correct all along; the hand-crafted test
transaction simply didn't resemble real fraud patterns the model
actually learned, despite looking intuitively suspicious to a human.

## Lesson for future API/ML validation
Hand-crafted test inputs based on human intuition about what "should"
look like fraud can be misleading when validating an ML-backed API.
The reliable validation method is reproducing a known, verified
ground-truth prediction from real data -- not inventing a plausible-
sounding example and trusting gut instinct about the expected outcome.
