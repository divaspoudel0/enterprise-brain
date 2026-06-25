import io
import json
import uuid
from typing import Any
import structlog
import pandas as pd
from pypdf import PdfReader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from app.models.data_source import DataSource
from app.services.vector_service import VectorService
from app.services.ontology_service import OntologyService
from app.services.storage_service import StorageService

log = structlog.get_logger()


class ETLService:
    @staticmethod
    async def ingest_csv(data_source: DataSource, file_bytes: bytes, db: AsyncSession) -> int:
        df = pd.read_csv(io.BytesIO(file_bytes))
        df = df.dropna(how="all").drop_duplicates()
        records = df.to_dict(orient="records")

        for i, row in enumerate(records):
            doc_id = f"{data_source.id}-{i}"
            text = " | ".join(f"{k}: {v}" for k, v in row.items() if pd.notna(v))
            await VectorService.upsert(doc_id, text, {
                "source_id": data_source.id,
                "source_name": data_source.name,
                "row_index": i,
                "data": json.dumps({k: str(v) for k, v in row.items()}),
            })

        object_name = f"sources/{data_source.id}/data.csv"
        StorageService.upload_file(object_name, file_bytes, "text/csv")

        await db.execute(
            update(DataSource).where(DataSource.id == data_source.id).values(
                status="active", record_count=len(records)
            )
        )
        return len(records)

    @staticmethod
    async def ingest_excel(data_source: DataSource, file_bytes: bytes, db: AsyncSession) -> int:
        xf = pd.ExcelFile(io.BytesIO(file_bytes))
        total = 0
        for sheet in xf.sheet_names:
            df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet).dropna(how="all")
            records = df.to_dict(orient="records")
            for i, row in enumerate(records):
                doc_id = f"{data_source.id}-{sheet}-{i}"
                text = " | ".join(f"{k}: {v}" for k, v in row.items() if pd.notna(v))
                await VectorService.upsert(doc_id, text, {
                    "source_id": data_source.id,
                    "source_name": data_source.name,
                    "sheet": sheet,
                    "row_index": i,
                    "data": json.dumps({k: str(v) for k, v in row.items()}),
                })
            total += len(records)

        object_name = f"sources/{data_source.id}/data.xlsx"
        StorageService.upload_file(object_name, file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        await db.execute(
            update(DataSource).where(DataSource.id == data_source.id).values(
                status="active", record_count=total
            )
        )
        return total

    @staticmethod
    async def ingest_pdf(data_source: DataSource, file_bytes: bytes, db: AsyncSession) -> int:
        reader = PdfReader(io.BytesIO(file_bytes))
        chunks = []
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            for i in range(0, max(1, len(text)), 500):
                chunk = text[i:i + 500].strip()
                if chunk:
                    chunks.append((page_num, i // 500, chunk))

        for page_num, chunk_idx, chunk in chunks:
            doc_id = f"{data_source.id}-p{page_num}-c{chunk_idx}"
            await VectorService.upsert(doc_id, chunk, {
                "source_id": data_source.id,
                "source_name": data_source.name,
                "page": page_num,
                "chunk": chunk_idx,
            })

        object_name = f"sources/{data_source.id}/document.pdf"
        StorageService.upload_file(object_name, file_bytes, "application/pdf")

        await db.execute(
            update(DataSource).where(DataSource.id == data_source.id).values(
                status="active", record_count=len(chunks)
            )
        )
        return len(chunks)

    @staticmethod
    async def ingest_json(data_source: DataSource, data: list[dict], db: AsyncSession) -> int:
        for i, item in enumerate(data):
            doc_id = f"{data_source.id}-{i}"
            text = json.dumps(item)
            await VectorService.upsert(doc_id, text, {
                "source_id": data_source.id,
                "source_name": data_source.name,
                "index": i,
                "data": text,
            })
            label = item.get("_entity_type", "Entity")
            entity_id = str(item.get("id", f"{data_source.id}-{i}"))
            props = {k: v for k, v in item.items() if not k.startswith("_")}
            await OntologyService.upsert_entity(label, entity_id, props)

        await db.execute(
            update(DataSource).where(DataSource.id == data_source.id).values(
                status="active", record_count=len(data)
            )
        )
        return len(data)
