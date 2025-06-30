import tensorflow as tf
from tensorflow.keras import layers, models, datasets
from tensorflow.keras.preprocessing.image import ImageDataGenerator

def create_cnn_model(input_shape=(128, 128, 3), num_classes=10):
    """
    Creates a CNN model for motor fault detection
    
    Args:
        input_shape: Shape of input images (default: (128, 128, 3))
        num_classes: Number of fault categories (default: 10)
        
    Returns:
        Compiled CNN model
    """
    model = models.Sequential([
        # First convolutional block
        layers.Conv2D(32, (3, 3), activation='relu', input_shape=input_shape),
        layers.MaxPooling2D((2, 2)),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        
        # Second convolutional block
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        
        # Third convolutional block
        layers.Conv2D(128, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        
        # Fourth convolutional block
        layers.Conv2D(256, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        
        # Flatten feature maps
        layers.Flatten(),
        
        # Fully connected layers
        layers.Dense(512, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.5),
        
        layers.Dense(256, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.5),
        
        # Output layer
        layers.Dense(num_classes, activation='softmax')
    ])
    
    # Compile the model
    model.compile(optimizer='adam',
                loss='categorical_crossentropy',
                metrics=['accuracy'])
    
    return model

def prepare_data():
    """
    Data preparation function (placeholder)
    In a real implementation, this would load and preprocess the motor fault dataset
    """
    # This is a placeholder - in a real implementation,
    # you would load your dataset here
    print("Data preparation would be implemented here")
    
    # Example data paths (would be replaced with actual paths)
    train_dir = "data/train"
    validation_dir = "data/validation"
    
    # Return dummy data for demonstration
    return train_dir, validation_dir

def train_model():
    """
    Main function to train the CNN model
    """
    # Set random seed for reproducibility
    tf.random.set_seed(42)
    
    # Get data directories
    train_dir, validation_dir = prepare_data()
    
    # Data augmentation for training set
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        fill_mode='nearest'
    )
    
    # Only rescaling for validation set
    validation_datagen = ImageDataGenerator(rescale=1./255)
    
    # Create data generators
    train_generator = train_datagen.flow_from_directory(
        train_dir,
        target_size=(128, 128),
        batch_size=32,
        class_mode='categorical'
    )
    
    validation_generator = validation_datagen.flow_from_directory(
        validation_dir,
        target_size=(128, 128),
        batch_size=32,
        class_mode='categorical'
    )
    
    # Determine number of classes from directory structure
    num_classes = len(train_generator.class_indices)
    
    # Create and compile model
    model = create_cnn_model((128, 128, 3), num_classes)
    
    # Train the model
    history = model.fit(
        train_generator,
        steps_per_epoch=train_generator.samples // 32,
        epochs=50,
        validation_data=validation_generator,
        validation_steps=validation_generator.samples // 32,
        callbacks=[
            tf.keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=5,
                restore_best_weights=True
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=3,
                min_lr=1e-6
            )
        ]
    )
    
    # Save the model
    model.save('motor_fault_cnn_model.h5')
    
    return model, history

if __name__ == "__main__":
    print("Starting CNN model training for motor fault detection")
    model, history = train_model()
    print("Model training completed successfully")