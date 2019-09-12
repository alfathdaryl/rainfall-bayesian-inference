# -*- coding: utf-8 -*-
"""Final_Project_BMKG.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1zKep9OIYjLiISMJpEWzFU1yknzszwUZ1
"""

#!pip install -U scikit-learn
# ^ Pake jika import gagal
# ^ Setelah dirun, restart runtime

import pandas as pd
import numpy as np
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, classification_report, jaccard_score

# List yang berisi semua nama file
excel_filenames = [bulan + " 2018.xlsx" for bulan in ["Januari", "Februari", "Maret", 
                                                       "April", "Mei", "Juni", 
                                                       "Juli", "Agustus", "September", 
                                                       "Oktober", "November", "Desember"]]

# Mengambil file .xlsx dan mengubah .xslx menjadi dataframe
def excelparser(excel_filename):
  # Hapus header sebanyak 8 baris dan footer sebanyak 12 baris
  return pd.read_excel(excel_filename, header = 8, skipfooter = 12)

# Gabung file .xlsx menjadi 1 dataframe
def excelcombiner(excel_filename):
  # Buat list kosong yang akan menyimpan banyak dataframes
  df_list = []
  
  # Iterasi semua file .xlsx untuk dibuat dataframenya dan dikumpulkan kedalam list df_list
  for item in excel_filename:
    df_list.append(excelparser(item))
  
  # Gabungkan semua isi df_list menjadi satu dataframe dan mulai hitungan index dari 0
  return pd.concat(df_list, ignore_index = True)

# Buat file csv dari semua file .xslx dengan mengambil list yang berisi nama .xslx
def csv_create(excel_filename):
  # Ambil nama file excel yang akan dibuat ke csv lalu masukkan kedalam fungsi excelcombiner
  df = excelcombiner(excel_filename)
  
  # Buat file csv dengan dataframe yang diambil tanpa memedulikan index
  return df.to_csv("final.csv", index = False)

# Buat file csv dari semua file .xslx 
csv_create(excel_filenames)

# Preprocess csv yang dibuat agar mempunyai nama kolom yang dapat dimengerti dan format yang sesuai
def csv_preprocess(csv_filename):
  # Read filename dari argumen dan ambil
  df = pd.read_csv(csv_filename)
  
  # Buang kolom tanggal
  df = df.drop(columns=["Tanggal"])
  
  # Ubah nama kolom
  df.columns = ["suhu_rendah", "suhu_tinggi", "lembap_rata", 
                "curah_hujan","lama_sinar", "cepat_angin_rata"]
  
  # Tukar nama kolom dan buat curah_hujan ke bagian kiri
  df = df.reindex(columns=["suhu_rendah", "suhu_tinggi", "lembap_rata", 
                           "lama_sinar", "cepat_angin_rata", "curah_hujan"])
  
  # Buang row apabila data tidak ada (8888.0 / NaN)
  df = df.drop(df[(df.curah_hujan == 8888.0) | (np.isnan(df.curah_hujan))].index)
  
  
  # Lakukan iterasi pada setiap row dan ubah nilai curah_hujan sesuai klasifikasi BMKG
  for idx, row in df.iterrows():
    if  df.loc[idx,'curah_hujan'] < 20:
        df.loc[idx,'curah_hujan'] = "ringan"
    elif df.loc[idx,'curah_hujan'] < 40:
        df.loc[idx,'curah_hujan'] = "sedang"
    else:
        df.loc[idx,'curah_hujan'] = "deras"
  
  return df.reset_index(drop = True)

# Lakukan fungsi preprocess terhadap file .csv
csv_preprocess("final.csv")

# Membuat dataframe yang berisi informasi standar defiasi dan rata-rata dari setiap kelas dan feature
def generate_df_std_mean(csv_filename):
  # Mengambil dataframe yang telah di preprocess
  df = csv_preprocess(csv_filename)
  
  # Membuat list berisi himpunan dataframe
  df_list = []
  
  # Menambahkan dataframe khusus tabel khusus dengan yang mempunyai nilai kelas masing-masing serta fiturnya
  for klasifikasi in df[df.columns[-1]].unique():
    df_list.append(df.loc[df[df.columns[-1]] == klasifikasi])
    df_list.append(df.loc[df[df.columns[-1]] == klasifikasi])
  
  # Mengaplikasikan rumus pada list dataframe untuk menghasilkan standar deviasi dan rata-rata untuk setiap kelas dan fitur
  for index, df in enumerate(df_list):
    for column in df.columns:
      if column != df.columns[-1] and index % 2 == 0:
        average_col = df.loc[:,column].mean()
        df.loc[:,column] = average_col
      elif column != df.columns[-1]:
        average_col = df.loc[:,column].std()
        df.loc[:,column] = average_col
        
  # Mengmperbaiki format dataframe agar sesuai dan mudah diolah        
  df = pd.concat(df_list, ignore_index = True).drop_duplicates().reset_index(drop = True)
  new_index = zip(df.iloc[:, -1], ["rata" if index % 2 == 0 else "std" for index in range(len(df))])
  new_index = pd.MultiIndex.from_tuples(new_index)
  df = df.drop(columns = df.columns[-1])
  df = pd.DataFrame(df.values, index=new_index, columns=df.columns)
  
  # Mengembalikan dataframe
  return df

