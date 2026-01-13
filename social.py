# social.py
import tweepy
import os


# Load Twitter API credentials from environment variables
BEARER_TOKEN = os.getenv("AAAAAAAAAAAAAAAAAAAAAH9%2F4gEAAAAAJSML6XltRftkLxW6qNNHgo30fVY%3DC5HuqmU0tmsx5y4v26YOyiimSl31AXs8F6QsWYV7ACV6AZyKsp")
API_KEY = os.getenv("RAfWFdoEa0xe4BlKAbtZRWxSA")
API_SECRET = os.getenv("VODTdp2VWdEQLVkz4P5MBfpNIjG0Bp7x4N9Lg36BiUXcuGdCK4")
ACCESS_TOKEN = os.getenv("412373520-YnUUf3tljKqNIJDY8idvIDPLUsYoZs9E2sOKql8T")
ACCESS_TOKEN_SECRET = os.getenv("ehwjR4nrYVlAxojiXCp003yNLYdWRGIyCevm000Vis1zi")

def run_twitter_search(keyword, limit=20):
    import time
    if not BEARER_TOKEN:
        print("Twitter API bearer token not set. Set TWITTER_BEARER_TOKEN in your environment.")
        return []
    client = tweepy.Client(bearer_token=BEARER_TOKEN, wait_on_rate_limit=True)
    try:
        tweets = client.search_recent_tweets(query=keyword, max_results=limit, tweet_fields=["author_id", "created_at"])
        # Rate limit handling
        if hasattr(tweets, 'meta') and 'x-rate-limit-remaining' in tweets.meta:
            remaining = int(tweets.meta['x-rate-limit-remaining'])
            reset = int(tweets.meta.get('x-rate-limit-reset', 0))
            if remaining == 0:
                sleep_time = max(0, reset - int(time.time()))
                print(f"Rate limit reached. Sleeping for {sleep_time} seconds.")
                time.sleep(sleep_time)
        results = []
        if tweets.data:
            for tweet in tweets.data:
                results.append({
                    "user": tweet.author_id,
                    "content": tweet.text,
                    "url": f"https://twitter.com/i/web/status/{tweet.id}",
                    "date": tweet.created_at
                })
        return results
    except tweepy.TooManyRequests as e:
        # Tweepy will raise this if rate limit is hit and wait_on_rate_limit=False
        print("Twitter API rate limit exceeded. Waiting before retry...")
        reset_time = int(e.response.headers.get('x-rate-limit-reset', 0))
        sleep_time = max(0, reset_time - int(time.time()))
        time.sleep(sleep_time)
        return run_twitter_search(keyword, limit)
    except Exception as e:
        print(f"Twitter API error: {e}")
        return []
