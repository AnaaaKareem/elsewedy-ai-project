from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import relationship
from shared.infrastructure.database import Base

class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    category = Column(String(50), nullable=False)
    lead_time = Column(Integer, default=30)
    
    market_prices = relationship("MarketPrice", back_populates="material")
    ai_signals = relationship("AISignal", back_populates="material")

class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    code = Column(String(10), unique=True) # ISO or Trade Code

    ai_signals = relationship("AISignal", back_populates="country")

class MarketPrice(Base):
    __tablename__ = "market_prices"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"))
    price = Column(Float, nullable=False) # python float maps to double precision usually, checking init.sql was DECIMAL(10,2) but Float is often fine for simpler apps or use Numeric
    currency = Column(String(10), default='USD')
    source = Column(String(50))
    captured_at = Column(DateTime, default=func.now())

    material = relationship("Material", back_populates="market_prices")

    __table_args__ = (
        Index('idx_market_prices_mat_time', 'material_id', 'captured_at'),
    )

class AISignal(Base):
    __tablename__ = "ai_signals"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"))
    country_id = Column(Integer, ForeignKey("countries.id"))
    input_price = Column(Float, nullable=False)
    decision = Column(String(20), nullable=False)
    confidence_score = Column(Float)
    stockout_risk = Column(Float)
    created_at = Column(DateTime, default=func.now())

    material = relationship("Material", back_populates="ai_signals")
    country = relationship("Country", back_populates="ai_signals")

    __table_args__ = (
        Index('idx_ai_signals_mat_time', 'material_id', 'created_at'),
    )
