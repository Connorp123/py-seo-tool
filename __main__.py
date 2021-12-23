# For crawling
from bs4 import BeautifulSoup
import requests
import re
from time import *
from random import randint

# For output
from pprint import pp

# For Firebase
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from datetime import datetime

# Constants
MAX_DEPTH = 5
MAX_WAIT_TIME = 0
BASE_URL = 'https://connorpeace.com'
VALID_URL_REGEX = re.compile('(.*connorpeace\.com.*)|(.*\.html)')


def wait():
    x = randint(0, MAX_WAIT_TIME)
    sleep(x)


def bfs(start_url, visited, must_fix):
    # Set up regex
    http_regex = re.compile('http.*')

    # Add the root
    fringe = [(start_url, 0,
               'base_url')]  # FIFO Queue (url, depth) - pop, visit, continue

    # Loop through fringe
    while len(fringe) > 0:

        # Remove next vertex
        current = fringe.pop()

        # Visit the vertex
        if not current[0] in visited and current[1] <= MAX_DEPTH:

            wait()

            # Get the bsoup object
            req = requests.get(current[0])
            response_code = int(req.status_code)

            # Mark vertex as visited
            visited[current[0]] = response_code
            print("Visiting:", current[0], response_code)

            # Check 5xx
            if response_code >= 500:
                must_fix['5xx'].append((current[0], current[2]))

            # Check 4xx
            elif response_code >= 400:
                must_fix['4xx'].append((current[0], current[2]))

            # Check 302
            elif response_code == 302:
                must_fix['302'].append((current[0], current[2]))

            # Check if this is related to the child URL
            elif response_code == 200 and VALID_URL_REGEX.match(current[0]):

                # Parse the page
                soup = BeautifulSoup(req.text, "html.parser")

                # Check page_title_missing
                if not soup.title:
                    must_fix['page_title_missing'].append(current[0])

                # Check h1_missing
                if not soup.h1:
                    must_fix['h1_missing'].append(current[0])

                # Check h1_multiple
                h1s = soup.find_all('h1')
                if len(h1s) > 1:
                    must_fix['h1_multiple'].append(current[0])

                # Check canonical_missing
                canonicals = soup.find_all(rel='canonical')
                if len(canonicals) != 1:
                    must_fix['canonical_missing'].append(current[0])

                # Add all found links to fringe
                all_links = soup.find_all('a')
                for a in all_links:
                    href = a['href']

                    # Fix URL if needed
                    if not http_regex.match(href):
                        href = BASE_URL + '/' + href

                    fringe.append((href, current[1] + 1, current[0]))

            else:
                print("Invalid response code:", response_code)


if __name__ == '__main__':
    # Initialize all variables
    must_fix = {
        '5xx': [],
        '4xx': [],
        '302': [],
        'page_title_missing': [],
        'h1_missing': [],
        'h1_multiple': [],
        'canonical_missing': []
    }
    visited = {}
    only_crawl_regex = r'.*connorpeace\.com.*'

    ############################################################################
    # Set up firebase
    #   https://www.freecodecamp.org/news/how-to-get-started-with-firebase-using-python/
    ############################################################################
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
    time_string = datetime.now().strftime("%Y-%m-%d_%H-%M")
    ref = db.reference(f'/{time_string}',
                       url="https://seo-tool-cp-default-rtdb.firebaseio.com/")

    ############################################################################
    # Crawl the site
    ############################################################################
    bfs(BASE_URL, visited, must_fix)

    ############################################################################
    # Output the results
    ############################################################################
    print("Printing visited:")
    pp(visited)
    print()

    print("Printing must_fix:")
    pp(must_fix)
    print()

    ############################################################################
    # Save the results to Firebase
    ############################################################################
    must_fix['stats'] = {
        '5xx': len(must_fix['5xx']),
        '4xx': len(must_fix['4xx']),
        '302': len(must_fix['302']),
        'page_title_missing': len(must_fix['page_title_missing']),
        'h1_missing': len(must_fix['h1_missing']),
        'h1_multiple': len(must_fix['h1_multiple']),
        'canonical_missing': len(must_fix['canonical_missing'])
    }

    fire_object = {
        'visited': list(visited.items()),
        'must_fix': must_fix,
    }

    ref.set(fire_object)
    print("Saved visited to firebase.")

    # ref_must_fix.set(must_fix)
    # print("Saved must_fix to firebase.")
