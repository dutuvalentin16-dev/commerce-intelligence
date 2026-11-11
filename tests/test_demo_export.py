"""A failed or incomplete dbt build must never become a publishable snapshot."""
import json

import pytest

from commerce_pipeline.export_demo import export


@pytest.mark.parametrize('statuses', [['pass'] * 41, ['pass'] * 41 + ['error']])
def test_export_rejects_incomplete_or_failed_build(tmp_path, monkeypatch, statuses):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'target').mkdir()
    (tmp_path / 'target/run_results.json').write_text(json.dumps({
        'results': [{'unique_id': f'model.example.m{i}', 'status': status}
                    for i, status in enumerate(statuses)],
    }))
    (tmp_path / 'target/manifest.json').write_text(json.dumps({'nodes': {
        f'model.example.m{i}': {'resource_type': 'model'} for i in range(42)
    }}))
    output = tmp_path / 'demo/data.json'
    with pytest.raises(ValueError, match='successful complete dbt build'):
        export(output)
    assert not output.exists()
