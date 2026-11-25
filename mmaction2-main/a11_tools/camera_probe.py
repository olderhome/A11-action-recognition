import argparse
import sys
import time
from pathlib import Path

import cv2


def parse_args():
    parser = argparse.ArgumentParser(
        description='Capture a short webcam clip for MMAction2 diagnostics.')
    parser.add_argument('--camera-id', type=int, default=0)
    parser.add_argument('--duration', type=float, default=4.0)
    parser.add_argument('--output-dir', type=Path, required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    if sys.platform.startswith('win'):
        camera = cv2.VideoCapture(args.camera_id, cv2.CAP_DSHOW)
    else:
        camera = cv2.VideoCapture(args.camera_id)

    if not camera.isOpened():
        camera.release()
        raise RuntimeError(f'Unable to open camera {args.camera_id}.')

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    capture_fps = 20.0

    for _ in range(5):
        camera.read()

    writer = None
    frame_count = 0
    start = time.perf_counter()
    frame_path = args.output_dir / 'camera_probe_frame.png'
    video_path = args.output_dir / 'camera_probe.mp4'

    try:
        while time.perf_counter() - start < args.duration:
            ok, frame = camera.read()
            if not ok:
                raise RuntimeError('Camera opened but no frame could be read.')
            if writer is None:
                height, width = frame.shape[:2]
                writer = cv2.VideoWriter(
                    str(video_path),
                    cv2.VideoWriter_fourcc(*'mp4v'),
                    capture_fps,
                    (width, height))
                if not writer.isOpened():
                    raise RuntimeError('Unable to create the camera test video.')
                cv2.imwrite(str(frame_path), frame)
            writer.write(frame)
            frame_count += 1
    finally:
        camera.release()
        if writer is not None:
            writer.release()

    elapsed = time.perf_counter() - start
    print(f'camera_id={args.camera_id}')
    print(f'frame={frame_path}')
    print(f'video={video_path}')
    print(f'frames={frame_count}')
    print(f'elapsed_seconds={elapsed:.2f}')
    print(f'effective_fps={frame_count / elapsed:.2f}')
    print(f'resolution={width}x{height}')


if __name__ == '__main__':
    main()
