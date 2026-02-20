"""Persistent storage for AutoML configurations and results."""

from typing import Optional, List
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import json
from loguru import logger

from .config import settings

Base = declarative_base()


class PipelineRecord(Base):
    """Database model for pipeline records."""
    __tablename__ = "pipelines"
    
    id = Column(String, primary_key=True)
    name = Column(String, index=True)
    config = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class ExecutionRecord(Base):
    """Database model for execution records."""
    __tablename__ = "executions"
    
    id = Column(String, primary_key=True)
    pipeline_id = Column(String)
    model_used = Column(String)
    prompt = Column(String)
    output = Column(String)
    latency = Column(Float)
    cost = Column(Float)
    tokens_used = Column(Integer)
    success = Column(Integer, default=1)
    error_message = Column(String, nullable=True)
    metadata = Column(JSON)
    timestamp = Column(DateTime, default=datetime.now, index=True)


class PromptVariantRecord(Base):
    """Database model for prompt variants."""
    __tablename__ = "prompt_variants"
    
    id = Column(String, primary_key=True)
    pipeline_id = Column(String)
    original_prompt = Column(String)
    optimized_prompt = Column(String)
    metrics = Column(JSON)
    score = Column(Float)
    version = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)


class StorageManager:
    """Manages persistent storage for AutoML service."""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.database_url
        self.engine = create_engine(self.database_url)
        Base.metadata.create_all(self.engine)
        SessionLocal = sessionmaker(bind=self.engine)
        self.db = SessionLocal()
        logger.info(f"Initialized storage: {self.database_url}")
    
    def save_pipeline_config(self, pipeline_id: str, name: str, config: dict) -> None:
        """Save pipeline configuration."""
        try:
            record = PipelineRecord(
                id=pipeline_id,
                name=name,
                config=config
            )
            self.db.merge(record)
            self.db.commit()
            logger.info(f"Saved pipeline config: {pipeline_id}")
        except Exception as e:
            logger.error(f"Failed to save pipeline config: {e}")
            self.db.rollback()
    
    def get_pipeline_config(self, pipeline_id: str) -> Optional[dict]:
        """Retrieve pipeline configuration."""
        try:
            record = self.db.query(PipelineRecord).filter_by(id=pipeline_id).first()
            return record.config if record else None
        except Exception as e:
            logger.error(f"Failed to get pipeline config: {e}")
            return None
    
    def save_execution(
        self,
        execution_id: str,
        pipeline_id: str,
        model_used: str,
        prompt: str,
        output: str,
        latency: float,
        cost: float = 0.0,
        tokens_used: int = 0,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        """Save execution record."""
        try:
            record = ExecutionRecord(
                id=execution_id,
                pipeline_id=pipeline_id,
                model_used=model_used,
                prompt=prompt,
                output=output,
                latency=latency,
                cost=cost,
                tokens_used=tokens_used,
                success=1 if success else 0,
                error_message=error_message,
                metadata=metadata or {},
            )
            self.db.add(record)
            self.db.commit()
            logger.debug(f"Saved execution: {execution_id}")
        except Exception as e:
            logger.error(f"Failed to save execution: {e}")
            self.db.rollback()
    
    def save_prompt_variant(
        self,
        variant_id: str,
        pipeline_id: str,
        original_prompt: str,
        optimized_prompt: str,
        metrics: dict,
        score: float,
        version: int,
    ) -> None:
        """Save prompt variant."""
        try:
            record = PromptVariantRecord(
                id=variant_id,
                pipeline_id=pipeline_id,
                original_prompt=original_prompt,
                optimized_prompt=optimized_prompt,
                metrics=metrics,
                score=score,
                version=version,
            )
            self.db.add(record)
            self.db.commit()
            logger.debug(f"Saved prompt variant: {variant_id}")
        except Exception as e:
            logger.error(f"Failed to save prompt variant: {e}")
            self.db.rollback()
    
    def get_execution_history(
        self,
        pipeline_id: str,
        limit: int = 100,
    ) -> List[dict]:
        """Get execution history for a pipeline."""
        try:
            records = self.db.query(ExecutionRecord).filter_by(
                pipeline_id=pipeline_id
            ).order_by(ExecutionRecord.timestamp.desc()).limit(limit).all()
            
            return [
                {
                    "id": r.id,
                    "model": r.model_used,
                    "latency": r.latency,
                    "success": bool(r.success),
                    "timestamp": r.timestamp.isoformat(),
                }
                for r in records
            ]
        except Exception as e:
            logger.error(f"Failed to get execution history: {e}")
            return []
    
    def get_performance_stats(self, pipeline_id: str) -> dict:
        """Get performance statistics for a pipeline."""
        try:
            records = self.db.query(ExecutionRecord).filter_by(
                pipeline_id=pipeline_id,
                success=1
            ).all()
            
            if not records:
                return {"message": "No successful executions"}
            
            latencies = [r.latency for r in records]
            
            return {
                "total_executions": len(records),
                "average_latency": sum(latencies) / len(latencies),
                "min_latency": min(latencies),
                "max_latency": max(latencies),
                "total_cost": sum(r.cost for r in records),
            }
        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {}
    
    def close(self) -> None:
        """Close database connection."""
        self.db.close()
        logger.info("Storage connection closed")
