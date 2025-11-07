from database import init_db, SessionLocal
from db_models import ProviderDB, AppointmentDB


def seed_providers():
    """Seed initial provider data"""
    db = SessionLocal()
    try:
        # Check if providers already exist
        if db.query(ProviderDB).count() > 0:
            print("Providers already seeded. Skipping...")
            return

        providers = [
            ProviderDB(
                id="provider-1",
                name="Dr. Sarah Chen",
                specialty="Family Medicine",
                bio="Dr. Chen has over 15 years of experience in family medicine and preventive care."
            ),
            ProviderDB(
                id="provider-2",
                name="Dr. James Kumar",
                specialty="Internal Medicine",
                bio="Dr. Kumar specializes in internal medicine with a focus on chronic disease management."
            )
        ]

        for provider in providers:
            db.add(provider)

        db.commit()
        print("Providers seeded successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding providers: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database tables created!")

    print("Seeding providers...")
    seed_providers()
    print("Database initialization complete!")
