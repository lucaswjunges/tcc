import tensorflow as tf
import numpy as np
import cv2
import os

# Parâmetros de treinamento
EPOCHS = 100
BATCH_SIZE = 32
IMG_HEIGHT = 128
IMG_WIDTH = 128
LEARNING_RATE = 0.0001

# Caminho para o dataset
DATASET_DIR = 'dataset'

# Carregamento do dataset
def load_dataset():
    train_ds = tf.keras.preprocessing.image_dataset_from_directory(
        DATASET_DIR,
        validation_split=0.2,
        subset="training",
        seed=123,
        image_size=(IMG_HEIGHT, IMG_WIDTH),
        batch_size=BATCH_SIZE)

    val_ds = tf.keras.preprocessing.image_dataset_from_directory(
        DATASET_DIR,
        validation_split=0.2,
        subset="validation",
        seed=123,
        image_size=(IMG_HEIGHT, IMG_WIDTH),
        batch_size=BATCH_SIZE)
    return train_ds, val_ds


# Criação do modelo CNN
def create_model():
    model = tf.keras.models.Sequential([
        tf.keras.layers.Conv2D(16, 3, padding='same', activation='relu', input_shape=(IMG_HEIGHT, IMG_WIDTH, 3)),
        tf.keras.layers.MaxPooling2D(),
        tf.keras.layers.Conv2D(32, 3, padding='same', activation='relu'),
        tf.keras.layers.MaxPooling2D(),
        tf.keras.layers.Conv2D(64, 3, padding='same', activation='relu'),
        tf.keras.layers.MaxPooling2D(),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dense(1, activation='sigmoid') # Alterar para o número de classes de falha
    ])
    return model


# Treinamento do modelo
def train_model(model, train_ds, val_ds):
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
                  loss='binary_crossentropy', # Alterar de acordo com o tipo de problema (multiclasse, etc.)
                  metrics=['accuracy'])

    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS
    )
    return model, history


# Salvar o modelo treinado
def save_model(model):
    model.save('modelo_treinado.h5')


if __name__ == "__main__":
    train_ds, val_ds = load_dataset()
    model = create_model()
    model, history = train_model(model, train_ds, val_ds)
    save_model(model)
    print("Treinamento concluído e modelo salvo como modelo_treinado.h5")