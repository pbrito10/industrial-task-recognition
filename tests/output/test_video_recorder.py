import numpy as np
import pytest

from src.output.video_recorder import VideoRecorder


def test_rejects_non_positive_fps(tmp_path):
    with pytest.raises(ValueError):
        VideoRecorder(tmp_path / "video.mp4", 0)


def test_disabled_recorder_does_not_create_file(tmp_path):
    path = tmp_path / "video.mp4"
    recorder = VideoRecorder(path, 10.0, enabled=False)

    recorder.write(np.zeros((10, 10, 3), dtype=np.uint8))
    recorder.close()

    assert not path.exists()
