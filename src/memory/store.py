"""SQLite database schema for storing experiments, runs, metrics, issues, and lessons."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
import json

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

Base = declarative_base()


class Factor(Base):
    """Factor definitions stored as YAML specs."""
    __tablename__ = "factors"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)
    yaml = Column(Text, nullable=False)  # Full YAML spec
    created_at = Column(DateTime, default=datetime.utcnow)
    tags = Column(JSON)  # List of tags like ["momentum", "volatility"]
    
    # Relationships
    runs = relationship("Run", back_populates="factor")


class Run(Base):
    """Backtest run records."""
    __tablename__ = "runs"
    
    id = Column(Integer, primary_key=True)
    factor_id = Column(Integer, ForeignKey("factors.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    in_sample_start = Column(DateTime)
    in_sample_end = Column(DateTime)
    out_sample_start = Column(DateTime)
    out_sample_end = Column(DateTime)
    seed = Column(Integer)
    regime_label = Column(String)  # e.g., "high_vol", "bull", "bear"
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")  # pending, running, completed, failed
    
    # Relationships
    factor = relationship("Factor", back_populates="runs")
    metrics = relationship("Metric", back_populates="run", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="run", cascade="all, delete-orphan")


class Metric(Base):
    """Performance metrics for each run."""
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False)
    
    # Return metrics
    ann_ret = Column(Float)
    ann_vol = Column(Float)
    sharpe = Column(Float, index=True)
    maxdd = Column(Float, index=True)
    
    # IC metrics
    avg_ic = Column(Float, index=True)
    ic_std = Column(Float)
    ir = Column(Float, index=True)  # Information Ratio
    
    # Turnover
    turnover = Column(Float)
    turnover_monthly = Column(Float)
    
    # Hit rate
    hit_rate = Column(Float)
    
    # Distribution
    skew = Column(Float)
    kurt = Column(Float)
    
    # Additional metrics stored as JSON
    additional_metrics = Column(JSON)
    
    # Relationships
    run = relationship("Run", back_populates="metrics")


class Issue(Base):
    """Issues detected during validation."""
    __tablename__ = "issues"
    
    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False)
    type = Column(String, nullable=False, index=True)  # e.g., "leakage_detected", "unstable_ic"
    detail = Column(Text, nullable=False)
    severity = Column(String, default="warning")  # info, warning, error, critical
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    run = relationship("Run", back_populates="issues")


class Lesson(Base):
    """Lessons learned from runs (successes and failures)."""
    __tablename__ = "lessons"
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    tags = Column(JSON)  # List of tags
    source_run_id = Column(Integer, ForeignKey("runs.id"), nullable=True)
    lesson_type = Column(String, default="general")  # success, failure, general
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Additional metadata
    metadata = Column(JSON)


class ExperimentStore:
    """Interface for interacting with the experiment database."""
    
    def __init__(self, db_path: str = "experiments.db"):
        """Initialize the store with a SQLite database."""
        self.db_path = Path(db_path)
        self.engine = create_engine(f"sqlite:///{self.db_path}", echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
    
    def create_factor(self, name: str, yaml: str, tags: Optional[List[str]] = None) -> Factor:
        """Create a new factor record."""
        session = self.get_session()
        try:
            factor = Factor(name=name, yaml=yaml, tags=tags or [])
            session.add(factor)
            session.commit()
            session.refresh(factor)
            return factor
        finally:
            session.close()
    
    def get_factor(self, factor_id: int) -> Optional[Factor]:
        """Get a factor by ID."""
        session = self.get_session()
        try:
            return session.query(Factor).filter(Factor.id == factor_id).first()
        finally:
            session.close()
    
    def get_factor_by_name(self, name: str) -> Optional[Factor]:
        """Get a factor by name."""
        session = self.get_session()
        try:
            return session.query(Factor).filter(Factor.name == name).first()
        finally:
            session.close()
    
    def create_run(
        self,
        factor_id: int,
        start_date: datetime,
        end_date: datetime,
        in_sample_start: Optional[datetime] = None,
        in_sample_end: Optional[datetime] = None,
        out_sample_start: Optional[datetime] = None,
        out_sample_end: Optional[datetime] = None,
        seed: Optional[int] = None,
        regime_label: Optional[str] = None,
        status: str = "pending"
    ) -> Run:
        """Create a new run record."""
        session = self.get_session()
        try:
            run = Run(
                factor_id=factor_id,
                start_date=start_date,
                end_date=end_date,
                in_sample_start=in_sample_start,
                in_sample_end=in_sample_end,
                out_sample_start=out_sample_start,
                out_sample_end=out_sample_end,
                seed=seed,
                regime_label=regime_label,
                status=status
            )
            session.add(run)
            session.commit()
            session.refresh(run)
            return run
        finally:
            session.close()
    
    def update_run_status(self, run_id: int, status: str):
        """Update run status."""
        session = self.get_session()
        try:
            run = session.query(Run).filter(Run.id == run_id).first()
            if run:
                run.status = status
                session.commit()
        finally:
            session.close()
    
    def create_metrics(self, run_id: int, metrics_dict: Dict[str, Any]) -> Metric:
        """Create metrics for a run."""
        session = self.get_session()
        try:
            # Extract standard metrics
            metric = Metric(
                run_id=run_id,
                ann_ret=metrics_dict.get("ann_ret"),
                ann_vol=metrics_dict.get("ann_vol"),
                sharpe=metrics_dict.get("sharpe"),
                maxdd=metrics_dict.get("maxdd"),
                avg_ic=metrics_dict.get("avg_ic"),
                ic_std=metrics_dict.get("ic_std"),
                ir=metrics_dict.get("ir"),
                turnover=metrics_dict.get("turnover"),
                turnover_monthly=metrics_dict.get("turnover_monthly"),
                hit_rate=metrics_dict.get("hit_rate"),
                skew=metrics_dict.get("skew"),
                kurt=metrics_dict.get("kurt"),
                additional_metrics=metrics_dict.get("additional_metrics", {})
            )
            session.add(metric)
            session.commit()
            session.refresh(metric)
            return metric
        finally:
            session.close()
    
    def create_issue(
        self,
        run_id: int,
        issue_type: str,
        detail: str,
        severity: str = "warning"
    ) -> Issue:
        """Create an issue record."""
        session = self.get_session()
        try:
            issue = Issue(
                run_id=run_id,
                type=issue_type,
                detail=detail,
                severity=severity
            )
            session.add(issue)
            session.commit()
            session.refresh(issue)
            return issue
        finally:
            session.close()
    
    def create_lesson(
        self,
        title: str,
        body: str,
        tags: Optional[List[str]] = None,
        source_run_id: Optional[int] = None,
        lesson_type: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Lesson:
        """Create a lesson record."""
        session = self.get_session()
        try:
            lesson = Lesson(
                title=title,
                body=body,
                tags=tags or [],
                source_run_id=source_run_id,
                lesson_type=lesson_type,
                metadata=metadata or {}
            )
            session.add(lesson)
            session.commit()
            session.refresh(lesson)
            return lesson
        finally:
            session.close()
    
    def get_top_runs(self, limit: int = 10, order_by: str = "sharpe") -> List[Run]:
        """Get top runs ordered by a metric."""
        session = self.get_session()
        try:
            query = session.query(Run).join(Metric)
            if order_by == "sharpe":
                query = query.order_by(Metric.sharpe.desc())
            elif order_by == "avg_ic":
                query = query.order_by(Metric.avg_ic.desc())
            elif order_by == "ir":
                query = query.order_by(Metric.ir.desc())
            return query.limit(limit).all()
        finally:
            session.close()
    
    def get_failed_runs(self, limit: int = 100) -> List[Run]:
        """Get runs with issues."""
        session = self.get_session()
        try:
            return session.query(Run).join(Issue).filter(
                Issue.severity.in_(["error", "critical"])
            ).limit(limit).all()
        finally:
            session.close()

