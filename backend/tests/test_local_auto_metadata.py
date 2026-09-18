from app.services.local_auto_metadata import infer_upload_metadata


def test_bibliographic_fields_are_not_generated_as_keywords() -> None:
    metadata = infer_upload_metadata(
        file_name="CVPR_2026_emotion_dataset.pdf",
        title="An Emotion Recognition Dataset for LLMs",
        doi=None,
        year=2026,
        venue="CVPR",
    )

    assert metadata.year == 2026
    assert metadata.conference == "CVPR"
    assert metadata.keywords == []
