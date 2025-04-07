"""
Update database to add proof approval fields to OrderFile model
"""
import os
import sys
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import text

from app import app, db
from models import OrderFile

def migrate_proof_approval_fields():
    """Add proof approval fields to OrderFile table"""
    with app.app_context():
        # Check if the fields already exist
        conn = db.engine.connect()
        inspector = db.inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('order_file')]

        # For SQLite, we need to add columns without constraints
        if 'approval_token' not in columns:
            print("Adding approval_token column to order_file table...")
            conn.execute(text("ALTER TABLE order_file ADD COLUMN approval_token VARCHAR(100)"))
            
        if 'approval_status' not in columns:
            print("Adding approval_status column to order_file table...")
            conn.execute(text("ALTER TABLE order_file ADD COLUMN approval_status VARCHAR(20) DEFAULT 'pending'"))
            
        if 'approval_date' not in columns:
            print("Adding approval_date column to order_file table...")
            conn.execute(text("ALTER TABLE order_file ADD COLUMN approval_date TIMESTAMP"))
            
        if 'approval_comment' not in columns:
            print("Adding approval_comment column to order_file table...")
            conn.execute(text("ALTER TABLE order_file ADD COLUMN approval_comment TEXT"))
            
        if 'proof_sent_at' not in columns:
            print("Adding proof_sent_at column to order_file table...")
            conn.execute(text("ALTER TABLE order_file ADD COLUMN proof_sent_at TIMESTAMP"))

        print("Migration completed successfully.")
        conn.close()

if __name__ == "__main__":
    migrate_proof_approval_fields()