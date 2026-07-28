"""Regression: progress prints must not ZeroDivisionError when episodes < 10."""


def test_progress_every_never_zero():
    for num_episodes in (1, 5, 9, 10, 100):
        progress_every = max(1, num_episodes // 10)
        assert progress_every >= 1
        # modulo must be defined
        for episode in range(num_episodes):
            _ = (episode + 1) % progress_every


def test_source_uses_max_guard():
    from pathlib import Path
    src = Path(__file__).with_name("test_rl_learning.py").read_text()
    assert "progress_every = max(1, num_episodes // 10)" in src
