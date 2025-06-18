import tensorflow as tf
import numpy as np
import os
from datetime import datetime

# Claude generated code, further might be change. Here only for example to collect trace

# Установка логов TensorFlow
tf.get_logger().setLevel('INFO')

print("TensorFlow версия:", tf.__version__)
print("GPU доступно:", tf.config.list_physical_devices('GPU'))

# Создание синтетических данных
def create_dataset(batch_size=32, num_samples=1000):
    """Создает синтетический датасет для обучения"""
    # Генерируем случайные данные
    X = np.random.randn(num_samples, 784).astype(np.float32)
    # Создаем синтетические метки (10 классов)
    y = np.random.randint(0, 10, size=(num_samples,))

    # Преобразуем в TensorFlow датасет
    dataset = tf.data.Dataset.from_tensor_slices((X, y))
    dataset = dataset.batch(batch_size)
    dataset = dataset.prefetch(tf.data.AUTOTUNE)

    return dataset

# Создание модели
def create_model():
    """Создает простую нейронную сеть"""
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(512, activation='relu', input_shape=(784,)),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(256, activation='relu'),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dense(10, activation='softmax')
    ])

    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )

    return model

# Функция тренировки с профилированием
@tf.function
def train_step(model, optimizer, loss_fn, x, y):
    """Один шаг тренировки"""
    with tf.GradientTape() as tape:
        predictions = model(x, training=True)
        loss = loss_fn(y, predictions)

    gradients = tape.gradient(loss, model.trainable_variables)
    optimizer.apply_gradients(zip(gradients, model.trainable_variables))

    return loss, predictions

def main():
    # Создание директории для логов профилировщика
    log_dir = f"./output_protobuf/{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    os.makedirs(log_dir, exist_ok=True)

    print(f"Логи профилировщика будут сохранены в: {log_dir}")

    # Создание модели и данных
    model = create_model()
    train_dataset = create_dataset(batch_size=64, num_samples=2000)

    # Настройка оптимизатора и функции потерь
    optimizer = tf.keras.optimizers.Adam(learning_rate=0.001)
    loss_fn = tf.keras.losses.SparseCategoricalCrossentropy()

    print("\nАрхитектура модели:")
    model.summary()

    # Запуск профилировщика
    print(f"\nЗапуск тренировки с профилированием...")

    # Опции профилировщика
    options = tf.profiler.experimental.ProfilerOptions(
        host_tracer_level=2,  # Детальное профилирование хоста
        python_tracer_level=1,  # Профилирование Python кода
        device_tracer_level=1   # Профилирование устройства
    )

    # Старт профилировщика
    tf.profiler.experimental.start(log_dir, options=options)

    try:
        # Обучение модели
        epoch_losses = []
        num_epochs = 5

        for epoch in range(num_epochs):
            print(f"\nЭпоха {epoch + 1}/{num_epochs}")
            epoch_loss = 0
            num_batches = 0

            for batch_x, batch_y in train_dataset:
                # Выполняем шаг тренировки
                loss, predictions = train_step(model, optimizer, loss_fn, batch_x, batch_y)
                epoch_loss += loss
                num_batches += 1

                # Выводим прогресс каждые 10 батчей
                if num_batches % 10 == 0:
                    print(f"  Батч {num_batches}, Loss: {loss:.4f}")

            avg_loss = epoch_loss / num_batches
            epoch_losses.append(avg_loss.numpy())
            print(f"  Средняя потеря за эпоху: {avg_loss:.4f}")

        # Дополнительные операции для демонстрации профилирования
        print("\nВыполнение дополнительных операций для профилирования...")

        # Создание больших тензоров и операций
        with tf.name_scope("large_operations"):
            large_tensor = tf.random.normal([2000, 2000], name="large_tensor")
            matrix_mult = tf.matmul(large_tensor, large_tensor, name="matrix_multiplication")
            conv_input = tf.random.normal([32, 224, 224, 3], name="conv_input")

            # Операции конволюции
            conv_layer = tf.keras.layers.Conv2D(64, 3, activation='relu', name="conv_layer")
            conv_output = conv_layer(conv_input)

            # Операции на GPU (если доступно)
            if tf.config.list_physical_devices('GPU'):
                with tf.device('/GPU:0'):
                    gpu_computation = tf.reduce_sum(tf.square(matrix_mult), name="gpu_reduction")

        print("Дополнительные операции завершены")

    finally:
        # Остановка профилировщика
        tf.profiler.experimental.stop()
        print(f"\nПрофилирование завершено. Логи сохранены в: {log_dir}")

    # Вывод результатов
    print(f"\nРезультаты тренировки:")
    print(f"Потери по эпохам: {[f'{loss:.4f}' for loss in epoch_losses]}")

if __name__ == "__main__":
    main()