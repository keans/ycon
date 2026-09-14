import threading

from ycon import load


def test_include_cycle_detection_is_isolated_per_thread(tmp_path):
    """A load() in one thread must not see another thread's include stack."""
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    a.write_text("value: !include b.yaml\n")
    b.write_text("value: from_b\n")

    results = {}
    errors = {}
    barrier = threading.Barrier(2)

    def run(name, path):
        barrier.wait()
        try:
            results[name] = load(path)
        except Exception as exc:  # noqa: BLE001 - surfaced via `errors`
            errors[name] = exc

    threads = [
        threading.Thread(target=run, args=("a", a)),
        threading.Thread(target=run, args=("b", b)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == {}
    assert results["a"] == {"value": {"value": "from_b"}}
    assert results["b"] == {"value": "from_b"}
