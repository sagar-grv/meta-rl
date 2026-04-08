from scripts.judging_audit import run_judging_audit


def test_judging_audit_checks_all_pass_locally():
    checks = run_judging_audit()

    assert checks
    assert all(check.passed for check in checks)


def test_judging_audit_contains_expected_layers():
    checks = run_judging_audit()
    names = {check.name for check in checks}

    assert "interface_contract" in names
    assert "policy_ordering" in names
    assert "hard_task_challenge" in names
    assert "determinism" in names
