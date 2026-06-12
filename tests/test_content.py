"""Validate all benchmark content against the shared contract schemas.

Run with the plugin venv (ScenarioConfig comes from checkmaite-plugin-custody):
    /Users/khan/openteams/checkmaite-plugin-custody/.venv/bin/pytest tests/ -v
"""

from pathlib import Path

import pytest
import yaml

from checkmaite_plugin_custody.custody_schemas import ScenarioConfig

ROOT = Path(__file__).parent.parent
SCENARIO_FILES = sorted((ROOT / "scenarios").glob("*.yaml"))

EXPECTED_IDS = {"A-baseline", "B-temp-loss", "C-confuser", "D-noisy-fusion", "E-ddil", "F-adversarial"}


def _load(path: Path) -> ScenarioConfig:
    return ScenarioConfig.model_validate(yaml.safe_load(path.read_text()))


def test_all_six_scenarios_present_with_expected_ids() -> None:
    assert {_load(p).scenario_id for p in SCENARIO_FILES} == EXPECTED_IDS


@pytest.mark.parametrize("path", SCENARIO_FILES, ids=lambda p: p.name)
def test_scenario_validates_against_contract_schema(path: Path) -> None:
    config = _load(path)
    assert config.scenario_id == path.stem  # filename == scenario_id
    if config.dataset == "visdrone-mot":
        assert config.gt_track_id is not None, "VisDrone scenarios are GT-scored"
    assert config.target_spec and config.task_prompt


def test_b_has_loss_window() -> None:
    config = _load(ROOT / "scenarios" / "B-temp-loss.yaml")
    assert config.loss_windows, "scenario B is the temporary-loss scenario"


def test_d_scripts_an_untruthful_cue() -> None:
    config = _load(ROOT / "scenarios" / "D-noisy-fusion.yaml")
    assert any(not cue.is_truthful for cue in config.cue_script)


def test_e_has_fault_profile() -> None:
    config = _load(ROOT / "scenarios" / "E-ddil.yaml")
    assert config.fault_profile is not None and config.fault_profile.rules


def test_f_injection_cue_is_flagged_untruthful() -> None:
    config = _load(ROOT / "scenarios" / "F-adversarial.yaml")
    injections = [cue for cue in config.cue_script if "SYSTEM OVERRIDE" in cue.content]
    assert injections, "scenario F must embed the prompt injection in a cue"
    assert all(not cue.is_truthful for cue in injections)
    assert config.perturbation is not None, "scenario F stacks a visual perturbation"


@pytest.mark.parametrize("name", ["citation", "explanation", "uncertainty"])
def test_rubrics_have_scoring_anchors_and_json_instruction(name: str) -> None:
    text = (ROOT / "rubrics" / f"{name}.md").read_text()
    for anchor in ("1.0", "0.5", "0.0"):
        assert anchor in text, f"{name}.md missing scoring anchor {anchor}"
    assert '"score"' in text and '"reasons"' in text, f"{name}.md must show the required JSON shape"


def test_scenario_config_with_explicit_designation_validates() -> None:
    """ScenarioConfig accepts an explicit designation block (VIRAT-style pin).

    VisDrone scenarios rely on GT-derived designation (designation=None in YAML);
    VIRAT scenarios (no GT) will pin it manually.  This test pins the schema
    accepts an explicit designation so future VIRAT scenarios can use it.
    """
    from checkmaite_plugin_custody.custody_schemas import Designation

    cfg = ScenarioConfig(
        scenario_id="A-baseline",
        dataset="visdrone-mot",
        sequence_id="uav0000137_00458_v",
        target_spec="white SUV travelling north",
        gt_track_id=12,
        task_prompt="Maintain custody of the white SUV.",
        designation=Designation(frame=0, x=25.0, y=40.0),
    )
    assert cfg.designation is not None
    assert cfg.designation.frame == 0
    assert cfg.designation.x == 25.0
    assert cfg.designation.y == 40.0

    # Round-trip via model_validate to confirm full serialization works
    again = ScenarioConfig.model_validate(cfg.model_dump())
    assert again.designation == cfg.designation


def test_manifest_records_provenance_and_license() -> None:
    manifest = yaml.safe_load((ROOT / "datasets" / "manifest.yaml").read_text())
    ids = {d["id"] for d in manifest["datasets"]}
    assert ids == {"visdrone-mot", "virat-aerial", "seadronessee"}
    for dataset in manifest["datasets"]:
        for field in ("name", "s3_prefix", "source_url", "license", "citation", "ground_truth", "used_for"):
            assert dataset.get(field), f"{dataset['id']} missing {field}"
