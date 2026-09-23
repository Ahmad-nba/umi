from scripts.demo import run_demo


def test_phase9_cli_demo_runs_to_closed_issue(capsys):
    assert run_demo() == 0

    output = capsys.readouterr().out
    assert "Demo issue:" in output
    assert "Final status: CLOSED" in output
    assert "Notifications:" in output
