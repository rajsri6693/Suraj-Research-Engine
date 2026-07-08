"""
Knowledge Viewer

Interactive CLI for browsing the research database: searching companies,
listing companies, viewing database statistics, and checking database
health. Talks exclusively to the Company Repository — it never accesses
the Database Manager or SQLite directly.
"""

from research_database.repositories.company_repository import CompanyRepository
from research_database.schema.company import Company

MENU_TEXT = """
Knowledge Viewer
================
1. Search Company
2. List Companies
3. Database Statistics
4. Database Health
5. Exit
"""


class KnowledgeViewer:
    """Runs the Knowledge Viewer menu loop against the Company Repository."""

    def __init__(self, company_repository: CompanyRepository) -> None:
        self.company_repository = company_repository

    def run(self) -> None:
        """Run the interactive menu until exit."""
        while True:
            print(MENU_TEXT)
            choice = input("Select an option (1-5): ").strip()

            if choice == "1":
                self._search_company()
            elif choice == "2":
                self._list_companies()
            elif choice == "3":
                self._show_statistics()
            elif choice == "4":
                self._show_health()
            elif choice == "5":
                print("Goodbye.")
                break
            else:
                print("Invalid option. Please choose 1-5.")

    def _search_company(self) -> None:
        term = input("Enter company name, symbol, or exchange to search: ").strip()

        if not term:
            print("Please enter a search term.")
            return

        results = self.company_repository.search(term)

        if not results:
            print("Company not found.")
            return

        for company in results:
            self._print_company(company)

    def _list_companies(self) -> None:
        companies = self.company_repository.list_all()

        if not companies:
            print("No companies found.")
            return

        print("\nCompanies")
        print("---------")
        for company in companies:
            print(f"{company.common_name} ({company.legal_name})")

    def _print_company(self, company: Company) -> None:
        print("\nCompany Found")
        print("-------------")
        print(f"Legal Name:   {company.legal_name}")
        print(f"Common Name:  {company.common_name or 'Unknown'}")
        print(f"Industry:     {company.industry or 'Unknown'}")
        print(f"Country:      {company.incorporation_country or 'Unknown'}")
        print(f"Headquarters: {company.headquarters_location or 'Unknown'}")
        print(f"Exchanges:    {', '.join(company.stock_exchanges) or 'Unknown'}")
        print(f"Tickers:      {', '.join(company.ticker_symbols) or 'Unknown'}")

    def _show_statistics(self) -> None:
        stats = self.company_repository.statistics()

        print("\nDatabase Statistics")
        print("-------------------")
        print(f"Total Companies:  {stats['total_companies']}")
        print(f"Total Sectors:    {stats['total_sectors']}")
        print(f"Database Version: {stats['database_version']}")

    def _show_health(self) -> None:
        print("\nDatabase Health")
        print("---------------")

        try:
            stats = self.company_repository.statistics()
        except Exception:
            print("Database Connected: False")
            return

        print("Database Connected: True")
        print(f"Total Companies:    {stats['total_companies']}")
        print(f"Database Version:   {stats['database_version']}")
