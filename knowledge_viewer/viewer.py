"""
Knowledge Viewer

Interactive CLI for browsing the research database: searching companies,
viewing database statistics, and checking database health.
"""

from research_database.database_manager import DatabaseManager

MENU_TEXT = """
Knowledge Viewer
================
1. Search Company
2. Database Statistics
3. Database Health
4. Exit
"""


class KnowledgeViewer:
    """Runs the Knowledge Viewer menu loop against the database."""

    def __init__(self, db_manager: DatabaseManager | None = None) -> None:
        self.db_manager = db_manager or DatabaseManager()

    def run(self) -> None:
        """Start the database and run the interactive menu until exit."""
        self.db_manager.connect()
        self.db_manager.initialize()

        try:
            while True:
                print(MENU_TEXT)
                choice = input("Select an option (1-4): ").strip()

                if choice == "1":
                    self._search_company()
                elif choice == "2":
                    self._show_statistics()
                elif choice == "3":
                    self._show_health()
                elif choice == "4":
                    print("Goodbye.")
                    break
                else:
                    print("Invalid option. Please choose 1-4.")
        finally:
            self.db_manager.close()

    def _search_company(self) -> None:
        name = input("Enter company name to search: ").strip()

        if not name:
            print("Please enter a company name.")
            return

        company = self.db_manager.search_company(name)

        if company is None:
            print("Company not found.")
            return

        print("\nCompany Found")
        print("-------------")
        print(f"Company Name: {company['name']}")
        print(f"Sector:       {company['sector'] or 'Unknown'}")
        print(f"Industry:     {company['industry'] or 'Unknown'}")
        print(f"Market Cap:   {company['market_cap'] or 'Unknown'}")
        print(f"Country:      {company['country'] or 'Unknown'}")
        print(f"Exchange:     {company['exchange'] or 'Unknown'}")
        print(f"Last Updated: {company['last_updated']}")

    def _show_statistics(self) -> None:
        stats = self.db_manager.get_statistics()

        print("\nDatabase Statistics")
        print("-------------------")
        print(f"Total Companies:  {stats['total_companies']}")
        print(f"Total Sectors:    {stats['total_sectors']}")
        print(f"Database Version: {stats['database_version']}")

    def _show_health(self) -> None:
        health = self.db_manager.health_check()
        file_size_kb = health["file_size_bytes"] / 1024

        print("\nDatabase Health")
        print("---------------")
        print(f"Database Connected: {health['connected']}")
        print(f"Schema Loaded:      {health['schema_loaded']}")
        print(f"Database Size:      {file_size_kb:.2f} KB")
