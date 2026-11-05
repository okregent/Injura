from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from fastapi.testclient import TestClient

from apps.api.main import create_app
from apps.api.service import AnalysisError, Limits


def upload(client, content=b'fixture', **kwargs):
    return client.post('/v1/analyses', files={'video': ('../../private.mp4', content, 'video/mp4')},
                       data={'side': 'left', 'facing': 'right'}, **kwargs)


def test_upload_uses_private_temp_path_and_cleans_success_and_preserves_selection():
    observed = []
    def analyze(path, side, facing):
        observed.append(path)
        assert path.read_bytes() == b'fixture'
        assert path.name == 'upload.video'
        return {'selection': {'side': side, 'facing': facing}, 'coaching': 'pending_validation'}
    with TestClient(create_app(analyzer=analyze)) as client:
        assert client.get('/health').json()['status'] == 'ok'
        response = upload(client)
    assert response.status_code == 200
    assert response.json()['selection'] == {'side': 'left', 'facing': 'right'}
    assert observed and not observed[0].exists() and not observed[0].parent.exists()


@pytest.mark.parametrize('content,status,code', [(b'', 422, 'empty_upload'), (b'12345', 413, 'upload_too_large')])
def test_file_limits_prevent_inference(content, status, code):
    def forbidden(*args):
        pytest.fail('inference must not run')
    with TestClient(create_app(analyzer=forbidden, limits=Limits(file_bytes=4))) as client:
        response = upload(client, content)
    assert response.status_code == status and response.json()['error']['code'] == code


def test_streamed_body_without_content_length_is_bounded():
    with TestClient(create_app(analyzer=lambda *args: {}, limits=Limits(file_bytes=4, multipart_overhead=256))) as client:
        request = client.build_request('POST', '/v1/analyses', files={'video': ('v.mp4', b'x' * 1000, 'video/mp4')},
                                       data={'side': 'left', 'facing': 'left'})
        del request.headers['content-length']
        response = client.send(request)
    assert response.status_code == 413
    assert response.json()['error']['code'] == 'upload_too_large'


@pytest.mark.parametrize('failure,expected', [(AnalysisError('invalid_video', 'Invalid video.'), 422),
                                            (RuntimeError('secret-path-and-trace'), 500)])
def test_error_envelope_cleanup_and_no_internal_detail_leak(failure, expected):
    paths = []
    def analyze(path, *args):
        paths.append(path)
        raise failure
    with TestClient(create_app(analyzer=analyze)) as client:
        response = upload(client)
        assert upload(client).status_code == expected  # Admission is released.
    assert response.status_code == expected
    assert 'secret-path-and-trace' not in response.text
    assert all(not path.exists() and not path.parent.exists() for path in paths)


def test_invalid_fields_and_client_self_approval_are_not_accepted():
    with TestClient(create_app(analyzer=lambda *args: pytest.fail('must not infer'))) as client:
        assert client.post('/v1/analyses', json={}).status_code == 415
        invalid = client.post('/v1/analyses', files={'video': ('v.mp4', b'x', 'video/mp4')},
                              data={'side': 'auto', 'facing': 'left'})
        assert invalid.status_code == 422
        extra = client.post('/v1/analyses', files={'video': ('v.mp4', b'x', 'video/mp4')},
                            data={'side': 'left', 'facing': 'left', 'approved': 'true'})
        assert extra.status_code == 400
        assert client.get('/missing').json()['error']['code'] == 'not_found'


def test_busy_request_does_not_queue_another_inference():
    entered, release = Event(), Event()
    def analyze(*args):
        entered.set()
        assert release.wait(5)
        return {'ok': True}
    with TestClient(create_app(analyzer=analyze)) as client, ThreadPoolExecutor(max_workers=1) as executor:
        first = executor.submit(upload, client)
        assert entered.wait(5)
        try:
            busy = upload(client)
            assert busy.status_code == 429 and busy.headers['Retry-After'] == '1'
            assert client.get('/health').status_code == 200
        finally:
            release.set()
        assert first.result().status_code == 200


def test_openapi_exposes_required_explicit_fields():
    with TestClient(create_app()) as client:
        schema = client.get('/openapi.json').json()
    body = schema['paths']['/v1/analyses']['post']['requestBody']['content']['multipart/form-data']['schema']
    assert body['required'] == ['video', 'side', 'facing']


def test_local_preview_and_capabilities_and_malformed_multipart():
    with TestClient(create_app()) as client:
        page = client.get('/')
        assert page.status_code == 200 and 'Local analysis preview' in page.text
        script = client.get('/static/preview.js')
        assert script.status_code == 200 and 'application/javascript' in script.headers['content-type']
        assert script.headers['cache-control'] == 'no-store'
        capabilities = client.get('/v1/capabilities').json()
        assert capabilities['limits']['frames'] == 1800
        assert capabilities['capture_review_upload'] is False
        malformed = client.post('/v1/analyses', content=b'bad framing',
                                headers={'content-type': 'multipart/form-data; boundary=fixture'})
        assert malformed.status_code == 400


def test_invalid_limits_rejected():
    with pytest.raises(ValueError):
        Limits(file_bytes=True)


def test_cors_is_opt_in_loopback_only_and_not_an_authentication_mechanism():
    with TestClient(create_app()) as client:
        assert 'access-control-allow-origin' not in client.get('/health', headers={'Origin':'http://localhost:8081'}).headers
    with TestClient(create_app(dev_origins=('http://localhost:8081',))) as client:
        response = client.get('/health', headers={'Origin':'http://localhost:8081'})
        assert response.headers['access-control-allow-origin'] == 'http://localhost:8081'
        assert 'access-control-allow-credentials' not in response.headers
        assert 'access-control-allow-origin' not in client.get('/health', headers={'Origin':'https://example.com'}).headers
    with pytest.raises(ValueError):
        create_app(dev_origins=('https://example.com',))
