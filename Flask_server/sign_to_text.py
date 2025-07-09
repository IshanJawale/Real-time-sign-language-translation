import torch
import joblib
import os
from torchvision.models.video import r3d_18, R3D_18_Weights
from torchvision import transforms
from decord import VideoReader, cpu
import numpy as np

def video_to_text(video_path, model_path="sign_language_model.pth", label_encoder_path="label_encoder.pkl", max_frames=16):
    """
    Convert a sign language video to text by predicting the sign.
    
    Args:
        video_path (str): Path to the video file.
        model_path (str): Path to the trained model.
        label_encoder_path (str): Path to the label encoder.
        max_frames (int): Maximum number of frames to use for prediction.
        
    Returns:
        str: The predicted sign language text.
    """
    try:
        # Ensure we're working with an absolute path
        abs_video_path = os.path.abspath(video_path)
        print(f"Processing video at: {abs_video_path}")
        
        # Verify file exists before attempting to read
        if not os.path.exists(abs_video_path):
            print(f"ERROR: Video file does not exist at path: {abs_video_path}")
            return "ERROR: Video file not found"
        
        # Set device
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Fast transform (batch-friendly)
        transform = transforms.Compose([
            transforms.Resize((112, 112)),
        ])
        
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
        vr = VideoReader(abs_video_path, ctx=cpu(0))
        total_frames = len(vr)
    
        if total_frames < max_frames:
            indices = np.linspace(0, total_frames - 1, max_frames).astype(int)
        else:
            indices = np.linspace(0, total_frames - 1, max_frames).astype(int)
    
        frames = vr.get_batch(indices).asnumpy()  # (T, H, W, C)
        frames = torch.from_numpy(frames).permute(3, 0, 1, 2).float() / 255.0  # (C, T, H, W)
        frames = transform(frames)
        video = frames.unsqueeze(0)  # (1, C, T, H, W)
        
        video = video.to(device)
        if device.type == 'cuda':
            video = video.half()
    
        # Predict
        with torch.no_grad():
            outputs = model(video)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]
            top_probs, top_indices = torch.topk(probabilities, 1)
    
        # Return the predicted text
        result = le.inverse_transform([top_indices[0].item()])[0]
        print(f"Successfully predicted: {result}")
        return result
    
    except Exception as e:
        print(f"Error in video_to_text: {str(e)}")
        # Return error message in case of failure
        return f"ERROR: {str(e)}"

if __name__ == "__main__":
    # Example usage
    test_video = "test.mov"
    predicted_text = video_to_text(test_video)
    print(f"Predicted Text: {predicted_text}") 