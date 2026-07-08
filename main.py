from knowledge_viewer.viewer import KnowledgeViewer
from research_database.database_initializer import DatabaseInitializer
from research_database.database_manager import DatabaseManager
from research_database.repositories.company_repository import CompanyRepository
from research_database.sample_data_seeder import SampleDataSeeder


def main() -> None:
    manager = DatabaseManager()
    manager.connect()
    DatabaseInitializer(manager).initialize()
    SampleDataSeeder(manager).seed()

    company_repository = CompanyRepository(manager)

    try:
        KnowledgeViewer(company_repository).run()
    finally:
        manager.close()


if __name__ == "__main__":
    main()
