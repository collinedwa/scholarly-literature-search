import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm


class StudySearch:

    def __init__(self, query="", num=0, export_input=True):
        """
        Attributes for search keyword, results number, and automatic export of data
        Leave blank for interactive input

        Parameters

        query: str. Desired keyword for search
        num: int. Desired number of results to include in table
        export_input: bool. If True, asks for user input to export. otherwise automatically exports data to .csv
        """

        self.query = '+'.join(query.split(" ")) if query != "" else ""
        self.results_num = num if num != 0 else ""
        self.export_input = export_input

    def search_to_df(self) -> pd.DataFrame:
        """
        Takes self.query attribute from initialization and performs
        a search to determine the number of results that stem from
        the keyword.

        Will prompt the user to enter a new phrase if no results are found
        """
        URL = f"https://pubmed.ncbi.nlm.nih.gov/?term={self.query}&size=200&filter=simsearch1.fha"
        page = requests.get(URL)
        page_data = BeautifulSoup(page.content, "lxml")

        try:
            results = page_data.find("span", class_="value").text
        except:
            print("\nNo studies found matching your keywords.\n")
            return pd.DataFrame()
        if "," in results:
            results = results.replace(",", "")
        maxnum = int(results)


        """
        Loop to establish desired number of results from pulled data
        """

        if self.results_num != "" and self.results_num > maxnum:
            print(f"Desired results exceeds retrieved results count.\nAdjusting to results count to {maxnum}")
            self.results_num = maxnum

        if self.results_num <= 200:
            page_count = 0
        else:
            page_count = (self.results_num//200)
            page_count += 1 if (self.results_num % 200) > 0 else 0
        if page_count > 1:
            print(f"\nParsing through {page_count} pages of data...")
            studies_list = []
            remaining_count = self.results_num

            """
            For loop to iterate through each page of data
            Uses data_parser function written below
            """
            for i in range(1, page_count+1):
                print(f"Page {i} of {page_count}")
                URL = f"https://pubmed.ncbi.nlm.nih.gov/?term={self.query}&size=200&filter=simsearch1.fha&page={i}"
                page = requests.get(URL)
                page_data = BeautifulSoup(page.content, "lxml")
                if remaining_count < 200:
                    search_results = page_data.find_all("article", class_="full-docsum", limit=remaining_count)
                else:
                    search_results = page_data.find_all("article", class_="full-docsum")
                studies_list += self.data_parser(search_results)
                remaining_count -= 200
                print(f"Page {i} of {page_count} complete.\n")
        else:
            search_results = page_data.find_all("article", class_="full-docsum", limit=self.results_num)
            studies_list = self.data_parser(search_results)
        print("Done!\n")
        return pd.DataFrame(data=studies_list)

    def data_parser(self, search_results) -> list:
        """
        Function to iterate through the search results and collect data
        """
        studies = []
        for study_data in tqdm(search_results, desc="Compiling Data"):
            studies.append(self.single_parse(study_data))
        return studies

    def single_parse(self, search_result):
        study_title = search_result.find("a", class_="docsum-title").text.strip()
        study_id = search_result.find("a", class_="docsum-title")
        study_authors = search_result.find("div", class_="docsum-citation full-citation").find("span", class_="docsum-authors full-authors").text.strip()
        study_URL = f"https://pubmed.ncbi.nlm.nih.gov{study_id['href']}"
        study_page = BeautifulSoup(requests.get(study_URL).content, "lxml")
        study_abstract = study_page.find("div", class_="abstract").find_all("p")
        abstract_text = ''

        """
        For loop in the event that a given study's abstract has multiple sections
        """
        for section in study_abstract:
            abstract_text += section.text.strip() + ' '
        study_citation = search_result.find("div", class_="docsum-citation full-citation").find("span", class_="docsum-journal-citation full-journal-citation").text.strip()
        return {"Title": study_title, "Authors": study_authors,
                        "Abstract": abstract_text, "Citation": study_citation,
                        "URL": study_URL}     

    def study_exporter(self, final_results):
        """
        Function which takes the DataFrame supplied earlier and prints out a preview
        Additionally exports to a .csv if desired
        """
        print(final_results)
        if self.export_input is False:
            file_name = self.query.replace("+", "_") + f"_{self.results_num}"
            final_results.to_csv(f"static/{file_name}.csv")
            print("Done!")
        while self.export_input:
            export_choice = input("Export to .csv? (y/n): ")
            if export_choice.lower() == 'y':
                file_name = self.query.replace("+", "_") + f"_{self.results_num}"
                final_results.to_csv(f"{file_name}.csv")
                print("Done!")
                break
            elif export_choice.lower() == 'n':
                break
            else:
                print("Invalid response!\n")
                continue
        return file_name


# Driver code for automated output
# new_study = StudySearch(query="bench press", num=100, export_input=False)
# final_results = new_study.search_to_df()
# new_study.study_exporter(final_results)

# Driver code for interactive, user directed output
#new_study = StudySearch()
#final_results = new_study.search_to_df()
#new_study.study_exporter(final_results)
