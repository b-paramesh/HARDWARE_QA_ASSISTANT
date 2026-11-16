from core.assistant import HardwareAssistant

def test_expected_hardware_sections():
    assistant = HardwareAssistant()
    assert {"cpu", "memory", "storage", "gpu", "memory_topology"} <= set(assistant.get_all_info())
