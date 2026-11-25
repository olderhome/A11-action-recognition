import argparse
import base64
import json
import statistics
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import cv2
import numpy as np
import torch
from mmengine import Config

from mmaction.apis import inference_recognizer, init_recognizer


REPO_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = REPO_ROOT.parent
OUTPUT_ROOT = PROJECT_ROOT / 'outputs'
RESULT_ROOT = OUTPUT_ROOT / 'comparison_results'
CAMERA_ROOT = OUTPUT_ROOT / 'camera_tests'
LABEL_FILE = REPO_ROOT / 'tools/data/kinetics/label_map_k400.txt'
ASSET_FILE = Path(__file__).with_name('comparison_app.html')

ROUTES = {
    'tsn_2d': {
        'name': '2D 骨干 + 时序聚合',
        'short_name': 'TSN · ResNet-50',
        'config': REPO_ROOT / 'demo/demo_configs/tsn_r50_1x1x8_video_infer.py',
        'checkpoint': REPO_ROOT / 'checkpoints/tsn_r50_kinetics400.pth',
        'sample': '8 段稀疏采样，每段 1 帧；帧级特征与预测概率聚合',
        'accent': '#37b7a5',
    },
    'r2plus1d_3d': {
        'name': '轻量 3D 卷积',
        'short_name': 'R(2+1)D · ResNet-34',
        'config': REPO_ROOT / 'demo/demo_configs/r2plus1d_r34_8x8x1_video_infer.py',
        'checkpoint': REPO_ROOT / 'checkpoints/r2plus1d_r34_kinetics400.pth',
        'sample': '8 帧连续片段；空间 2D 卷积与时间 1D 卷积联合建模',
        'accent': '#df8e3b',
    },
}


BASE_CASES = [
    {
        'id': 'demo_arm_wrestling',
        'title': '掰手腕示例',
        'description': '项目自带视频，动作明确，适合验证两条路线是否识别正确。',
        'reference': 'arm wrestling',
        'path': REPO_ROOT / 'demo/demo.mp4',
    },
    {
        'id': 'camera_portrait',
        'title': '摄像头人物近景',
        'description': '先前采集的摄像头测试片段，没有明确的大幅动作。',
        'reference': '无明确动作标签',
        'path': OUTPUT_ROOT / 'camera_probe/camera_probe.mp4',
    },
]


def read_labels():
    return [line.strip() for line in LABEL_FILE.read_text(
        encoding='utf-8').splitlines() if line.strip()]


def top5_from_scores(scores, labels):
    order = np.argsort(-scores)[:5]
    return [{
        'label': labels[int(index)],
        'score': float(scores[int(index)]),
    } for index in order]


def resize_for_preview(frame, max_width=720):
    height, width = frame.shape[:2]
    if width <= max_width:
        return frame
    scale = max_width / width
    return cv2.resize(
        frame, (max_width, int(height * scale)),
        interpolation=cv2.INTER_AREA)


