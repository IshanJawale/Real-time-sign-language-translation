import os
import cv2
import re
import string
from glob import glob

def clean_text(text):
    """Lowercase, remove digits, punctuation and extension."""
    text = os.path.splitext(text)[0]  # Remove file extension
    text = re.sub(r'[\d]', '', text)  # Remove digits
    text = text.translate(str.maketrans('', '', string.punctuation))  # Remove punctuation
    return text.lower().strip()

def extract_label_map(dataset_path):
    """Extract cleaned label → actual video path."""
    label_map = {}
    for file_path in glob(os.path.join(dataset_path, "*.MOV")):
        filename = os.path.basename(file_path)
        cleaned_label = clean_text(filename)
        if cleaned_label not in label_map:
            label_map[cleaned_label] = file_path
    return label_map

def match_best_phrases(sentence, label_map):
    """Dynamic programming to find the best matching sequence of phrases."""
    sentence = sentence.lower().translate(str.maketrans('', '', string.punctuation))
    words = sentence.split()
    n = len(words)
    dp = [None] * (n + 1)
    dp[0] = []

    for i in range(1, n + 1):
        for j in range(i):
            phrase = ' '.join(words[j:i])
            cleaned = clean_text(phrase)
            if cleaned in label_map and dp[j] is not None:
                candidate = dp[j] + [(cleaned, label_map[cleaned])]
                if dp[i] is None or len(candidate) > len(dp[i]):
                    dp[i] = candidate
        if dp[i] is None:
            dp[i] = dp[i - 1]  # Skip unmatched

    return dp[n] if dp[n] else []

def merge_videos_opencv(video_paths, output_path):
    """Merge videos using OpenCV."""
    if not video_paths:
        print("❌ No video paths to merge.")
        return

    # Create the directory for output_path if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    out = None
    for path in video_paths:
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            print(f"⚠️ Failed to open {path}")
            continue

        fps = cap.get(cv2.CAP_PROP_FPS)
        width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if out is None:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)
        cap.release()

    if out:
        out.release()
        print(f"✅ Final video saved to: {output_path}")


def generate_sentence_video(sentence, dataset_path, output_path):
    """Main function to generate the final video."""
    label_map = extract_label_map(dataset_path)
    print(f"🎯 Labels available: {list(label_map.keys())}\n")

    matched = match_best_phrases(sentence, label_map)
    print("🔍 Best matched phrases:")
    for phrase, path in matched:
        print(f"  ✅ '{phrase}' → {path}")

    video_paths = [path for _, path in matched]
    merge_videos_opencv(video_paths, output_path)

# Example usage
if __name__ == "__main__":
    dataset_path = "Python_AI/Example_videos"
    output_path = "temp_uploads/output_sentence.mp4"
    sentence = "I am sad, how are you?"
    generate_sentence_video(sentence, dataset_path, output_path)
