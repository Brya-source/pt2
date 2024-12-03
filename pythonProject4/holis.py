import snscrape.modules.twitter as sntwitter

query = "secuestro lang:es"
tweets = []

for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
    if i > 100:
        break
    print(tweet.content)

