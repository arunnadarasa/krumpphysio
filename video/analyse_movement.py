#!/usr/bin/env python3
import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

LANDMARK_MAP = {
    "left_shoulder": (13, 11, 23),
    "right_shoulder": (14, 12, 24),
    "left_elbow": (11, 13, 15),
    "right_elbow": (12, 14, 16),
    "left_hip": (11, 23, 25),
    "right_hip": (12, 24, 26),
    "left_knee": (23, 25, 27),
    "right_knee": (24, 26, 28),
}

VALID_JOINTS = list(LANDMARK_MAP.keys())

MODEL_PATH = Path(__file__).parent / "pose_landmarker_lite.task"
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"


def download_model():
    if not MODEL_PATH.exists():
        print(f"Downloading pose model to {MODEL_PATH}...", file=sys.stderr)
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("Model downloaded.", file=sys.stderr)


def calculate_angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    ba = a - b
    bc = c - b

    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
    cosine = np.clip(cosine, -1.0, 1.0)
    angle = np.arccos(cosine)
    return np.degrees(angle)


def classify_smoothness(variance: float) -> str:
    if variance < 5.0:
        return "low"
    elif variance < 15.0:
        return "medium"
    return "high"


def count_reps(angles: list, min_peak_distance_frames: int = 8) -> int:
    """
    Count movement cycles (reps) from the joint angle time series.
    Uses local maxima of the smoothed angle signal; each peak is one extension cycle.
    """
    if not angles or len(angles) < min_peak_distance_frames * 2:
        return 0
    arr = np.array(angles, dtype=float)
    # Light smoothing to reduce noise
    kernel = np.ones(5) / 5
    smoothed = np.convolve(arr, kernel, mode="same")
    peaks = 0
    last_peak_idx = -min_peak_distance_frames - 1
    for i in range(1, len(smoothed) - 1):
        if smoothed[i] >= smoothed[i - 1] and smoothed[i] >= smoothed[i + 1]:
            if i - last_peak_idx >= min_peak_distance_frames:
                peaks += 1
                last_peak_idx = i
    return peaks


def draw_landmarks_on_frame(frame, landmarks, width, height):
    connections = [
        (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
        (11, 23), (12, 24), (23, 24), (23, 25), (24, 26),
        (25, 27), (26, 28)
    ]

    for lm in landmarks:
        x = int(lm.x * width)
        y = int(lm.y * height)
        cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

    for start, end in connections:
        if start < len(landmarks) and end < len(landmarks):
            x1 = int(landmarks[start].x * width)
            y1 = int(landmarks[start].y * height)
            x2 = int(landmarks[end].x * width)
            y2 = int(landmarks[end].y * height)
            cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)


def process_video(
    video_path: str,
    joint: str,
    target: float,
    output_path: str = None,
    min_confidence: float = 0.5,
    extended: bool = False
):
    download_model()
    start_time = time.time()

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"error": True, "code": "VIDEO_READ_ERROR", "message": f"Could not open video file: {video_path}"}

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    writer = None
    if output_path:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    idx_a, idx_b, idx_c = LANDMARK_MAP[joint]
    angles = []
    frames_detected = 0

    base_options = python.BaseOptions(model_asset_path=str(MODEL_PATH))
    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        output_segmentation_masks=False,
        min_pose_detection_confidence=min_confidence,
        min_tracking_confidence=min_confidence
    )

    with vision.PoseLandmarker.create_from_options(options) as landmarker:
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            result = landmarker.detect(mp_image)

            angle_this_frame = None

            if result.pose_landmarks and len(result.pose_landmarks) > 0:
                landmarks = result.pose_landmarks[0]
                frames_detected += 1

                a = np.array([landmarks[idx_a].x * width, landmarks[idx_a].y * height])
                b = np.array([landmarks[idx_b].x * width, landmarks[idx_b].y * height])
                c = np.array([landmarks[idx_c].x * width, landmarks[idx_c].y * height])

                angle_this_frame = calculate_angle(a, b, c)
                angles.append(angle_this_frame)

                if writer:
                    draw_landmarks_on_frame(frame, landmarks, width, height)
                    text = f"{joint}: {angle_this_frame:.1f} deg (target: {target})"
                    cv2.putText(frame, text, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            if writer:
                writer.write(frame)

            frame_idx += 1

    cap.release()
    if writer:
        writer.release()

    if len(angles) == 0:
        return {"error": True, "code": "NO_POSE_DETECTED", "message": "No pose detected in any frame"}

    observed = float(np.mean(angles))
    variance = float(np.var(np.diff(angles))) if len(angles) > 1 else 0.0
    smoothness = classify_smoothness(variance)
    processing_time = int((time.time() - start_time) * 1000)

    summary = [{"joint": joint, "target": target, "observed": round(observed, 1)}]

    if extended:
        reps = count_reps(angles)
        return {
            "summary": summary,
            "meta": {
                "video_path": video_path,
                "frames_total": total_frames,
                "frames_detected": frames_detected,
                "frames_skipped": total_frames - frames_detected,
                "detection_rate": round(frames_detected / max(total_frames, 1), 3),
                "smoothness": smoothness,
                "variance": round(variance, 2),
                "min_angle": round(float(np.min(angles)), 1),
                "max_angle": round(float(np.max(angles)), 1),
                "reps": reps,
                "annotated_video": output_path,
                "processing_time_ms": processing_time
            }
        }

    return summary


def main():
    parser = argparse.ArgumentParser(description="Analyze movement from video using MediaPipe BlazePose")
    parser.add_argument("--video", required=True, help="Path to input video file")
    parser.add_argument("--joint", required=True, choices=VALID_JOINTS, help="Joint to analyze")
    parser.add_argument("--target", required=True, type=float, help="Target angle in degrees")
    parser.add_argument("--output", help="Path for annotated output video")
    parser.add_argument("--min-confidence", type=float, default=0.5, help="Minimum pose detection confidence")
    parser.add_argument("--extended", action="store_true", help="Output extended metadata")

    args = parser.parse_args()

    if not Path(args.video).exists():
        error = {"error": True, "code": "VIDEO_READ_ERROR", "message": f"Video file not found: {args.video}"}
        print(json.dumps(error), file=sys.stderr)
        sys.exit(1)

    result = process_video(
        video_path=args.video,
        joint=args.joint,
        target=args.target,
        output_path=args.output,
        min_confidence=args.min_confidence,
        extended=args.extended
    )

    if isinstance(result, dict) and result.get("error"):
        print(json.dumps(result), file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result))


if __name__ == "__main__":
    main()
