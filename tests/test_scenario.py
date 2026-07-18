from dd4tester.scenario import load_scenario


def test_loads_yaml_scenario(tmp_path) -> None:
    scenario_file = tmp_path / "sample.yaml"
    scenario_file.write_text(
        """
name: smoke
host: 127.0.0.1
port: 4444
timeout: 3
database: runs/test.sqlite3
transcript_dir: transcripts
credential_name: dd4-login
steps:
  - wait_for: "login:"
    timeout: 2
  - send: "guest"
  - send_env: "DD4_PASSWORD"
  - pause: 0.1
""",
        encoding="utf-8",
    )

    scenario = load_scenario(scenario_file)

    assert scenario.name == "smoke"
    assert scenario.host == "127.0.0.1"
    assert scenario.port == 4444
    assert scenario.steps[0].action == "wait_for"
    assert scenario.steps[0].value == "login:"
    assert scenario.steps[2].action == "send_env"
    assert scenario.steps[2].value == "DD4_PASSWORD"
    assert scenario.steps[3].action == "pause"
    assert scenario.steps[3].value == 0.1
    assert scenario.credential_name == "dd4-login"
