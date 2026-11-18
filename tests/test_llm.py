import io
import json
from urllib.error import HTTPError, URLError
from unittest.mock import Mock

import pytest

from app import llm, pipeline


@pytest.fixture(autouse=True)
def isolated_api(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'test-key')
    monkeypatch.setattr(llm, 'build_system_prompt', lambda: 'SQL system instructions')
    monkeypatch.setattr(llm.request, 'urlopen', Mock(side_effect=AssertionError('Unexpected network')))
    monkeypatch.setattr(pipeline, 'write_log', Mock())


def reply(monkeypatch, text, finish='STOP'):
    envelope = {'candidates': [{'finishReason': finish, 'content': {'parts': [{'text': text}]}}]}
    call = Mock(return_value=io.BytesIO(json.dumps(envelope).encode()))
    monkeypatch.setattr(llm.request, 'urlopen', call)
    return call


def test_request_and_retry_context(monkeypatch):
    result = {'status': 'ok', 'sql': 'SELECT CustomerID FROM Customers', 'assumption': '', 'message': 'Sonuç'}
    call = reply(monkeypatch, json.dumps(result))
    assert llm.generate_sql('Müşteriler kim?', 'no such column: ID') == result
    req = call.call_args.args[0]
    payload = json.loads(req.data)
    assert req.full_url.endswith(':generateContent')
    assert 'test-key' not in req.full_url
    assert req.get_header('X-goog-api-key') == 'test-key'
    assert payload['systemInstruction']['parts'][0]['text'] == 'SQL system instructions'
    assert payload['contents'][1]['role'] == 'model'
    assert len(payload['contents']) == len(llm.FEW_SHOT_EXAMPLES) * 2 + 1
    assert 'no such column: ID' in payload['contents'][-1]['parts'][0]['text']
    assert payload['generationConfig']['responseMimeType'] == 'application/json'
    assert call.call_args.kwargs['timeout'] == 120


def test_missing_key(monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY')
    with pytest.raises(llm.ModelUnavailableError, match='GEMINI_API_KEY'):
        llm.generate_sql('Müşteriler kim?')


@pytest.mark.parametrize('code', [400, 401, 403, 404, 429, 500, 503])
def test_http_errors_hide_provider_details(monkeypatch, code):
    monkeypatch.setattr(llm.request, 'urlopen', Mock(side_effect=HTTPError('url', code, 'test-key', {}, None)))
    with pytest.raises(llm.ModelUnavailableError) as caught:
        llm.generate_sql('Müşteriler kim?')
    assert str(code) in str(caught.value)
    assert 'test-key' not in str(caught.value)


@pytest.mark.parametrize('error', [TimeoutError('test-key'), URLError('test-key')])
def test_connection_error(monkeypatch, error):
    monkeypatch.setattr(llm.request, 'urlopen', Mock(side_effect=error))
    with pytest.raises(llm.ModelUnavailableError) as caught:
        llm.generate_sql('Müşteriler kim?')
    assert 'test-key' not in str(caught.value)


@pytest.mark.parametrize('text,finish', [('', 'STOP'), ('invalid', 'STOP'), ('{}', 'STOP'),
    ('{"status":"ok","sql":""}', 'STOP'), ('{"status":"ok","sql":"SELECT 1"}', 'MAX_TOKENS'),
    ('{}', 'SAFETY')])
def test_invalid_output(monkeypatch, text, finish):
    reply(monkeypatch, text, finish)
    with pytest.raises(llm.ModelOutputError):
        llm.generate_sql('Müşteriler kim?')


@pytest.mark.parametrize('envelope', [{}, {'candidates': []}, {'promptFeedback': {'blockReason': 'SAFETY'}}, None])
def test_missing_candidate(monkeypatch, envelope):
    monkeypatch.setattr(llm.request, 'urlopen', Mock(return_value=io.BytesIO(json.dumps(envelope).encode())))
    with pytest.raises(llm.ModelOutputError):
        llm.generate_sql('Müşteriler kim?')


@pytest.mark.parametrize('status', ['clarify', 'unsupported'])
def test_no_sql_for_non_ok(monkeypatch, status):
    reply(monkeypatch, json.dumps({'status': status, 'sql': 'SELECT 1', 'message': 'Açıklama'}))
    assert llm.generate_sql('Soru')['sql'] == ''


def test_pipeline_success(monkeypatch):
    reply(monkeypatch, json.dumps({'status': 'ok', 'sql': 'SELECT COUNT(*) AS total FROM Customers'}))
    result = pipeline.ask('Kaç müşterimiz var?')
    assert result['status'] == 'success'
    assert result['rows'] == [{'total': 200}]


def test_model_sql_still_validated(monkeypatch):
    reply(monkeypatch, json.dumps({'status': 'ok', 'sql': 'DELETE FROM Customers'}))
    assert pipeline.ask('Müşterileri sil')['status'] == 'rejected'


def test_direct_sql_needs_no_api(monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY')
    assert pipeline.ask('SELECT COUNT(*) AS total FROM Customers')['rows'] == [{'total': 200}]
    assert pipeline.ask('SELECT * FROM Customers; DELETE FROM Customers')['status'] == 'rejected'


def test_pipeline_missing_key(monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY')
    assert pipeline.ask('Kaç müşterimiz var?')['error_type'] == 'model_unavailable'


def test_pipeline_invalid_response(monkeypatch):
    reply(monkeypatch, 'bad json')
    assert pipeline.ask('Kaç müşterimiz var?')['error_type'] == 'invalid_model_response'
