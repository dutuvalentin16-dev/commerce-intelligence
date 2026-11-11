"""A failed or incomplete dbt build must never become a publishable snapshot."""
import json

import pytest

from commerce_pipeline.export_demo import export


@pytest.mark.parametrize('statuses', [['pass'] * 41, ['pass'] * 41 + ['error']])
def test_export_rejects_incomplete_or_failed_build(tmp_path, monkeypatch, statuses):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'target').mkdir()
    (tmp_path / 'target/run_results.json').write_text(json.dumps({
        'results': [{'status': status} for status in statuses],
    }))
    output = tmp_path / 'demo/data.json'
    with pytest.raises(ValueError, match='successful complete dbt build'):
        export(output)
    assert not output.exists()
