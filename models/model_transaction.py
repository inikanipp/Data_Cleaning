from typing import Optional
import datetime
import decimal
import uuid

from sqlalchemy import Boolean, Date, ForeignKeyConstraint, Index, Integer, Numeric, PrimaryKeyConstraint, String, Text, Uuid, text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class Method(Base):
    __tablename__ = 'method'
    __table_args__ = (
        PrimaryKeyConstraint('id_method', name='method_pkey'),
        Index('method_method_key', 'method', postgresql_include=[], unique=True)
    )

    id_method: Mapped[int] = mapped_column(Integer, primary_key=True)
    method: Mapped[str] = mapped_column(String, nullable=False)

    transaction: Mapped[list['Transaction']] = relationship('Transaction', back_populates='method')


class Product(Base):
    __tablename__ = 'product'
    __table_args__ = (
        PrimaryKeyConstraint('id_product', name='product_pkey'),
        Index('product_product_key', 'product', postgresql_include=[], unique=True)
    )

    id_product: Mapped[int] = mapped_column(Integer, primary_key=True)
    product: Mapped[str] = mapped_column(String, nullable=False)

    transaction: Mapped[list['Transaction']] = relationship('Transaction', back_populates='product')


class Retailer(Base):
    __tablename__ = 'retailer'
    __table_args__ = (
        PrimaryKeyConstraint('id_retailer', name='retailer_pkey'),
        Index('retailer_retailer_name_key', 'retailer_name', postgresql_include=[], unique=True)
    )

    id_retailer: Mapped[int] = mapped_column(Integer, primary_key=True)
    retailer_name: Mapped[str] = mapped_column(String, nullable=False)

    transaction: Mapped[list['Transaction']] = relationship('Transaction', back_populates='retailer')


class State(Base):
    __tablename__ = 'state'
    __table_args__ = (
        PrimaryKeyConstraint('id_state', name='state_pkey'),
        Index('state_state_key', 'state', postgresql_include=[], unique=True)
    )

    id_state: Mapped[int] = mapped_column(Integer, primary_key=True)
    state: Mapped[str] = mapped_column(String, nullable=False)
    region: Mapped[str] = mapped_column(String, nullable=False)

    city: Mapped[list['City']] = relationship('City', back_populates='state')


class UploadHistory(Base):
    __tablename__ = 'upload_history'
    __table_args__ = (
        PrimaryKeyConstraint('id_upload', name='upload_history_pkey'),
        Index('upload_history_system_name_key', 'system_name', postgresql_include=[], unique=True)
    )

    id_upload: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    system_name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'PENDING'::text"))
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    note: Mapped[Optional[str]] = mapped_column(Text)
    uploaded_by: Mapped[Optional[str]] = mapped_column(String)
    upload_date: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=6), server_default=text('CURRENT_TIMESTAMP'))

    transaction: Mapped[list['Transaction']] = relationship('Transaction', back_populates='upload_history')


class Users(Base):
    __tablename__ = 'users'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='users_pkey'),
        Index('users_email_key', 'email', postgresql_include=[], unique=True)
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    email: Mapped[Optional[str]] = mapped_column(Text)
    password: Mapped[Optional[str]] = mapped_column(Text)
    role: Mapped[Optional[str]] = mapped_column(Text, server_default=text("'STAFF'::text"))


class City(Base):
    __tablename__ = 'city'
    __table_args__ = (
        ForeignKeyConstraint(['id_state'], ['state.id_state'], ondelete='CASCADE', onupdate='CASCADE', name='city_id_state_fkey'),
        PrimaryKeyConstraint('id_city', name='city_pkey'),
        Index('city_city_key', 'city', postgresql_include=[], unique=True)
    )

    id_city: Mapped[int] = mapped_column(Integer, primary_key=True)
    city: Mapped[str] = mapped_column(String, nullable=False)
    id_state: Mapped[int] = mapped_column(Integer, nullable=False)

    state: Mapped['State'] = relationship('State', back_populates='city')
    transaction: Mapped[list['Transaction']] = relationship('Transaction', back_populates='city')


class Transaction(Base):
    __tablename__ = 'transaction'
    __table_args__ = (
        ForeignKeyConstraint(['id_city'], ['city.id_city'], onupdate='CASCADE', name='transaction_id_city_fkey'),
        ForeignKeyConstraint(['id_method'], ['method.id_method'], onupdate='CASCADE', name='transaction_id_method_fkey'),
        ForeignKeyConstraint(['id_product'], ['product.id_product'], onupdate='CASCADE', name='transaction_id_product_fkey'),
        ForeignKeyConstraint(['id_retailer'], ['retailer.id_retailer'], onupdate='CASCADE', name='transaction_id_retailer_fkey'),
        ForeignKeyConstraint(['id_upload'], ['upload_history.id_upload'], ondelete='CASCADE', onupdate='CASCADE', name='transaction_id_upload_fkey'),
        PrimaryKeyConstraint('id_transaction', name='transaction_pkey')
    )

    id_transaction: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_retailer: Mapped[int] = mapped_column(Integer, nullable=False)
    id_product: Mapped[int] = mapped_column(Integer, nullable=False)
    id_method: Mapped[int] = mapped_column(Integer, nullable=False)
    id_city: Mapped[int] = mapped_column(Integer, nullable=False)
    id_upload: Mapped[Optional[int]] = mapped_column(Integer)
    invoice_date: Mapped[Optional[datetime.date]] = mapped_column(Date, server_default=text('CURRENT_DATE'))
    price_per_unit: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    unit_sold: Mapped[Optional[int]] = mapped_column(Integer)
    total_sales: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    operating_profit: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    operating_margin: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    is_approved: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))

    city: Mapped['City'] = relationship('City', back_populates='transaction')
    method: Mapped['Method'] = relationship('Method', back_populates='transaction')
    product: Mapped['Product'] = relationship('Product', back_populates='transaction')
    retailer: Mapped['Retailer'] = relationship('Retailer', back_populates='transaction')
    upload_history: Mapped[Optional['UploadHistory']] = relationship('UploadHistory', back_populates='transaction')
