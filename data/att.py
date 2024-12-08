import pandas as pd

# Путь к Excel-файлу
file_path = "data/official_attribute_data/fall2024.xlsx"

# Загрузка данных из файла Excel
df = pd.read_excel(file_path)

attributes = df['Attribute'].dropna().str.split(',').explode()

# Удаление лишних пробелов и получение уникальных значений
unique_attributes = attributes.str.strip().unique()

# Сортировка уникальных значений для удобства
unique_attributes = sorted(unique_attributes)

# Сохранение или вывод результата
print("Уникальные значения в столбце Attribute:")
for attr in unique_attributes:
    print(attr)