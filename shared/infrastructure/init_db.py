from sqlalchemy.orm import Session
from shared.infrastructure.database import engine, SessionLocal, Base
from shared.infrastructure.models import Material, Country

def init_db():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()

def seed_data(db: Session):
    # Seed Materials
    materials_data = [
        ('Copper', 'Shielding'), ('Aluminum', 'Shielding'), ('PVC', 'Polymer'), ('XLPE', 'Polymer'),
        ('PE', 'Polymer'), ('LSF', 'Polymer'), ('GSW', 'Shielding'), ('GST', 'Shielding'), ('Copper Tape', 'Shielding'),
        ('Aluminum Tape', 'Shielding'), ('Mica Tape', 'Screening'), ('Water-blocking', 'Screening')
    ]
    
    for name, category in materials_data:
        if not db.query(Material).filter(Material.name == name).first():
            db.add(Material(name=name, category=category))
    
    # Seed Countries
    countries_data = [
        # MENA
        ('Egypt', '818'), ('UAE', '784'), ('Saudi Arabia', '682'),
        # APAC
        ('China', '156'), ('India', '356'), ('Japan', '392'), ('S.Korea', '410'), ('Australia', '36'),
        # EU
        ('Germany', '276'), ('Italy', '380'), ('France', '251'), ('Spain', '724'), ('UK', '826'),
        # NA
        ('USA', '842'), ('Canada', '124'),
        # LATAM
        ('Brazil', '76'), ('Mexico', '484'), ('Argentina', '32'),
        # SSA
        ('South Africa', '710'), ('Nigeria', '566'), ('Kenya', '404')
    ]

    for name, code in countries_data:
        if not db.query(Country).filter(Country.name == name).first():
            db.add(Country(name=name, code=code))

    db.commit()

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialization complete.")
