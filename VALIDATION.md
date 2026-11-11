# Validation Record

## Original project validation

**11 November 2026:** The original project was checked in an environment with Python and Flask installed. Five `unittest` cases passed. The Flask test client returned HTTP 200 for the home page and HTTP 201 when creating a sample report, with three sample channels. These checks do not constitute a fresh virtual-environment installation or a full end-to-end browser acceptance test.

**9 November 2026:** A real Tavily request through the backend returned HTTP 201 and a single software-review page. This confirms the API integration was reachable at that time, **not** that the resulting recommendation was appropriate. No additional paid live API request was made during final packaging.

Original automated test output:

```text
test_changed_market_does_not_reuse_uk_recommendations (test_app.WorkflowTests.test_changed_market_does_not_reuse_uk_recommendations) ... ok
test_live_candidates_are_limited_and_deduplicated (test_app.WorkflowTests.test_live_candidates_are_limited_and_deduplicated) ... ok
test_missing_and_wrong_type_inputs (test_app.WorkflowTests.test_missing_and_wrong_type_inputs) ... ok
test_missing_key_reports_failure_without_fake_results (test_app.WorkflowTests.test_missing_key_reports_failure_without_fake_results) ... ok
test_saved_result_survives_app_restart (test_app.WorkflowTests.test_saved_result_survives_app_restart) ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.074s

OK
```

## English-language revision

The interface, server responses, sample report, tests, and project documentation were translated to English. The previously used one-time Chinese localisation module was removed; this is a fresh repository without the local report database. Verification of the revised source should be performed in an environment with Flask installed:

```bash
python -m pip install -r requirements.txt
python -m unittest -v
```

No API credentials or live Tavily results are included in the repository.
