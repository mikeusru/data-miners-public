from utils import get_api, MyTweetCursor, connect_dataset
import tweepy


keywords = ["AAPL", "IPHONE", "MSFT", "APPLE", "MICROSOFT", "IPAD", "IPOD", "MACBOOK", "SURFACE PRO", "AIRPODS"]

api = get_api()
db = connect_dataset()
tweet_cursor = MyTweetCursor(api, keywords, db)
tweet_cursor.scrape_tweets()
