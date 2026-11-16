from core.nlp import detect_intent, resolve_follow_up, normalize_question

def test_memory_paraphrases():
    assert detect_intent("is my memory expandable") == "memory"
    assert detect_intent("can I install another memory stick") == "memory"

def test_typo_in_extendable():
    assert detect_intent("rxtendable up to") == "memory"
    assert "extendable" in normalize_question("rxtendable up to")

def test_gpu_paraphrase():
    assert detect_intent("which graphics card is inside") == "gpu"

def test_follow_up_context():
    history = [{"role": "user", "content": "about ram"}]
    resolved = resolve_follow_up("rxtendable up to", history)
    assert detect_intent(resolved) == "memory"


def test_cpu_follow_up_inherits_cpu_topic():
    history = [{"role": "user", "content": "about cpu"}]
    resolved = resolve_follow_up("can it be extended", history)
    assert detect_intent(resolved) == "cpu"

def test_explicit_ram_follow_up_overrides_previous_cpu():
    history = [{"role": "user", "content": "about cpu"}]
    resolved = resolve_follow_up("can RAM be upgraded", history)
    assert detect_intent(resolved) == "memory"
