import torch
import joblib
from torchvision.models.video import r3d_18, R3D_18_Weights
from torchvision.io import read_video
from torchvision import transforms

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def predict_sign_video_top3(video_path, model_path, label_encoder_path, max_frames=16):
    le = joblib.load(label_encoder_path)

    weights = R3D_18_Weights.DEFAULT
    model = r3d_18(weights=weights)
    model.fc = torch.nn.Linear(model.fc.in_features, len(le.classes_))
    model.load_state_dict(torch.load(model_path, map_location=device))
    model = model.to(device)
    model.eval()

    video, _, _ = read_video(video_path, pts_unit='sec')
    video = video.float() / 255.0

    total_frames = video.shape[0]
    if total_frames >= max_frames:
        video = video[:max_frames]
    else:
        pad = max_frames - total_frames
        video = torch.cat([video, video[-1:].repeat(pad, 1, 1, 1)], dim=0)

    video = video.permute(3, 0, 1, 2)
    video = transforms.Resize((112, 112))(video)
    video = video.unsqueeze(0).to(device)

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

if __name__ == "__main__":
    test_video = r"test.mov"
    model_path = "sign_language_model.pth"
    label_encoder_path = "label_encoder.pkl"

    prediction = predict_sign_video_top3(test_video, model_path, label_encoder_path)
    print(f"\n✅ Final Predicted Sign: {prediction}")
