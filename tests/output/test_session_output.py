from datetime import datetime

from src.output.session_output import (
    create_session_output_layout,
    debug_csv_paths,
    relative_to_output_root,
    sessions_dir_from_config,
)


def _config(tmp_path):
    return {
        "output": {
            "excel_output_dir": str(tmp_path),
            "sessions_subdir": "sessions",
            "record_video": True,
            "video_fps": 10.0,
        }
    }


def test_creates_session_folder_structure(tmp_path):
    start = datetime(2026, 4, 27, 15, 30, 12)

    layout = create_session_output_layout(_config(tmp_path), start)

    assert layout.session_dir == tmp_path / "sessions" / "2026-04-27_15h30m12s"
    assert layout.gap_frames_dir.is_dir()
    assert layout.video_dir.is_dir()
    assert layout.video_path == layout.video_dir / "sessao_2026-04-27_15h30_annotated.mp4"


def test_creates_unique_session_folder_when_same_second_exists(tmp_path):
    config = _config(tmp_path)
    start = datetime(2026, 4, 27, 15, 30, 12)

    first = create_session_output_layout(config, start)
    second = create_session_output_layout(config, start)

    assert first.session_dir.name == "2026-04-27_15h30m12s"
    assert second.session_dir.name == "2026-04-27_15h30m12s_02"


def test_debug_csv_paths_includes_session_and_legacy_files(tmp_path):
    config = _config(tmp_path)
    legacy = tmp_path / "debug_legacy.csv"
    legacy.write_text("legacy", encoding="utf-8")

    session_dir = sessions_dir_from_config(config) / "2026-04-27_15h30m12s"
    session_dir.mkdir(parents=True)
    session_csv = session_dir / "debug_session.csv"
    session_csv.write_text("session", encoding="utf-8")

    assert set(debug_csv_paths(config)) == {legacy, session_csv}


def test_relative_to_output_root_uses_compact_label(tmp_path):
    config = _config(tmp_path)
    path = tmp_path / "sessions" / "abc" / "debug.csv"

    assert relative_to_output_root(path, config) == "sessions/abc/debug.csv"
