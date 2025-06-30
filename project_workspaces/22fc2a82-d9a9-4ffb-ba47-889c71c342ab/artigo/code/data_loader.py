import os
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision.io import read_image
import pandas as pd
import numpy as np
from PIL import Image
import torchvision.transforms as transforms

class MotorFailureDataset(Dataset):
    def __init__(self, csv_file, root_dir, transform=None):
        self.data = pd.read_csv(csv_file)
        self.root_dir = root_dir
        self.transform = transform
        
        # Map labels to indices
        unique_labels = self.data['label'].unique()
        self.label_to_idx = {label: idx for idx, label in enumerate(unique_labels)}
        
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        img_name = os.path.join(self.root_dir, 
                               self.data.iloc[idx, 0])
        image = read_image(img_name)
        label = self.data.iloc[idx, 1]
        label = self.label_to_idx[label]
        
        if self.transform:
            image = self.transform(image)
            
        return image, label

def create_data_loaders(train_csv, val_csv, test_csv, 
                         root_dir, batch_size=32, num_workers=4):
    # Define transformations
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    test_transform = val_transform
    
    # Create datasets
    train_dataset = MotorFailureDataset(
        csv_file=train_csv,
        root_dir=root_dir,
        transform=train_transform
    )
    
    val_dataset = MotorFailureDataset(
        csv_file=val_csv,
        root_dir=root_dir,
        transform=val_transform
    )
    
    test_dataset = MotorFailureDataset(
        csv_file=test_csv,
        root_dir=root_dir,
        transform=test_transform
    )
    
    # Create data loaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers
    )
    
    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers
    )
    
    return train_loader, val_loader, test_loader