import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm

class StudySearch:

    def __init__(self, query=""):
        if query != "":
            self.query = '+'.join(query.split(" "))
        else:
            self.query = ""
        self.results_num = ""
    
    
    def search_to_df(self) -> pd.DataFrame:
        """
        Takes self.query attribute from initialization and performs
        a search to determine the number of results that stem from
        the keyword.

        Will prompt the user to enter a new phrase if no results are found
        """
        while True:
            if self.query == "":
                self.query = '+'.join(input("Enter desired topic: ").split(" "))
            URL = f"https://pubmed.ncbi.nlm.nih.gov/?term={self.query}&size=200&filter=simsearch1.fha"
            page = requests.get(URL)
            page_data = BeautifulSoup(page.content, "html.parser")

            try:
                results = page_data.find("span", class_="value").text
            except:
                print("\nNo studies found matching your keywords.\n")
                self.query = ""
                continue
            if "," in results:
                results = results.replace(",","")
            maxnum = int(results)
            break

        """
        Loop to establish desired number of results from pulled data
        """
        while True:
            self.results_num = input(f"\n{results} results found, sorted by relevancy. Enter how many you would like to compile (1-{maxnum}): ")
            if int(self.results_num) > int(maxnum):
                print("Too high! Please select a number within the given range.")
                continue
            elif int(self.results_num) == 0:
                print("Must at least select 1 result!")
                continue
            else:
                break

        if int(self.results_num) <= 200:
            page_count = 0
        else:
            page_count = (int(self.results_num)//200 + 1)
        if page_count > 1:
            print(f"\nParsing through {page_count} pages of data...")
            studies_list = []
            remaining_count = int(self.results_num)

            """
            For loop to iterate through each page of data
            Uses data_parser function written below
            """
            for i in range(1, page_count+1):
                print(f"Page {i} of {page_count}")
                URL = f"https://pubmed.ncbi.nlm.nih.gov/?term={self.query}&size=200&filter=simsearch1.fha&page={i}"
                page = requests.get(URL)
                page_data = BeautifulSoup(page.content, "html.parser")
                if remaining_count < 200:
                    search_results = page_data.find_all("article", class_="full-docsum", limit=remaining_count)
                else:
                    search_results = page_data.find_all("article", class_="full-docsum")
                studies_list += self.data_parser(search_results)
                remaining_count -= 200
                print(f"Page {i} of {page_count} complete.\n")
        else:
            search_results = page_data.find_all("article", class_="full-docsum", limit=int(self.results_num))
            studies_list = self.data_parser(search_results)
        print("Done!\n")
        return pd.DataFrame(data=studies_list)


    def data_parser(self, search_results) -> list:
        """
        Function to iterate through the search results and collect data
        """
        studies = []
        for study_data in tqdm(search_results, desc ="Compiling Data"):
            study_title = study_data.find("a", class_="docsum-title").text.strip()
            study_id = study_data.find("a", class_="docsum-title")
            study_authors = study_data.find("div", class_="docsum-citation full-citation").find("span").text.strip()
            study_URL = f"https://pubmed.ncbi.nlm.nih.gov{study_id['href']}"
            study_page = BeautifulSoup(requests.get(study_URL).content, "html.parser")
            study_abstract = study_page.find("div", class_="abstract-content selected").find_all("p")
            abstract_text = ''

            """
            For loop in the event that a given study's abstract has multiple sections
            """
            for section in study_abstract:
                abstract_text += section.text.strip() + "\n"

            study_journal = study_page.find("div", class_="article-source").find("button").text.strip()
            study_citation = study_page.find("div", class_="article-source").find("span", class_="cit").text
            citation = f"{study_journal}; {study_citation}"
            studies.append({"Title": study_title, "Authors": study_authors, 
                            "Abstract": abstract_text, "Citation": citation, 
                            "URL": study_URL, })  
        return studies
    
    
    def study_exporter(self, final_results):
        """
        Function which takes the DataFrame supplied earlier and prints out a preview
        Additionally exports to a .csv if desired
        """
        print(final_results)
        while True:
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

#Driver Code
new_study = StudySearch()
final_results = new_study.search_to_df()
new_study.study_exporter(final_results)
