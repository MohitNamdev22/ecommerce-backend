from app.core.database import Base, engine
from app.auth.models import User  # Import models

# Add this to env.py
target_metadata = Base.metadata
connectable = engine