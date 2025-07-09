import torch
import joblib
import numpy as np
import cv2
from decord import VideoReader, cpu
from torchvision.models.video import mc3_18, MC3_18_Weights
import torch.nn.functional as F

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def load_video_ultra_fast(video_path, max_frames=16, resize=(112, 112)):
    vr = VideoReader(video_path, ctx=cpu(0))
    total_frames = len(vr)
    indices = np.linspace(0, total_frames - 1, max_frames).astype(int)
    frames = vr.get_batch(indices).asnumpy()  # (T, H, W, C)

    resized_frames = np.stack([cv2.resize(f, resize) for f in frames])  # (T, H, W, C)
    video = torch.from_numpy(resized_frames).permute(3, 0, 1, 2).float() / 255.0  # (C, T, H, W)
    return video.unsqueeze(0)  # (1, C, T, H, W)

def predict_sign_video_ultrafast(video_path, model_path, label_encoder_path, max_frames=16):
    # Load label encoder
    le = joblib.load(label_encoder_path)

    # Load lightweight model
    weights = MC3_18_Weights.DEFAULT
    model = mc3_18(weights=weights)
    model.fc = torch.nn.Linear(model.fc.in_features, len(le.classes_))
    model.load_state_dict(torch.load(model_path, map_location=device))
    model = model.to(device).eval()

    if device.type == 'cuda':
        model = model.half()

    # Preprocess video
    video = load_video_ultra_fast(video_path, max_frames)
    video = video.to(device)
    if device.type == 'cuda':
        video = video.half()

    with torch.no_grad():
        outputs = model(video)
        probs = F.softmax(outputs, dim=1)[0]
        top_probs, top_indices = torch.topk(probs, 3)

    print("\n🔍 Top 3 Predictions:")
    for i in range(3):
        label = le.inverse_transform([top_indices[i].item()])[0]
        confidence = top_probs[i].item() * 100
        print(f"{i + 1}. {label}: {confidence:.2f}%")

    return le.inverse_transform([top_indices[0].item()])[0]

# Example usage
if __name__ == "__main__":
    test_video = "test.mov"
    model_path = "sign_language_model.pth"
    label_encoder_path = "label_encoder.pkl"

    prediction = predict_sign_video_ultrafast(test_video, model_path, label_encoder_path)
    print(f"\n✅ Final Predicted Sign: {prediction}")
