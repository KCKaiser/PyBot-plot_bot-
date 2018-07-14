
# coding: utf-8

# In[1]:


# Import dependencies
import os
import tweepy
import pandas as pd
import json
import time
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib import style

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
analyzer = SentimentIntensityAnalyzer()


# In[2]:


try:
    from config import consumer_key, consumer_secret, access_token, access_token_secret

except:
    consumer_key = os.environ['CONSUMER_KEY']
    consumer_secret = os.environ['CONSUMER_SECRET']
    access_token = os.environ['ACCESS_TOKEN']
    access_token_secret = os.environ['ACCESS_TOKEN_SECRET']


# In[3]:


# Tweepy API Authentication
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, parser=tweepy.parsers.JSONParser())


# In[4]:


def createplot(sentiments_df, target_user):
    style.use('ggplot')
    plt.figure(figsize=(8, 5))
    x_vals = sentiments_df["Tweets Ago"]
    y_vals = sentiments_df["Compound"]
    sentiment_plt, = plt.plot(sentiments_df["Tweets Ago"], sentiments_df["Compound"], marker = "o", linewidth = 0.5, 
                          color = "royalblue", alpha = 0.8)
    now = datetime.now()
    now = now.strftime("%Y-%m-%d %H:%M")
    plt.title(f"Sentiment Analysis of Tweets ({now}) for {target_user}")
    plt.xlim([x_vals.max(),x_vals.min()]) 
    plt.ylabel("Tweet Polarity")
    plt.xlabel("Tweets Ago")
    plt.xticks(size = 9)
    plt.yticks(size = 9)
    plt.xlim(min(sentiments_df["Tweets Ago"]) - 2, 2) 
    lgd = plt.legend([sentiment_plt], [target_user], loc = "right", bbox_to_anchor=(1.31, 0.9))

    plt.savefig(f'output_images/{target_user[1:]}.png', bbox_extra_artists=(lgd,), bbox_inches='tight')


# In[5]:


def tweetout(target_user, person_to_thank):
    api.update_with_media(f'output_images/{target_user[1:]}.png',
                          f'New Tweet Analysis: {target_user} (Thanks @{person_to_thank}!)')


# In[6]:


tweet_ids = []
analysis_targets = []

# Searching for mentions
target_term = "@plot_bot"


def plotbot():
    
    # Searching for mentions
    public_tweets = api.search(target_term, count=100, result_type="recent")
    
    # For every tweet from our search...
    for tweet in public_tweets["statuses"]:

        tweet_id = tweet["id"]
        
        # Find unique tweets that were not previously used
        if tweet_id not in tweet_ids:
            
            # Append the tweet id for this tweet to a list
            tweet_ids.append(tweet_id)
            
            # Pull out the name of the user who tweeted @plot_bot
            person_to_thank = tweet["user"]["screen_name"]
            
            # Pull out the username of the user we're analyzing from the tweet itself
            tweet_text = tweet["text"]
            tweet_index = tweet_text.find(target_term)
            tweet_space = tweet_text.find("@", tweet_index + 1)
            
            
            # Do so if only if the tweet has the word "analyze" and has a second username mention
            if not tweet_text.find("Analyze")== -1 or not tweet_text.find("analyze")== -1:
                if not tweet_space == -1:
                    # Making sure the code still works regardless if there is space after the second username
                    if not tweet_text[tweet_space: ].find(" ")== -1:
                        tweet_short = tweet_text[tweet_space:]
                        index_space = tweet_text[tweet_space: ].find(" ")
                        target_user = tweet_short[:index_space]
            
                    else:
                        target_user = tweet_text[tweet_space: ]
            
                    # For every tweet from our search that are unique and the target has not been analyzed before
                    #(And the tweet uses the word analyze and mentions a second username)
                    if target_user not in analysis_targets:
                        analysis_targets.append(target_user)

                        oldest_tweet = None
                        sentiments = []
                        twitter_ids = []
                        counter = -1

                        # For every tweet from our search that are unique and the target has not been analyzed before,
                        # Flip through 25 pages for 500 tweets from the target
                        for x in range(25):
                            user_tweets = api.user_timeline(target_user, max_id = oldest_tweet)

                            # For every page for the new target from every unique tweet from our search...
                            for user_tweet in user_tweets:

                                twitter_id = user_tweet["id"]

                                # Make sure we're not pulling duplicate tweets
                                if twitter_id not in twitter_ids:

                                    twitter_ids.append(twitter_id)

                                    user_text = user_tweet["text"]

                                    results = analyzer.polarity_scores(user_text)

                                    oldest_tweet = user_tweet['id'] - 1

                                    sentiment_dictionary = {"Date": tweet["created_at"],
                                                            "Compound" : results["compound"],
                                                            "Positive" : results["pos"],
                                                            "Negative" : results["neg"],
                                                            "Neutral" : results["neu"],
                                                            "Tweets Ago" : counter}              

                                    sentiments.append(sentiment_dictionary)
                                    counter -= 1

                                sentiments_df = pd.DataFrame(sentiments)

                        createplot(sentiments_df, target_user)
                        #tweetout(target_user, person_to_thank)


# In[ ]:


while(True):
    plotbot()
    time.sleep(300)

