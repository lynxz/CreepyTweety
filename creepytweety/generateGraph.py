'''
Created on Jan 4, 2013

@author: lynxz
'''

from TweetClient import TweetClient
import networkx as nx
import matplotlib.pyplot as plt
import operator

def get_tweets(user, tweets):
    client = TweetClient()
    client.setup()
    try:
        return client.fetch_user_tweets(user, tweets)
    except IOError as e:
        print 'Caught IOError %s' % e.strerror
        return []

def get_user_info(tweet):
    user_data = {'name': tweet['user']['name'],
                 'screen_name': tweet['user']['screen_name'],
                 'id': tweet['user']['id'],
                 'profile_image': tweet['user']['profile_image_url'],
                 'location': tweet['user']['location']}
    
    if tweet['user']['url'] != None:
        if tweet['user']['entities']['url']['urls'][0]['expanded_url'] != None:
            user_data['url'] = tweet['user']['entities']['url']['urls'][0]['expanded_url']
        else:
            user_data['url'] = tweet['user']['url']
        
    return user_data

def get_tweet_data(tweet):
    tweet_data = {'message' : tweet['text'],
                  'id': tweet['id'],
                  'user_mentions': tweet['entities']['user_mentions'],
                  'hashtags': tweet['entities']['hashtags']
                }

    return tweet_data

def print_statistics(stat_dict):
    print '** Statistics **'
    print ''
        
    norm_value = 1.0
        
    if len(stat_dict) > 0:
        print "%d entries used" % len(stat_dict)
        sorted_entries = sorted(stat_dict.iteritems(), key = operator.itemgetter(1), reverse = True)
        for entry in sorted_entries:
            print '%s : %d' % entry
        norm_value = float(sorted_entries[0][1] * 2.0)
        print ''
    return norm_value

def generate_hashtag_graph(user, tweet_count):
    tweets = get_tweets(user, tweet_count)

    if len(tweets) > 0:
        user_data = get_user_info(tweets[0])
        sn = user_data['screen_name']
        hashtag_usage = {}

        print "User id: %s Screen Name: %s Real Name: %s" % (user_data['id'], user_data['screen_name'], user_data['name'])
        
        for tweet in tweets:
            tweet_data = get_tweet_data(tweet)
                    
            for hashtag in tweet_data['hashtags']:
                if hashtag['text'] in hashtag_usage: 
                    hashtag_usage[hashtag['text']] += 1
                else:
                    hashtag_usage[hashtag['text']] = 1
        
        norm_value = print_statistics(hashtag_usage)
    
        print "** Generating Graph **"
        
        hashtag_graph = nx.Graph()
        hashtag_graph.add_node(sn)
        
        for hashtag in hashtag_usage.keys():
            hashtag_graph.add_node(hashtag)
            hashtag_graph.add_edge(sn, hashtag, weight = float(hashtag_usage[hashtag]) / norm_value)
            
        print ''
            
        pos=nx.spring_layout(hashtag_graph)
        plt.figure(figsize = (20, 20))
        plt.title(user_data['name'])
        nx.draw(hashtag_graph, pos, edge_color = 'b', alpha = 0.5, node_size = 0, iterations = 200)
        plt.axis('equal')
        plt.savefig('%s_hashtag.png' % sn)
        plt.show()

def add_user_interactions_to_graph(user, tweet_count, graph, treshold):
    tweets = get_tweets(user, tweet_count)
    user_interactions = {}
    return_list = []
    
    if len(tweets) > 0:
        user_data = get_user_info(tweets[0])
        sn = user_data['screen_name']
        
        print "User id: %s Screen Name: %s Real Name: %s" % (user_data['id'], sn, user_data['name'])
        
        for tweet in tweets:
            tweet_data = get_tweet_data(tweet)
                    
            for user in tweet_data['user_mentions']:
                if user['screen_name'] in user_interactions: 
                    user_interactions[user['screen_name']] += 1
                else:
                    user_interactions[user['screen_name']] = 1
    
        norm_value = print_statistics(user_interactions)
        
        for user in user_interactions.keys():
            if user_interactions[user] >= treshold:
                graph.add_node(user)
                graph.add_edge(sn, user, weight = (float(user_interactions[user]) / norm_value))
                return_list.append(user)
    
    return return_list
            
def plot_interaction_graph(graph, user):
    pos=nx.spring_layout(graph)
    plt.figure(figsize = (16.5, 11.7))
    plt.title('Social interactions for %s' % user)
    nx.draw(graph, pos, edge_color = 'b', alpha = 0.5, node_size = 0, iterations = 100)
    plt.axis('equal')
    plt.savefig('%s_interactions.png' % user)
    print 'Done!'

def generate_interactions_graph_for_users(users, tweet_count, current_level, max_level, graph, treshold, processed_users = []):
    for user in users:
        if not user in processed_users:
            processed_users.append(user)
            user_list = add_user_interactions_to_graph(user, tweet_count, graph, treshold)
            if current_level < max_level:
                generate_interactions_graph_for_users(user_list, tweet_count, current_level + 1, max_level, graph, treshold, processed_users)  

def generate_interactions_graph(user, tweet_count = 100, max_level = 2, treshold = 1):
    interaction_graph = nx.DiGraph()
    interaction_graph.add_node(user)
    generate_interactions_graph_for_users([user,], tweet_count, 0, max_level, interaction_graph, treshold)
    plot_interaction_graph(interaction_graph, user)

if __name__ == '__main__':
    generate_interactions_graph('MartinSLewis', tweet_count = 200, max_level = 2, treshold = 5)
        