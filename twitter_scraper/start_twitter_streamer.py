from utils import MyStreamListener, get_api
import tweepy


keywords = ["AAPL", "IPHONE", "MSFT", "APPLE", "MICROSOFT", "IPAD", "IPOD", "MACBOOK", "SURFACE PRO", "AIRPODS"]

stream_listener = MyStreamListener(keywords)
api = get_api()
stream = tweepy.Stream(auth=api.auth, listener=stream_listener)
stream.filter(track=keywords)