def annotate_frame(video_path, route_key, route, predictions, elapsed):
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f'Unable to open test video: {video_path}')

    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    capture.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_count // 2))
    ok, frame = capture.read()
    if not ok:
        capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ok, frame = capture.read()
    capture.release()
    if not ok:
        raise RuntimeError(f'Unable to read a frame from: {video_path}')

    frame = resize_for_preview(frame)
    height, width = frame.shape[:2]
    panel_height = min(190, height)
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (width, panel_height), (16, 18, 20), -1)
    frame = cv2.addWeighted(overlay, 0.86, frame, 0.14, 0)

    accent_bgr = (183, 142, 223) if route_key == 'r2plus1d_3d' else (
        165, 183, 55)
    cv2.putText(
        frame, route['short_name'].encode('ascii', 'ignore').decode(),
        (18, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.72, accent_bgr, 2,
        cv2.LINE_AA)

    top1 = predictions[0]
    top_text = f"{top1['label']}  {top1['score'] * 100:.1f}%"
    cv2.putText(
        frame, top_text, (18, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.86,
        (245, 245, 245), 2, cv2.LINE_AA)
    cv2.putText(
        frame, f'inference {elapsed:.2f}s', (18, 96),
        cv2.FONT_HERSHEY_SIMPLEX, 0.48, (195, 198, 202), 1, cv2.LINE_AA)

    for index, item in enumerate(predictions[1:4], start=1):
        text = f"{index + 1}. {item['label']}  {item['score'] * 100:.2f}%"
        cv2.putText(
            frame, text, (18, 100 + index * 24),
            cv2.FONT_HERSHEY_SIMPLEX, 0.48, (220, 220, 220), 1,
            cv2.LINE_AA)
    return frame


def encode_jpeg(frame):
    ok, encoded = cv2.imencode(
        '.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    if not ok:
        raise RuntimeError('Unable to encode result frame.')
    return base64.b64encode(encoded.tobytes()).decode('ascii')


def write_jpeg(path, frame):
    ok, encoded = cv2.imencode(
        '.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    if not ok:
        raise RuntimeError(f'Unable to write result frame: {path}')
    path.write_bytes(encoded.tobytes())


def discover_camera_cases():
    cases = []
    if not CAMERA_ROOT.exists():
        return cases
    for index, path in enumerate(
            sorted(CAMERA_ROOT.glob('camera_*.mp4'), reverse=True)[:6]):
        cases.append({
            'id': f'camera_capture_{index}_{path.stem}',
            'title': f'新摄像头片段 {index + 1}',
            'description': '由测试台现场采集的短视频。',
            'reference': '实时采集，参考标签未知',
            'path': path,
        })
    return cases


def all_cases():
    return [case for case in BASE_CASES + discover_camera_cases()
            if case['path'].exists()]


def case_public(case):
    return {
        key: str(value) if key == 'path' else value
        for key, value in case.items() if key != 'path'
    }


class ComparisonModels:
    def __init__(self, device):
        self.device = device
        self.labels = read_labels()
        self.models = {}
        self.metadata = {}
        self.lock = threading.Lock()

    def ensure_loaded(self):
        with self.lock:
            for route_key, route in ROUTES.items():
                if route_key in self.models:
                    continue
                cfg = Config.fromfile(str(route['config']))
                model = init_recognizer(
                    cfg, str(route['checkpoint']), device=self.device)
                model.eval()
                parameters = sum(parameter.numel()
                                 for parameter in model.parameters())
                parameter_mb = sum(
                    parameter.numel() * parameter.element_size()
                    for parameter in model.parameters()) / (1024**2)
                self.models[route_key] = model
                self.metadata[route_key] = {
                    'parameters': parameters,
                    'parameter_mb': parameter_mb,
                }
            warmup_video = REPO_ROOT / 'demo/demo.mp4'
            for route_key in ROUTES:
                if not self.metadata[route_key].get('warmed_up'):
                    inference_recognizer(
                        self.models[route_key], str(warmup_video))
                    self.metadata[route_key]['warmed_up'] = True

    def infer(self, route_key, video_path):
        self.ensure_loaded()
        model = self.models[route_key]
        timings = []
        result = None
        for _ in range(3):
            if self.device.startswith('cuda'):
                torch.cuda.synchronize()
            start = time.perf_counter()
            result = inference_recognizer(model, str(video_path))
            if self.device.startswith('cuda'):
                torch.cuda.synchronize()
            timings.append(time.perf_counter() - start)
        scores = result.pred_score.detach().float().cpu().numpy()
        return top5_from_scores(scores, self.labels), statistics.median(timings)

    def gpu_resident_mb(self):
        if not self.device.startswith('cuda'):
            return 0.0
        return torch.cuda.memory_allocated() / (1024**2)

    def gpu_peak_mb(self):
        if not self.device.startswith('cuda'):
            return 0.0
        return torch.cuda.max_memory_allocated() / (1024**2)


def capture_camera(camera_id, duration, fps=20):
    CAMERA_ROOT.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = CAMERA_ROOT / f'camera_{timestamp}.mp4'
    camera = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
    if not camera.isOpened():
        camera.release()
        raise RuntimeError(f'Unable to open camera {camera_id}.')
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    for _ in range(5):
        camera.read()

    writer = None
    frame_count = 0
    start = time.perf_counter()
    try:
        while time.perf_counter() - start < duration:
            ok, frame = camera.read()
            if not ok:
                raise RuntimeError('Camera opened but returned no frame.')
            if writer is None:
                height, width = frame.shape[:2]
                writer = cv2.VideoWriter(
                    str(output_path),
                    cv2.VideoWriter_fourcc(*'mp4v'),
                    fps,
                    (width, height))
                if not writer.isOpened():
                    raise RuntimeError('Unable to create camera test video.')
            writer.write(frame)
            frame_count += 1
    finally:
        camera.release()
        if writer is not None:
            writer.release()

    if frame_count == 0:
        raise RuntimeError('No camera frames were captured.')
    return output_path, frame_count, time.perf_counter() - start


def run_comparison(models, case, progress=None):
    RESULT_ROOT.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    route_results = {}
    annotated_frames = {}
    if models.device.startswith('cuda'):
        torch.cuda.reset_peak_memory_stats()

    for route_key, route in ROUTES.items():
        if progress:
            progress(route['name'])
        predictions, elapsed = models.infer(route_key, case['path'])
        frame = annotate_frame(
            case['path'], route_key, route, predictions, elapsed)
        frame_path = RESULT_ROOT / f'{run_id}_{route_key}.jpg'
        write_jpeg(frame_path, frame)
        route_results[route_key] = {
            'name': route['name'],
            'short_name': route['short_name'],
            'sample': route['sample'],
            'accent': route['accent'],
            'top5': predictions,
            'elapsed_seconds': elapsed,
            **models.metadata[route_key],
            'frame_path': str(frame_path),
        }
        annotated_frames[route_key] = encode_jpeg(frame)

    tsn = route_results['tsn_2d']
    r3d = route_results['r2plus1d_3d']
    agreement = tsn['top5'][0]['label'] == r3d['top5'][0]['label']
    faster = min(route_results, key=lambda key: route_results[key][
        'elapsed_seconds'])
    response = {
        'run_id': run_id,
        'case': {
            'id': case['id'],
            'title': case['title'],
            'reference': case['reference'],
        },
        'routes': route_results,
        'images': annotated_frames,
        'summary': {
            'agreement': agreement,
            'faster_route': faster,
            'tsn_top1': tsn['top5'][0]['label'],
            'r3d_top1': r3d['top5'][0]['label'],
            'confidence_delta': (
                tsn['top5'][0]['score'] - r3d['top5'][0]['score']),
            'gpu_resident_mb': models.gpu_resident_mb(),
            'gpu_peak_mb': models.gpu_peak_mb(),
            'device': models.device,
        },
        'created_at': datetime.now().isoformat(timespec='seconds'),
    }

    metadata_path = RESULT_ROOT / f'{run_id}.json'
    metadata = json.loads(json.dumps(response))
    metadata.pop('images', None)
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding='utf-8')
    response['result_file'] = str(metadata_path)
    return response


class Application:
    def __init__(self, device):
        self.models = ComparisonModels(device)
        self.run_lock = threading.Lock()
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        RESULT_ROOT.mkdir(parents=True, exist_ok=True)

    def testcases(self):
        return [case_public(case) for case in all_cases()]

    def find_case(self, case_id):
        for case in all_cases():
            if case['id'] == case_id:
                return case
        raise ValueError(f'Unknown test case: {case_id}')

    def run(self, case_id):
        with self.run_lock:
            return run_comparison(self.models, self.find_case(case_id))

    def capture_and_run(self, camera_id=0, duration=4.0):
        with self.run_lock:
            path, frames, elapsed = capture_camera(camera_id, duration)
            case = {
                'id': f'live_{path.stem}',
                'title': '现场摄像头测试',
                'description': '刚刚由摄像头采集。',
                'reference': '实时采集，参考标签未知',
                'path': path,
            }
            result = run_comparison(self.models, case)
            result['capture'] = {
                'path': str(path),
                'frames': frames,
                'elapsed_seconds': elapsed,
            }
            return result

    def history(self):
        records = []
        for path in sorted(
                RESULT_ROOT.glob('*.json'), key=lambda p: p.stat().st_mtime,
                reverse=True)[:10]:
            try:
                data = json.loads(path.read_text(encoding='utf-8'))
                records.append({
                    'run_id': data['run_id'],
                    'case': data['case']['title'],
                    'created_at': data['created_at'],
                    'tsn_top1': data['summary']['tsn_top1'],
                    'r3d_top1': data['summary']['r3d_top1'],
                    'agreement': data['summary']['agreement'],
                })
            except (KeyError, json.JSONDecodeError):
                continue
        return records


def make_handler(app):
    class Handler(BaseHTTPRequestHandler):
        def _json(self, payload, status=200):
            data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _read_json(self):
            length = int(self.headers.get('Content-Length', '0'))
            if length == 0:
                return {}
            return json.loads(self.rfile.read(length))

        def do_GET(self):
            path = urlparse(self.path).path
            if path in ('/', '/index.html'):
                data = ASSET_FILE.read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            if path == '/api/testcases':
                self._json({'cases': app.testcases()})
                return
            if path == '/api/history':
                self._json({'history': app.history()})
                return
            if path == '/api/health':
                self._json({
                    'ok': True,
                    'cuda': torch.cuda.is_available(),
                    'gpu': (
                        torch.cuda.get_device_name(0)
                        if torch.cuda.is_available() else None),
                })
                return
            self._json({'error': 'Not found'}, status=404)

        def do_POST(self):
            path = urlparse(self.path).path
            try:
                body = self._read_json()
                if path == '/api/run':
                    self._json(app.run(body['case_id']))
                    return
                if path == '/api/capture':
                    self._json(app.capture_and_run(
                        camera_id=int(body.get('camera_id', 0)),
                        duration=float(body.get('duration', 4.0))))
                    return
                self._json({'error': 'Not found'}, status=404)
            except Exception as error:
                self._json({'error': str(error)}, status=500)

        def log_message(self, message, *args):
            print(f'[server] {message % args}')

    return Handler


def parse_args():
    parser = argparse.ArgumentParser(
        description='Interactive TSN vs R(2+1)D comparison dashboard.')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=7860)
    parser.add_argument(
        '--device', default='cuda:0' if torch.cuda.is_available() else 'cpu')
    return parser.parse_args()


def main():
    args = parse_args()
    app = Application(args.device)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(app))
    print(f'Comparison dashboard: http://{args.host}:{args.port}')
    print(f'Device: {args.device}')
    server.serve_forever()


if __name__ == '__main__':
    main()
