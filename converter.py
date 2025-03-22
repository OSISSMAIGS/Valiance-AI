import json
import csv

def dict_to_json(dictionary, filename):
    """
    Mengonversi dictionary ke file JSON.
    """
    with open(filename, 'w', encoding='utf-8') as json_file:
        json.dump(dictionary, json_file, indent=4, ensure_ascii=False)

def csv_to_json(csv_filename, json_filename):
    """
    Mengonversi file CSV ke file JSON.
    Setiap baris dalam CSV akan dikonversi menjadi sebuah dictionary,
    dan keseluruhan data akan disimpan sebagai list of dictionaries.
    """
    data = []
    with open(csv_filename, 'r', encoding='utf-8') as csv_file:
        # Menggunakan csv.DictReader agar setiap baris menjadi dictionary
        reader = csv.DictReader(csv_file)
        for row in reader:
            data.append(row)
            
    with open(json_filename, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)

# Contoh penggunaan:
if __name__ == '__main__':
    # Contoh konversi dictionary ke JSON
    data_dict = {
        "name": "Kevin",
        "age": 25,
        "city": "New York"
    }
    dict_to_json(data_dict, "output_dict.json")

    csv_to_json("input.csv", "output_csv.json")
