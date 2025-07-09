import torch
import joblib
from torchvision.models.video import r3d_18, R3D_18_Weights
from torchvision import transforms
from decord import VideoReader, cpu
import numpy as np

# Set device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Fast transform (batch-friendly)
transform = transforms.Compose([
    transforms.Resize((112, 112)),
])

def load_video_fast(video_path, max_frames=16):
    vr = VideoReader(video_path, ctx=cpu(0))
    total_frames = len(vr)

    if total_frames < max_frames:
        indices = np.linspace(0, total_frames - 1, max_frames).astype(int)
    else:
        indices = np.linspace(0, total_frames - 1, max_frames).astype(int)

    frames = vr.get_batch(indices).asnumpy()  # (T, H, W, C)
    frames = torch.from_numpy(frames).permute(3, 0, 1, 2).float() / 255.0  # (C, T, H, W)
    frames = transform(frames)
    return frames.unsqueeze(0)  # (1, C, T, H, W)

def predict_sign_video_top3(video_path, model_path, label_encoder_path, max_frames=16):
    # Load label encoder
    le = joblib.load(label_encoder_path)

    # Load model
    weights = R3D_18_Weights.DEFAULT
    model = r3d_18(weights=weights)
    model.fc = torch.nn.Linear(model.fc.in_features, len(le.classes_))
    model.load_state_dict(torch.load(model_path, map_location=device))
    model = model.to(device).eval()

    if device.type == 'cuda':
        model = model.half()

    # Load and preprocess video
    video = load_video_fast(video_path, max_frames)
    video = video.to(device)
    if device.type == 'cuda':
        video = video.half()

    # Predict
    with torch.no_grad():
        outputs = model(video)
        probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]
        top_probs, top_indices = torch.topk(probabilities, 3)

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

    prediction = predict_sign_video_top3(test_video, model_path, label_encoder_path)
    print(f"\n✅ Final Predicted Sign: {prediction}")
