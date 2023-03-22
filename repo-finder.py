from re import search
from dotenv import dotenv_values

import requests

from model.repository import Repository

config = {
    **dotenv_values(".env.shared"),  # load shared development variables
    **dotenv_values(".env.secret"),  # load sensitive variables
    # **os.environ,  # override loaded values with environment variables
}

# IBM GHE or public GH
GHE = config.get("USE_GHE")

if GHE:
    PAT = config.get("IBM_PAT")
    GH_URL = config.get("IBM_GH")
    GH_API = config.get("IBM_API")
else:
    PAT = config.get("PAT")
    GH_URL = config.get("GH")
    GH_API = config.get("GH_API")

STARS = "stargazers_count"
LAST_UPDATED = "pushed_at"

QUERY = config.get("QUERY")

class RepoFinder():

    def __init__(self):
        self.repos = []
        self.query = QUERY
        self.per_page = 100 # Number of results per page

    def set_query(self, query: str) -> None:
        # Define your search query parameters
        # Multiple tags can be searched like topic:tag+topic:tag
        # Note this performs an AND search
        # Can also search for title with in:title title
        self.query = query

    def get_query(self) -> str:
        return self.query

    def get_per_page(self) -> str:
        return self.per_page

    def get_repos(self) -> list:
        return self.repos

    def set_repos(self, repos) -> None:
        self.repos = repos

    def search_gh(self) -> requests.Response:
        # Make a request to the GitHub search API
        if GHE:
            headers = {
                "Authorization": f"Token {PAT}",
                "Accept": "application/vnd.github+json"
            }

            search_url = f'https://api.github.ibm.com/search/repositories?q={self.query}&per_page={self.per_page}'
            return requests.get(search_url, headers=headers)
        else:
            return requests.get(f'https://api.github.ibm.com/search/repositories?q={self.query}&per_page={self.per_page}')

    def retrieve_repos(self, response):
        # Parse the JSON response
        results = response.json()['items']

        repos_file = open("repos.txt", 'w')
        repos = self.get_repos()
        # Print the name and URL of each repository
        for result in results:
            repo = Repository(result['html_url'])
            repo.fetchRepoData(PAT, GH_URL, GH_API)
            repos.append(repo)
            repos_file.write("[%s](%s) \n" % (
                repo.data['repo_path'],
                repo.data['html_url'],
            ))
    #        print(f"{result['full_name']}: {result['html_url']}")
        repos_file.close()
        self.set_repos(repos)

    def populate_repo_info(self):
        out_file = open("repos.md", 'w')

        out_file.write("Name | Description | Last Updated | Stars \n")
        out_file.write("--- | --- | --- | --- \n")

        for repo in repo_finder.get_repos():
            description = repo.data['description']
            if description is not None:
                description = description.replace("|", "\|")
            out_file.write("[%s](%s) | %s | %s | %s \n" % (
                repo.data['repo_path'],
                repo.data['html_url'],
                description,
                repo.data['pushed_at'][0:len('2020-01-01')],
                repo.data['stargazers_count']
            ))
        out_file.close()

    def sort_repos(self, repos, sort_by) -> Repository:
        return sorted(
                repos,
                key=lambda repo: repo.data[sort_by],
                reverse=True)

    def sort_by_stars(self, repos=None) -> Repository:
        if not repos:
            repos = self.get_repos()
        sorted_repos = self.sort_repos(repos, STARS)
        self.set_repos(sorted_repos)

    def sort_by_updated(self, repos=None) -> Repository:
        if not repos:
            repos = self.get_repos()
        sorted_repos = self.sort_repos(repos, LAST_UPDATED)
        self.set_repos(sorted_repos)

if __name__ == "__main__":
    repo_finder = RepoFinder()

    response = repo_finder.search_gh()

    # Check if the request was successful
    if response.status_code == 200:
        repo_finder.retrieve_repos(response)
    else:
        print(f"Request failed with status code {response.status_code}")

    repo_finder.sort_by_updated()

    repo_finder.populate_repo_info()