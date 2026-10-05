import logging
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, regularizers

from src.config import (
    N_CHANNELS, BAND_NAMES, STAT_FEATURES,
    CNN_FILTERS, CNN_KERNEL_SIZE, CNN_POOL_SIZE,
    LSTM_UNITS, LSTM_DROPOUT,
    META_DENSE_UNITS, META_DROPOUT,
    LEARNING_RATE,
)

logger = logging.getLogger(__name__)

N_BANDS = len(BAND_NAMES)
N_STATS = len(STAT_FEATURES)

CNN_TIMESTEPS = N_CHANNELS
CNN_FEATURES = N_BANDS * N_STATS

LSTM_TIMESTEPS = N_BANDS
LSTM_FEATURES = N_CHANNELS * N_STATS


def build_model() -> keras.Model:
    cnn_input = keras.Input(shape=(CNN_TIMESTEPS, CNN_FEATURES), name="cnn_input")
    lstm_input = keras.Input(shape=(LSTM_TIMESTEPS, LSTM_FEATURES), name="lstm_input")

    cnn = _build_cnn_stream(cnn_input)
    lstm_out = _build_lstm_stream(lstm_input)

    merged = layers.Concatenate(name="stream_fusion")([cnn, lstm_out])
    output = _build_meta_classifier(merged)

    model = keras.Model(
        inputs=[cnn_input, lstm_input],
        outputs=output,
        name="DualStream_CNN_LSTM_Ensemble",
    )

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss="binary_crossentropy",
        metrics=[
            "accuracy",
            keras.metrics.AUC(name="auc"),
            keras.metrics.Precision(name="precision"),
            keras.metrics.Recall(name="recall"),
        ],
    )

    logger.info(f"Model built | parameters: {model.count_params():,}")
    return model


def get_callbacks(model_save_path: str) -> list:
    return [
        keras.callbacks.EarlyStopping(
            monitor="val_auc",
            patience=10,
            mode="max",
            restore_best_weights=True,
            verbose=1,
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=5,
            min_lr=1e-6,
            verbose=1,
        ),
        keras.callbacks.ModelCheckpoint(
            filepath=model_save_path,
            monitor="val_auc",
            save_best_only=True,
            mode="max",
            save_format="h5",
            verbose=1,
        ),
    ]


def _build_cnn_stream(cnn_input: tf.Tensor) -> tf.Tensor:
    x = cnn_input

    for i, n_filters in enumerate(CNN_FILTERS):
        x = layers.Conv1D(
            filters=n_filters,
            kernel_size=CNN_KERNEL_SIZE,
            padding="same",
            kernel_regularizer=regularizers.l2(1e-4),
            name=f"cnn_conv_{i+1}",
        )(x)
        x = layers.BatchNormalization(name=f"cnn_bn_{i+1}")(x)
        x = layers.ReLU(name=f"cnn_relu_{i+1}")(x)

        if i == 0:
            x = layers.MaxPooling1D(pool_size=CNN_POOL_SIZE, name="cnn_maxpool")(x)

    cnn_out = layers.GlobalAveragePooling1D(name="cnn_gap")(x)
    return cnn_out


def _build_lstm_stream(lstm_input: tf.Tensor) -> tf.Tensor:
    x = lstm_input

    x = layers.LSTM(
        units=LSTM_UNITS[0],
        return_sequences=True,
        recurrent_dropout=LSTM_DROPOUT,
        name="lstm_layer_1",
    )(x)
    x = layers.Dropout(LSTM_DROPOUT, name="lstm_dropout_1")(x)

    lstm_out = layers.LSTM(
        units=LSTM_UNITS[1],
        return_sequences=False,
        recurrent_dropout=LSTM_DROPOUT,
        name="lstm_layer_2",
    )(x)
    lstm_out = layers.Dropout(LSTM_DROPOUT, name="lstm_dropout_2")(lstm_out)

    return lstm_out


def _build_meta_classifier(merged: tf.Tensor) -> tf.Tensor:
    x = merged

    for i, units in enumerate(META_DENSE_UNITS):
        x = layers.Dense(
            units=units,
            activation="relu",
            kernel_regularizer=regularizers.l2(1e-4),
            name=f"meta_dense_{i+1}",
        )(x)
        x = layers.BatchNormalization(name=f"meta_bn_{i+1}")(x)
        x = layers.Dropout(META_DROPOUT, name=f"meta_dropout_{i+1}")(x)

    output = layers.Dense(1, activation="sigmoid", name="output")(x)
    return output
