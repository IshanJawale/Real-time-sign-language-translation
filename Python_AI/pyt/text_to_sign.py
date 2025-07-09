import os
import cv2
import re
import mediapipe as mp
from glob import glob
from moviepy import concatenate_videoclips, VideoFileClip

def clean_text(text):
    """Clean text to match labels."""
    return re.sub(r'[\d.]', '', text).lower().strip()

def extract_label_map(dataset_path):
    """Extract video file paths associated with labels."""
    label_map = {}
    for category in os.listdir(dataset_path):
        cat_path = os.path.join(dataset_path, category)
        if not os.path.isdir(cat_path):
            continue

        for label_folder in os.listdir(cat_path):
            label_path = os.path.join(cat_path, label_folder)
            cleaned_label = clean_text(label_folder)

            video_files = glob(os.path.join(label_path, "*.mov"))
            if video_files:
                label_map[cleaned_label] = video_files[0]

    return label_map

def match_sentence_to_videos(sentence, label_map):
    """Match sentence words to video clips."""
    sentence = clean_text(sentence)
    words = sentence.split()
    matched_labels = []
    idx = 0

    while idx < len(words):
        found = False
        for n in range(3, 0, -1):
            if idx + n > len(words):
                continue
            phrase = ' '.join(words[idx:idx + n])
            if phrase in label_map:
                matched_labels.append((phrase, label_map[phrase]))
                idx += n
                found = True
                break
        if not found:
            raise ValueError(f"❌ No matching label found for word/phrase: '{words[idx]}'")
    return matched_labels

# Initialize MediaPipe for hand tracking
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)

def detect_hands(frame):
    """Detect hands in a frame using MediaPipe."""
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)
    return results

def trim_video_with_hands(video_path, start_frame, end_frame, output_path="trimmed_video.mov"):
    """Trim video based on detected hand movements."""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_path, fourcc, fps, (1920, 1080))

    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    frame_count = start_frame
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret or frame_count > end_frame:
            break

        results = detect_hands(frame)
        if results.multi_hand_landmarks:
            out.write(frame)
        frame_count += 1

    cap.release()
    out.release()
    print(f"✅ Trimmed video saved to: {output_path}")

def generate_sentence_video(sentence, dataset_path):
    """Generate video by matching sentence to labels and trimming based on hand motion."""
    label_map = extract_label_map(dataset_path)
    print(f"📚 Found {len(label_map)} labels in dataset.")

    matched = match_sentence_to_videos(sentence, label_map)
    print("\n🔍 Matched labels:")
    for phrase, path in matched:
        print(f"  ✅ '{phrase}' → {path}")

    video_paths = []
    for _, path in matched:
        # Assume hand movement occurs from frame 10 to 90 (just as an example)
        start_frame = 10
        end_frame = 90

        # Trim video based on hand movement
        temp_output = "temp_trimmed_video.mov"
        trim_video_with_hands(path, start_frame, end_frame, temp_output)
        video_paths.append(temp_output)

    # Merge the trimmed video clips
    final_clip = concatenate_videoclips([VideoFileClip(vp) for vp in video_paths], method="compose")
    final_clip.write_videofile("output_sentence.mov", codec="libx264", fps=24, threads=4, preset='ultrafast')
    print(f"✅ Final video saved to: output_sentence.mov")

# Example usage
if __name__ == "__main__":
    dataset_path = r"../Example_videos"
    sentence = "how are you"
    try:
        generate_sentence_video(sentence, dataset_path)
    except ValueError as e:
        print(e)
