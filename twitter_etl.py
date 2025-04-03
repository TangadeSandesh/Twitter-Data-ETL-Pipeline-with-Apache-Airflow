import tweepy
import pandas as pd
import json
import os
from dotenv import load_dotenv
from airflow.providers.amazon.aws.hooks.s3 import S3Hook  # Import S3Hook

# Load environment variables from .env file
load_dotenv()

# Get Bearer Token from .env
BEARER_TOKEN = os.getenv("BEARER_TOKEN")

def run_twitter_etl():
    client = tweepy.Client(bearer_token=BEARER_TOKEN)

    try:
        user = client.get_user(username="elonmusk")  # Get User ID
        user_id = user.data.id
        print(f"User ID: {user_id}")

        # Fetch latest tweets with additional fields
        tweets = client.get_users_tweets(
            id=user_id, 
            max_results=10, 
            tweet_fields=["created_at", "public_metrics"]
        )
        print(f"Tweets Data: {tweets.data}") 
        tweet_list = []
        
        if tweets.data:
            for tweet in tweets.data:
                tweet_data = {
                    "id": tweet.id,
                    "text": tweet.text,
                    "created_at": tweet.created_at.isoformat(),  # Convert datetime to string
                    "like_count": tweet.public_metrics["like_count"],
                    "retweet_count": tweet.public_metrics["retweet_count"]
                }
                tweet_list.append(tweet_data)

            # Convert list to DataFrame
            df = pd.DataFrame(tweet_list)

            # Save DataFrame to a local CSV file
            local_file_path = "/elon_twitter_data.csv"
            df.to_csv(local_file_path, index=False, encoding="utf-8")
            print(f"Data saved locally to {local_file_path}")

            # Upload the file to S3
            s3_hook = S3Hook(aws_conn_id="aws_default")  # Ensure "aws_default" connection exists in Airflow
            s3_hook.load_file(
                filename=local_file_path,
                key="elon_twitter_data.csv",  # S3 key (path)
                bucket_name="sandesh-twitter-bucket",  # Your S3 bucket name
                replace=True  # Overwrite if file exists
            )
            print("Data uploaded to S3 successfully.")

        else:
            print("No tweets found.")

    except tweepy.TweepyException as e:
        print(f"Error: {e}")