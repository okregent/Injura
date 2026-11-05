"""Local development API: uvicorn apps.api.main:app --host 127.0.0.1."""

from pathlib import Path
from dataclasses import asdict
from tempfile import TemporaryDirectory
from threading import Lock

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.responses import HTMLResponse
from python_multipart.exceptions import MultipartParseError
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException
from starlette.formparsers import MultiPartException

from apps.api.service import AnalysisError, Limits, analyze_video


def error_response(status, code, message):
    return JSONResponse(status_code=status, content=dict(schema_version=1, error=dict(code=code, message=message)))


class BodyLimit:
    """Count received body bytes even without Content-Length."""

    def __init__(self, app, maximum):
        self.app, self.maximum = app, maximum

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        lengths = [value for key, value in scope['headers'] if key == b'content-length']
        if lengths and (len(lengths) != 1 or not lengths[0].isdigit()):
            return await error_response(400, 'invalid_length', 'Invalid Content-Length.')(scope, receive, send)
        if lengths and int(lengths[0]) > self.maximum:
            return await error_response(413, 'upload_too_large', 'Upload exceeds the request size limit.')(scope, receive, send)
        received = 0

        async def bounded_receive():
            nonlocal received
            event = await receive()
            if event['type'] == 'http.request':
                received += len(event.get('body', b''))
                if received > self.maximum:
                    scope['injura.upload_too_large'] = True
                    # The multipart parser closes partial spool files on this exception.
                    raise MultiPartException('Upload exceeds the request size limit.')
            return event

        await self.app(scope, bounded_receive, send)


def create_app(*, analyzer=None, limits=Limits()):
    app = FastAPI(title='Injura local analysis API', version='0.1.0')
    app.add_middleware(BodyLimit, maximum=limits.file_bytes + limits.multipart_overhead)
    admission = Lock()
    service = analyzer or (lambda path, side, facing: analyze_video(path, side, facing, limits=limits))

    @app.exception_handler(HTTPException)
    async def http_error(request, exception):
        if request.scope.get('injura.upload_too_large'):
            return error_response(413, 'upload_too_large', 'Upload exceeds the request size limit.')
        messages = {400: ('invalid_multipart', 'Malformed multipart request.'),
                    404: ('not_found', 'Endpoint not found.'), 405: ('method_not_allowed', 'Method not allowed.')}
        code, message = messages.get(exception.status_code, ('request_error', 'Request could not be processed.'))
        return error_response(exception.status_code, code, message)

    @app.get('/health')
    async def health():
        return dict(status='ok', service='injura', schema_version=1)

    @app.get('/v1/capabilities')
    async def capabilities():
        return dict(schema_version=1, limits=asdict(limits), exercise='squat',
                    selection_required=['side', 'facing'], coaching='pending_validation',
                    capture_review_upload=False, personal_baseline_upload=False)

    @app.get('/', response_class=HTMLResponse, include_in_schema=False)
    async def preview():
        return HTMLResponse(Path(__file__).with_name('index.html').read_text(encoding='utf-8'))

    @app.post('/v1/analyses', openapi_extra={'requestBody': {'required': True, 'content': {
        'multipart/form-data': {'schema': {'type': 'object', 'required': ['video', 'side', 'facing'],
            'additionalProperties': False, 'properties': {'video': {'type': 'string', 'format': 'binary'},
                'side': {'type': 'string', 'enum': ['left', 'right']},
                'facing': {'type': 'string', 'enum': ['left', 'right']}}}}}}})
    async def analyze(request: Request):
        if request.headers.get('content-type', '').split(';', 1)[0].strip().lower() != 'multipart/form-data':
            return error_response(415, 'multipart_required', 'Use multipart/form-data with video, side and facing.')
        if not admission.acquire(blocking=False):
            response = error_response(429, 'analysis_busy', 'One analysis is already running; retry later.')
            response.headers['Retry-After'] = '1'
            return response
        try:
            async with request.form(max_files=1, max_fields=2, max_part_size=limits.multipart_overhead) as form:
                if set(form) != {'video', 'side', 'facing'} or any(len(form.getlist(key)) != 1 for key in form):
                    return error_response(422, 'invalid_fields', 'Supply exactly one video, side and facing.')
                video, side, facing = form['video'], form['side'], form['facing']
                if not isinstance(video, UploadFile) or side not in ('left', 'right') or facing not in ('left', 'right'):
                    return error_response(422, 'invalid_fields', 'Video must be a file; side and facing must be left or right.')
                if video.content_type not in ('video/mp4', 'video/quicktime', 'application/octet-stream'):
                    return error_response(415, 'unsupported_media_type', 'Supported upload hints are MP4, MOV or binary video.')
                with TemporaryDirectory(prefix='injura-upload-') as directory:
                    path, total = Path(directory) / 'upload.video', 0
                    with path.open('xb') as handle:
                        while True:
                            chunk = await video.read(64 * 1024)
                            if not chunk:
                                break
                            total += len(chunk)
                            if total > limits.file_bytes:
                                return error_response(413, 'upload_too_large', 'Video exceeds the file size limit.')
                            handle.write(chunk)
                    if not total:
                        return error_response(422, 'empty_upload', 'Video file is empty.')
                    result = await run_in_threadpool(service, path, side, facing)
                    return JSONResponse(result)
        except AnalysisError as exception:
            return error_response(exception.status, exception.code, exception.message)
        except HTTPException:
            raise
        except MultipartParseError:
            return error_response(400, 'invalid_multipart', 'Malformed multipart request.')
        except Exception:
            return error_response(500, 'analysis_failed', 'Analysis could not be completed.')
        finally:
            admission.release()

    return app


app = create_app()