generate_df_std_mean("final.csv")

# Fungsi Gaussian Naive Bayes yang sesuai dengan isi paper
def function_gnb(x, std_feature, mean_feature):
  return (1 / (std_feature * np.sqrt(2 * np.pi))) * (np.e ** (-(x - mean_feature)**2/(2 * (std_feature**2))))

# 1. Fungsi prediksi yang akan mengembalikan prediksi setiap kelas dengan nilai prediksinya
# 2. Fungsi mengambil fitur yang akan diprediksi dalam bentuk dictionary, dan mengambil 
#    dataframe yang berisi nilai standar deviasi dan rata-rata setiap kelas dan fitur
def predict_gnb(dict_feature, df_std_mean):
  
  # Ambil kelas yang ada pada dataframe
  predict_class = set([item[0] for item in list(df_std_mean.index)])
  
  # Ambil keys dari input dict
  actual_predict = dict.fromkeys(predict_class)

  
  # Mengiterasi dan mengaplikasikan rumus gaussian NB untuk setiap fitur berdasarkan fitur input
  for item in actual_predict.copy():
    semi_predict = []
    
    for key, value in dict_feature.items():
      semi_predict.append(function_gnb(value,
                                       df_std_mean.loc[(item, "std"), key], 
                                       df_std_mean.loc[(item, "rata"), key]))
      
    actual_predict[item] = np.prod(semi_predict)
  
  return actual_predict
 	
# Fungsi yang menghasilkan keys yang mempunyai nilai tertinggi
def highest_dict(_dict):
  return max(_dict, key = lambda key: _dict[key])


prediksi = {"suhu_rendah": 25.8,"suhu_tinggi": 32.4,"lembap_rata": 79,"lama_sinar": 4.6,"cepat_angin_rata": 1}
prediksi_dict = predict_gnb(prediksi, generate_df_std_mean("final.csv"))
print(prediksi_dict)
highest_dict(prediksi_dict)

# Fungsi untuk membuat tuple yang berisi list hasil_benar, list hasil_prediksi,list dan kelas
def generate_pred_true(csv_filename):
  # Ambil dataframe dari csv
  df = csv_preprocess(csv_filename)
  
  # Ambil dataframs std dan rata-rata dari csv
  df_std_mean = generate_df_std_mean(csv_filename)
  
  # Ambil list hasil benar menggunakan fungsi iloc
  true = list(df.iloc[:,-1])
  
  # Buat list kosong yang akan diisi prediksi
  pred = []
  
  # Buat list berisi kelas
  labels = df[df.columns[-1]].unique()
  
  # Buat dictionary dari setiap row dataframe
  dict_list = csv_preprocess(csv_filename).iloc[:,:-1].to_dict('records')
  
  # Aplikasikan fungsi dari setiap dictionary yang dibuat dari setiap row dataframe kedalam fungsi predict_gnb
  for dict_pred in dict_list:
    pred.append(highest_dict(predict_gnb(dict_pred, df_std_mean)))
    
  # Kembalikan tuple yang berisi list hasil_benar, list hasil_prediksi,list dan kelas
  return (true, pred, df[df.columns[-1]].unique())

tp_tuple = generate_pred_true("final.csv")

# Fungsi untuk membuat laporan confusion matrix, akurasi, presisi, recall, dan error ratio
def generate_report(tp_tuple):
  # Ambil nilai dari tuple
  true, pred, labels = tp_tuple
  
  # Aplikasikan semua variabel kedalam fungsi yang disediakan library scikit-learn
  cf_matrix = confusion_matrix(true, pred, labels = labels)
  accuracy =  jaccard_score(true, pred, average = None, labels = labels)
  precision = precision_score(true, pred, average = None, labels = labels)
  recall = recall_score(true, pred, average = None, labels = labels)
  error_ratio = np.array([1 - rate for rate in accuracy])
  
  # Print hasil
  print("Confussion Matrix : (dengan nilai Ringan, Sedang, Deras secara berurutan)\n", cf_matrix)
  print("\nAkurasi : \t", accuracy)
  print("Precision : \t", precision)
  print("Recall : \t", recall)
  print("Error Ratio : \t", error_ratio) 
  
generate_report(tp_tuple)
