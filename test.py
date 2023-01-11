import requests

if __name__ == '__main__':
    url = "https://streaming-availability.p.rapidapi.com/search/basic"

    querystring = {"country":"us","service":"netflix","type":"movie","output_language":"en","language":"en"}

    headers = {
        'x-rapidapi-host': "streaming-availability.p.rapidapi.com",
        'x-rapidapi-key': "37abd91e7dmsh205104ce6e42bc3p13a5f2jsn15a6f607cedb"
        }

    response = requests.request("GET", url, headers=headers, params=querystring)

    print(response.text)