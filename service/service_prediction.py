import pandas as pd
from datetime import date, timedelta
import joblib
from scipy.stats import boxcox

from repository.repository_transaction import RepositoryTransaction
from schema.schema_prediction import MinimalPredictionInput, RawSalesInput

class PredictionService:
    def __init__(self, model_path: str, columns_path: str, lambdas_path: str):
        self.model = joblib.load(model_path)
        self.training_columns = joblib.load(columns_path)
        self.lambdas = joblib.load(lambdas_path)

    def _extract_features(self, raw: RawSalesInput) -> dict:
        """Ekstraksi data mentah menjadi format yang dimengerti model"""
        
        # 1. Ekstraksi Gender dan Nama Produk
        # Men's Street Footwear -> Gender: Men's, Product: Street Footwear
        raw_p = raw.Product_Raw
        gender = "Men's" if "Men's" in raw_p else "Women's" if "Women's" in raw_p else "Unisex"
        
        # Bersihkan string produk (menghapus kata Men's atau Women's)
        product_clean = raw_p.replace("Men's ", "").replace("Women's ", "").strip()

        # 2. Ekstraksi Fitur Waktu dari Transaction_Date
        dt = raw.Transaction_Date
        
        return {
            'Retailer': raw.Retailer,
            'Region': raw.Region,
            'State': raw.State,
            'City': raw.City,
            'Product': product_clean,
            'Operating Margin': raw.Operating_Margin,
            'Gender': gender,
            'Price per Unit': raw.Price_per_Unit,
            'Month': dt.month,
            'DayofWeek': dt.weekday(), # 0=Senin, 6=Minggu
            'week': dt.isocalendar()[1]
        }

    def predict(self, raw_input: RawSalesInput):
        # Langkah 1: Ekstraksi fitur
        features = self._extract_features(raw_input)
        df = pd.DataFrame([features])

        # Langkah 2: Transformasi Box-Cox
        if 'Price per Unit' in self.lambdas:
            lmbda_price = self.lambdas['Price per Unit']
            # Pastikan nilai tidak 0 atau negatif sebelum boxcox
            df['Price per Unit'] = boxcox(df['Price per Unit'], lmbda=lmbda_price)

        # Langkah 3: Dummy Encoding & Alignment
        df_encoded = pd.get_dummies(df)
        df_final = df_encoded.reindex(columns=self.training_columns, fill_value=0)

        # Langkah 4: Prediksi
        prediction = self.model.predict(df_final)
        return prediction[0]
    

    # async def predict_smart(self, input_data: MinimalPredictionInput, repo: RepositoryTransaction):
    #     # A. Ambil Nama State (Region dihapus sesuai permintaan)
    #     location = await repo.get_state_from_city(input_data.City)
    #     if not location:
    #         raise ValueError(f"Data State untuk kota '{input_data.City}' tidak ditemukan.")
        
    #     state_name = location.state_name

    #     # B. Ambil Harga Terakhir
    #     last_price = await repo.get_last_price(input_data.Product_Raw, input_data.City)
    #     if last_price is None:
    #         raise ValueError(f"Harga terakhir untuk '{input_data.Product_Raw}' di {input_data.City} tidak ditemukan.")

    #     # C. Ekstraksi Fitur Otomatis
    #     tomorrow = date.today() + timedelta(days=1)
        
    #     # Ekstraksi Gender & Produk
    #     raw_p = input_data.Product_Raw
    #     gender = "Men's" if "Men's" in raw_p else "Women's" if "Women's" in raw_p else "Unisex"
    #     product_clean = raw_p.replace("Men's ", "").replace("Women's ", "").strip()

    #     # D. Susun Fitur (Tanpa Region)
    #     features = {
    #         'Retailer': input_data.Retailer,
    #         'State': state_name,
    #         'City': input_data.City,
    #         'Product': product_clean,
    #         'Operating Margin': input_data.Operating_Margin,
    #         'Sales Method': input_data.Sales_Method,
    #         'Gender': gender,
    #         'Price per Unit': float(last_price),
    #         'Month': tomorrow.month,
    #         'DayofWeek': tomorrow.weekday(),
    #         'week': tomorrow.isocalendar()[1]
    #     }

    #     # E. ML Processing
    #     df = pd.DataFrame([features])

    #     # Box-Cox
    #     if 'Price per Unit' in self.lambdas and last_price > 0:
    #         df['Price per Unit'] = boxcox(df['Price per Unit'], lmbda=self.lambdas['Price per Unit'])

    #     # Encoding & Alignment
    #     df_encoded = pd.get_dummies(df)
    #     df_final = df_encoded.reindex(columns=self.training_columns, fill_value=0)

    #     # F. Predict
    #     prediction = self.model.predict(df_final)

    #     return {
    #         "prediction_result": float(prediction[0]),
    #         "metadata": {
    #             "state_detected": state_name,
    #             "price_used": float(last_price),
    #             "prediction_date": tomorrow.isoformat()
    #         }
    #     }



    async def predict_comparison(self, input_data: MinimalPredictionInput, repo: RepositoryTransaction):
        # A. Ambil Data Lokasi & Historis Terakhir
        location = await repo.get_state_from_city(input_data.City)
        if not location:
            raise ValueError(f"Kota '{input_data.City}' tidak ditemukan di database.")

        history = await repo.get_latest_history(input_data.Product_Raw, input_data.City)
        if not history:
            raise ValueError(f"Data historis untuk produk '{input_data.Product_Raw}' di {input_data.City} belum ada.")

        last_price = float(history.price_per_unit)
        last_margin = float(history.operating_margin)

        # B. Persiapan Fitur Umum (Tanggal Besok & Gender)
        tomorrow = date.today() + timedelta(days=1)
        gender = "Men's" if "Men's" in input_data.Product_Raw else "Women's" if "Women's" in input_data.Product_Raw else "Unisex"
        product_clean = input_data.Product_Raw.replace("Men's ", "").replace("Women's ", "").strip()

        # C. Fungsi Internal Prediksi (untuk dijalankan 2x)
        def run_prediction(margin_to_use):
            feat = {
                'Retailer': input_data.Retailer,
                'State': location.state_name,
                'City': input_data.City,
                'Product': product_clean,
                'Operating Margin': margin_to_use,
                'Sales Method': input_data.Sales_Method,
                'Gender': gender,
                'Price per Unit': last_price,
                'Month': tomorrow.month,
                'DayofWeek': tomorrow.weekday(),
                'week': tomorrow.isocalendar()[1]
            }
            df = pd.DataFrame([feat])
            
            # Transformasi Box-Cox pada harga historis
            if 'Price per Unit' in self.lambdas and last_price > 0:
                df['Price per Unit'] = boxcox(df['Price per Unit'], lmbda=self.lambdas['Price per Unit'])
            
            df_encoded = pd.get_dummies(df).reindex(columns=self.training_columns, fill_value=0)
            return float(self.model.predict(df_encoded)[0])

        # D. Hitung 2 Skenario
        # 1. Skenario Historis (Margin Default dari DB)
        sales_hist = run_prediction(last_margin)
        profit_hist = sales_hist * last_margin

        # 2. Skenario Custom (Margin Baru dari User)
        sales_custom = run_prediction(input_data.New_Operating_Margin)
        profit_custom = sales_custom * input_data.New_Operating_Margin

        return {
            "historical_scenario": {
                "margin_used": last_margin,
                "predicted_total_sales": sales_hist,
                "estimated_profit": profit_hist
            },
            "custom_scenario": {
                "margin_used": input_data.New_Operating_Margin,
                "predicted_total_sales": sales_custom,
                "estimated_profit": profit_custom
            },
            "comparison": {
                "profit_diff": profit_custom - profit_hist,
                "is_better": (profit_custom > profit_hist),
                "target_date": tomorrow.isoformat(),
                "price_unit_used": last_price
            }
        }