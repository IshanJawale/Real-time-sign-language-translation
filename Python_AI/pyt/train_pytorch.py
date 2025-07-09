import os
import re
import joblib
from glob import glob
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms
from torchvision.io import read_video
from torchvision.models.video import r3d_18, R3D_18_Weights
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import numpy as np

# Check if CUDA is available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# 1. Custom Dataset
class SignLanguageVideoDataset(Dataset):
    def __init__(self, video_paths, labels, transform=None, max_frames=16):
        self.video_paths = video_paths
        self.labels = labels
        self.transform = transform
        self.max_frames = max_frames

    def __len__(self):
        return len(self.video_paths)

    def __getitem__(self, idx):
        video_path = self.video_paths[idx]
        label = self.labels[idx]

        # Read video using torchvision
        video, _, _ = read_video(video_path, pts_unit='sec')
        video = video.float() / 255.0

        # Limit or pad the video to self.max_frames
        total_frames = video.shape[0]
        if total_frames >= self.max_frames:
            video = video[:self.max_frames]
        else:
            pad = self.max_frames - total_frames
            video = torch.cat([video, video[-1:].repeat(pad, 1, 1, 1)], dim=0)

        # Permute to (C, T, H, W)
        video = video.permute(3, 0, 1, 2)

        if self.transform:
            video = self.transform(video)

        return video, label

# 2. Utility to get videos and clean labels
def load_videos_and_labels(root_dir):
    video_paths = []
    labels = []

    print("Loading videos and labels...")

    for category in os.listdir(root_dir):
        cat_path = os.path.join(root_dir, category)
        if not os.path.isdir(cat_path):
            continue
        for label in os.listdir(cat_path):
            label_path = os.path.join(cat_path, label)
            if not os.path.isdir(label_path):
                continue
            # Clean label name
            clean_label = re.sub(r'[\d.]', '', label)
            for video_file in glob(os.path.join(label_path, "*.mov")):
                video_paths.append(video_file)
                labels.append(clean_label)

    print(f"Loaded {len(video_paths)} videos with {len(set(labels))} unique labels.")
    return video_paths, labels

# 3. Training Function
def train_model(dataset_path, batch_size=4, epochs=10, lr=1e-4):
    print("Starting model training...")

    video_paths, raw_labels = load_videos_and_labels(dataset_path)

    # Label encoding
    le = LabelEncoder()
    labels_encoded = le.fit_transform(raw_labels)
    print(f"Encoded {len(set(raw_labels))} unique labels into {len(set(labels_encoded))} classes.")

    # Train-val split
    train_videos, val_videos, train_labels, val_labels = train_test_split(
        video_paths, labels_encoded, test_size=0.2, stratify=labels_encoded, random_state=42)

    print(f"Train videos: {len(train_videos)}, Validation videos: {len(val_videos)}")

    transform = transforms.Compose([
        transforms.Resize((112, 112))
    ])

    train_dataset = SignLanguageVideoDataset(train_videos, train_labels, transform)
    val_dataset = SignLanguageVideoDataset(val_videos, val_labels, transform)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)

    # Load model with updated weights syntax
    weights = R3D_18_Weights.DEFAULT
    model = r3d_18(weights=weights)
    model.fc = nn.Linear(model.fc.in_features, len(le.classes_))
    model = model.to(device)

    print(f"Model structure: \n{model}")

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    # Training Loop
    for epoch in range(epochs):
        print(f"Epoch {epoch + 1}/{epochs}")
        model.train()
        running_loss, correct, total = 0.0, 0, 0

        for batch_idx, (inputs, targets) in enumerate(train_loader):
            if batch_idx % 100 == 0:  # Print progress every 100 batches
                print(f"Batch {batch_idx}/{len(train_loader)}")

            inputs, targets = inputs.to(device), targets.to(device)
            optimizer.zero_grad()

            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * inputs.size(0)
            _, predicted = outputs.max(1)
            correct += predicted.eq(targets).sum().item()
            total += targets.size(0)

        train_acc = correct / total
        print(f"Train Loss: {running_loss/total:.4f}, Train Accuracy: {train_acc * 100:.2f}%")

        # Validation
        model.eval()
        val_correct, val_total = 0, 0
        with torch.no_grad():
            for inputs, targets in val_loader:
                inputs, targets = inputs.to(device), targets.to(device)
                outputs = model(inputs)
                _, predicted = outputs.max(1)
                val_correct += predicted.eq(targets).sum().item()
                val_total += targets.size(0)
        val_acc = val_correct / val_total
        print(f"Validation Accuracy: {val_acc * 100:.2f}%\n")

    # Save model and encoder
    torch.save(model.state_dict(), "sign_language_model.pth")
    joblib.dump(le, "label_encoder.pkl")
    print("✅ Model and label encoder saved!")

    return model, le

# 4. Run Training
if __name__ == "__main__":
    dataset_path = r"E:\Ishan\K.K. Wagh\Sixth Semester\Mobile Application Development\dataset3"
    model, label_encoder = train_model(dataset_path, batch_size=4, epochs=20, lr=1e-4)   #epoch = 20, batch size = 4
