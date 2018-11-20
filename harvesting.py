import praw
import json

tokenfile = open('tokens.json', 'r')
tokens = json.load(tokenfile)

print(tokens)


reddit = praw.Reddit(client_id=tokens['client_id'],
                     client_secret=tokens['client_secret'],
                     username=tokens['username'],
                     password=tokens['password'],
                     user_agent=tokens['user_agent'])


for submission in reddit.subreddit('askreddit').hot(limit=100):
    print(submission.title)
