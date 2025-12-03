import pytest
from nlp_service.app.information_system_strategy import InformationSystemStrategy
from nlp_service.app.nlp_config import NLPConfig

@pytest.fixture
def strategy():
    config = NLPConfig()
    return InformationSystemStrategy(config_settings=config.config, nlp_model=None)

def test_false_positive_gistratsiya(strategy):
    text = "гистрация"
    detections = strategy.detect_information_systems_in_text(text)
    assert not detections, f"False positive detected for 'гистрация': {detections}"

def test_false_positive_gistrirovannykh(strategy):
    text = "гистрированных"
    detections = strategy.detect_information_systems_in_text(text)
    assert not detections, f"False positive detected for 'гистрированных': {detections}"

def test_true_positive_gis_jkh(strategy):
    text = "ГИС ЖКХ"
    detections = strategy.detect_information_systems_in_text(text)
    assert any("ГИС" in d["original_value"] for d in detections), f"True positive not detected for 'ГИС ЖКХ': {detections}"

def test_true_positive_egisufhd(strategy):
    text = "ЕГИСУФХД"
    detections = strategy.detect_information_systems_in_text(text)
    assert any("ЕГИС" in d["original_value"] for d in detections), f"True positive not detected for 'ЕГИСУФХД': {detections}"
