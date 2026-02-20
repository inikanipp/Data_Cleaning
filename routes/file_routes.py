from fastapi import FastAPI, UploadFile, File, HTTPException, APIRouter
# import pandas as pd
import polars as pl
import io

# # app = FastAPI()
# router = APIRouter(prefix='/api/v1')

# @router.post("/upload-excel/")
# async def upload_excel(file: UploadFile = File(...)):
#     # 1. Validasi ekstensi file
#     if not file.filename.endswith(('.xlsx', '.xls')):
#         raise HTTPException(status_code=400, detail="File harus berupa Excel (.xlsx atau .xls)")

#     try:
#         contents = await file.read()
        
#         buffer = io.BytesIO(contents)
#         df = pl.read_excel(buffer)

#         data = df[:5].to_dict(as_series=False)

#         return {
#             "filename": file.filename,
#             "row_count": len(df),
#             "data": data 
#         }
#     except Exception as e:
#         return {"error": f"Gagal memproses file: {str(e)}"}

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from config.database import get_db

# Import semua repository
from repository.repository_city import RepositoryCity
from repository.repository_method import RepositoryMethod
from repository.repository_product import RepositoryProduct
from repository.repository_retailer import RepositoryRetailer
from repository.repository_transaction import RepositoryTransaction
from schema.schema_prediction import MinimalPredictionInput, RawSalesInput
from service.service_cleaning import ServiceTransaction
from service.service_polars import ServicePolars
from service.service_prediction import PredictionService

router = APIRouter()

@router.post("/upload-transaction")
async def upload_transaction_excel(
    file: UploadFile = File(...), 
    db: AsyncSession = Depends(get_db),
    service_polars_tool: ServicePolars = Depends(ServicePolars)
):
    # 1. Instansiasi semua Repository dengan session db yang sama
    repo_city = RepositoryCity(db)
    repo_method = RepositoryMethod(db)
    repo_product = RepositoryProduct(db)
    repo_retailer = RepositoryRetailer(db)
    repo_transaction = RepositoryTransaction(db)

    # 2. Masukkan repository ke dalam Service
    # Pastikan __init__ di ServiceTransaction kamu sudah menerima semua repo ini
    service = ServiceTransaction(
        repo_city=repo_city,
        repo_method=repo_method,
        repo_product=repo_product,
        repo_retailer=repo_retailer,
        repo_transaction=repo_transaction,
        service_polars=service_polars_tool
    )

    # 3. Jalankan fungsi proses excel
    result = await service.process_excel_users(file)
    
    return {"status": "success", "total_processed": len(result)}



predict_service = PredictionService(
    model_path='routes/model1.pkl',
    columns_path='routes/columns_structure1.pkl',
    lambdas_path='routes/model_lambdas1.pkl'
)


# Import session database Anda, contoh: from database import get_db

# @router.post("/predict")
# async def do_predict(data: MinimalPredictionInput, db: AsyncSession = Depends(get_db)):
#     try:
#         repo = RepositoryTransaction(db)
#         result = await predict_service.predict_smart(data, repo)
#         return {"status": "success", "data": result}
#     except ValueError as ve:
#         raise HTTPException(status_code=404, detail=str(ve))
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Terjadi kesalahan: {str(e)}")


# @router.post("/predict")
# async def compare_sales(data: MinimalPredictionInput, db: AsyncSession = Depends(get_db)):
#     try:
#         repo = RepositoryTransaction(db)
#         result = await predict_service.predict_comparison(data, repo)
#         return {"status": "success", "data": result}
#     except ValueError as ve:
#         raise HTTPException(status_code=404, detail=str(ve))
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error: {str(e)}")



@router.post("/predict-comparison")
async def handle_prediction(data: MinimalPredictionInput, db: AsyncSession = Depends(get_db)):
    try:
        repo = RepositoryTransaction(db)
        result = await predict_service.predict_comparison(data, repo)
        return {"status": "success", "data": result}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        # Menangani error nama kolom/atribut database
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan: {str(e)}")