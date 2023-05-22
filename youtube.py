import streamlit as st
import googleapiclient.discovery
import googleapiclient.errors
import math
import pymongo
import certifi
import mysql.connector as sql
import pandas as pd
from PIL import Image

client = pymongo.MongoClient("mongodb+srv://admin:12345@cluster0.vbxqbgu.mongodb.net/?retryWrites=true&w=majority",tlsCAFile=certifi.where())
db = client.youtube
collection=db.harvesting_data

mydb=sql.connect(
host="localhost",
user="root",
password="",
)

apikey = "AIzaSyAua-mtrggdS3bCV72ReZRjx74SQCenWgQ"

mycursor=mydb.cursor(buffered=True)
mycursor.execute('use youtube')

# print(mydb)

def get_channel_details_with_channelid(channel_id):
  

    api_service_name = "youtube"
    api_version = "v3"
    api_key=apikey

   
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=api_key)

    request = youtube.channels().list(
        part="snippet,contentDetails,statistics,status",
        id=channel_id
    )
    response = request.execute()
    return response


def get_playlistitem_details_with_channelid(playlist_id):
    api_service_name = "youtube"
    api_version = "v3"
    api_key=apikey

    youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey=api_key)
    request = youtube.playlistItems().list(
        part="snippet",
        maxResults=50,
        playlistId=playlist_id,
    )
    response = request.execute()
    return response


def get_playlistitem_details_with_pagetoken(playlist_id, page_token):
    api_service_name = "youtube"
    api_version = "v3"
    api_key=apikey

    youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey=api_key)
    request = youtube.playlistItems().list(
        part="snippet",
        maxResults=50,
        playlistId=playlist_id,
        pageToken = page_token
    )
    response = request.execute()
    return response

def get_playlist_item_details_with_playlistid_wrapper(playlist_id):
    response=get_playlistitem_details_with_channelid(playlist_id = playlist_id)
    video_ids=[]
    playlist=[]

    for i in range(len(response.get('items'))):
        video_ids.append(response.get('items')[i].get('snippet').get('resourceId').get('videoId'))
        playlist.append(response.get('items')[i])

    next_page_token = response.get('nextPageToken')
    more_pages  = True

    while more_pages:
        if next_page_token is None:
            more_pages = False
        else:
            response=get_playlistitem_details_with_pagetoken(playlist_id=playlist_id, page_token=next_page_token)
            for i in range(len(response.get('items'))):
                video_ids.append(response.get('items')[i].get('snippet').get('resourceId').get('videoId'))
                playlist.append(response.get('items')[i])

            next_page_token=response.get('nextPageToken')
    return video_ids,playlist


def get_video_details_with_videoid(video_id):
    api_service_name = "youtube"
    api_version = "v3"
    api_key=apikey

   
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=api_key)

    request = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        id=video_id,
        maxResults=50,
        
    )
    response = request.execute()
    return response


def get_video_details_with_videoid_wrapper(video_ids):
    limit = math.ceil(len(video_ids)/50)
    videos = []
    for i in range(limit):
        r=get_video_details_with_videoid(video_ids[i*50:50*(i+1)])
        for i in r.get('items'):
            videos.append(i)
    return videos


def get_comment_details_with_videoid(video_ids):
   
    api_service_name = "youtube"
    api_version = "v3"
    DEVELOPER_KEY = apikey

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey = DEVELOPER_KEY)

    request = youtube.commentThreads().list(
        part="snippet,replies",
        maxResults=100,
        videoId=video_ids
    )
    response = request.execute()
    return response


def get_comment_details_with_videoid_wrapper(video_ids):
    comments = []
    for i in video_ids:
        try:
            comments.append({i : get_comment_details_with_videoid(i)})
        except:
            pass
    return comments
        

def construct_file_for_mongodb(channel_id):
    try:
        if collection.find_one(channel_id) is None:
            result = dict(_id = channel_id,channel_details=get_channel_details_with_channelid(channel_id))
            playlist_id = result.get('channel_details').get('items')[0].get('contentDetails').get('relatedPlaylists').get('uploads')
            playlist = get_playlist_item_details_with_playlistid_wrapper(playlist_id=playlist_id)
            result.update(dict(playlist_details = playlist[1]))
            video = get_video_details_with_videoid_wrapper(video_ids=playlist[0])
            result.update(dict(video_details = video))
            comments = get_comment_details_with_videoid_wrapper(playlist[0])
            result.update(dict(comment_details = comments))
            return result
        else:
            return 'Duplicate'
    except TypeError:
        return False


def data_for_dropdown():
    dropdown_data = []
    data= collection.find({},{"channel_details.items.snippet.title":True})
    for i in data:
        dropdown_data.append(i.get('channel_details').get('items')[0].get('snippet').get('title'))
    return dropdown_data
        
        
def migrate_to_mongodb(data):
    collection.insert_one(data)

def index_channel_details(channel_data):
    value = []
    value.append(channel_data.get('id'))
    value.append(channel_data.get('snippet').get('title'))
    value.append(channel_data.get('kind'))
    value.append(channel_data.get('statistics').get('viewCount'))
    value.append(channel_data.get('snippet').get('description'))
    value.append(channel_data.get('status').get('privacyStatus'))   
    return value

def insert_into_channel(channel_data):
    value = index_channel_details(channel_data)  
    mycursor.execute('insert into channel values(%s,%s,%s,%s,%s,%s)',tuple(value))
    mycursor.execute("commit;")

def index_playlist_details(playlist_data):
    value = []
    value.append(playlist_data.get('snippet').get('playlistId'))
    value.append(playlist_data.get('snippet').get('channelId'))
    value.append(playlist_data.get('snippet').get('channelTitle'))
    
    return value
    
def insert_into_playlist(playlist_data):
    value = index_playlist_details(playlist_data)
   
    mycursor.execute('insert into playlist values(%s,%s,%s)',tuple(value))
    mycursor.execute("commit;")

def convert_timestamp_to_seconds(timestamp):
    sec=0
    timestamp=timestamp.strip('PT')
    p=['H','M','S']
    val = {'H':3600,'M':60,'S':1}
    for i in p:
        if i in timestamp:
            s=timestamp.split(i)
            timestamp=s[1]
            sec+=int(s[0])*val.get(i)
    return sec
        

def index_video_details(video_data,playlist_id='N/A'):
    value = []
    value.append(video_data.get('id'))
    value.append(playlist_id)
    value.append(video_data.get('snippet').get('title'))
    value.append(video_data.get('snippet').get('description'))
    value.append(video_data.get('snippet').get('publishedAt'))
    value.append(video_data.get('statistics').get('viewCount',0))
    value.append(video_data.get('statistics').get('likeCount',0))
    value.append(video_data.get('statistics').get('dislikeCount',0))
    value.append(video_data.get('statistics').get('favoriteCount',0))
    value.append(video_data.get('statistics').get('commentCount',0))
    value.append(convert_timestamp_to_seconds(video_data.get('contentDetails').get('duration')))
    value.append(video_data.get('snippet').get('thumbnails').get('default').get('url'))
    value.append(video_data.get('contentDetails').get('caption')) 
    return value
    
def insert_into_video(video_data,playlist_id):
    for i in video_data:
        value = index_video_details(i,playlist_id)   
        mycursor.execute('insert into video values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',tuple(value))
        mycursor.execute("commit;")

def index_comment_details(comment_data):
    try:
        comment_data =comment_data
        value = []
        value.append(comment_data.get('id'))
        value.append(comment_data.get('snippet').get('videoId'))
        value.append(comment_data.get('snippet').get('topLevelComment').get('snippet').get('textDisplay'))
        value.append(comment_data.get('snippet').get('topLevelComment').get('snippet').get('authorDisplayName'))
        value.append(comment_data.get('snippet').get('topLevelComment').get('snippet').get('publishedAt'))
    
        return value
    except :
        return None
    
    
def insert_into_comment(comment_data):
    for dic in comment_data:
        for data in list(dic.values())[0].get('items'):
            value = index_comment_details(data)
            if value is not None:
                mycursor.execute('insert into comment values(%s,%s,%s,%s,%s)',tuple(value))
                mycursor.execute("commit;")
            else:
                pass

def migrate_to_sql(data):
    try:
         insert_into_channel(data.get('channel_details').get('items')[0])
         insert_into_playlist(data.get('playlist_details')[0])
         insert_into_video(data.get('video_details'),playlist_id=data.get('playlist_details')[0].get('snippet').get('playlistId'))
         insert_into_comment(data.get('comment_details'))
         return True
    except :
        return False
    
def get_data_for_option(channel_name):
    data=collection.find_one({"channel_details.items.snippet.title":channel_name})
    return data  


questions=[
    "1.What are the names of all the videos and their corresponding channels?",
    "2.Which channels have the most number of videos, and how many videos do they have?",
    "3.What are the top 10 most viewed videos and their respective channels?",
    "4.How many comments were made on each video, and what are their corresponding video names?",
    "5.Which videos have the highest number of likes, and what are their corresponding channel names?",
    "6.What is the total number of likes and dislikes for each video, and what are their corresponding video names?",
    "7.What is the total number of views for each channel, and what are their corresponding channel names?",
    "8.What are the names of all the channels that have published videos in the year 2022?",
    "9.What is the average duration of all videos in each channel, and what are their corresponding channel names?",
    "10.Which videos have the highest number of comments, and what are their corresponding channel names?"

]

def map_questions_to_query(questions):
    query=[
    "SELECT v.VIDEO_NAME,c.CHANNEL_NAME from video v JOIN playlist p ON v.PLAYLIST_ID = p.PLAYLIST_ID JOIN channel c ON c.CHANNEL_ID = p.CHANNEL_ID;",
    "SELECT c.CHANNEL_NAME,COUNT(v.VIDEO_ID) as 'COUNT' from channel c JOIN playlist p ON c.CHANNEL_ID = p.CHANNEL_ID JOIN video v ON v.PLAYLIST_ID=p.PLAYLIST_ID GROUP BY c.CHANNEL_NAME;",
    "SELECT v.VIDEO_NAME, v.VIEW_COUNT, c.CHANNEL_NAME FROM video v JOIN playlist p ON v.PLAYLIST_ID = p.PLAYLIST_ID JOIN channel c ON c.CHANNEL_ID = p.CHANNEL_ID ORDER BY VIEW_COUNT DESC LIMIT 10;",
    "SELECT COUNT(c.COMMENT_ID),v.VIDEO_NAME FROM comment c JOIN video v on c.VIDEO_ID=v.VIDEO_ID GROUP BY v.VIDEO_ID ORDER BY COUNT(c.COMMENT_ID) DESC;",
    "SELECT c.CHANNEL_NAME,v.VIDEO_NAME,v.LIKE_COUNT FROM video v JOIN playlist p ON v.PLAYLIST_ID = p.PLAYLIST_ID JOIN channel c ON c.CHANNEL_ID = p.CHANNEL_ID ORDER BY v.LIKE_COUNT DESC;",
    "SELECT VIDEO_NAME,LIKE_COUNT,DISLIKE_COUNT FROM video ORDER BY LIKE_COUNT DESC;",
    "SELECT c.CHANNEL_NAME,SUM(v.VIEW_COUNT) from video v JOIN playlist p ON v.PLAYLIST_ID = p.PLAYLIST_ID JOIN channel c ON c.CHANNEL_ID = p.CHANNEL_ID GROUP BY c.CHANNEL_ID;",
    "SELECT distinct(c.CHANNEL_NAME) from video v JOIN playlist p ON v.PLAYLIST_ID = p.PLAYLIST_ID JOIN channel c ON c.CHANNEL_ID = p.CHANNEL_ID WHERE year(v.PUBLISHED_DATE)=2022;",
    "SELECT c.CHANNEL_NAME,ROUND(AVG(v.DURATION),3)  from video v JOIN playlist p ON v.PLAYLIST_ID = p.PLAYLIST_ID JOIN channel c ON c.CHANNEL_ID = p.CHANNEL_ID GROUP BY c.CHANNEL_NAME;",
    "SELECT c.CHANNEL_NAME,v.VIDEO_NAME,count(co.COMMENT_ID) from video v JOIN playlist p ON v.PLAYLIST_ID = p.PLAYLIST_ID JOIN channel c ON c.CHANNEL_ID = p.CHANNEL_ID JOIN comment co ON v.VIDEO_ID =co.VIDEO_ID GROUP BY v.VIDEO_ID ORDER BY count(co.COMMENT_ID) DESC;"
    ]

    columns=[
    ['Channel Name','Video Name'],
    ['Channel Name','Videos Count'],
    ['Channel Name','Video Name','View Count'],
    ['Video Name','Comments Count'],
    ['Channel Name','Video Name','Likes Count'],
    ['Video Name','Likes Count','Dislike Count'],
    ['Channel Name','Total Views Count'],
    ['Channel Name'],
    ['Channel Name','Average Duration'],
    ['Channel Name','Video Name','Comments Count']
    ]
    dic={}
    for i in range(len(questions)):
        dic[questions[i]]={'query':query[i],'columns':columns[i]}
    return dic

# questions_mapped=res=dict(zip(questions,query))

def main():
    # st.set_page_config(layout="wide")
    st.title("YouTube Data Scrapping")
    dropdown_values= data_for_dropdown()
    questions_mapped = map_questions_to_query(questions)
    valid_channel_id = True
    menu = ["Home","Search","Questions","About"]
    choice = st.sidebar.selectbox("Menu",menu)
    if choice=="Home":
        st.write('''This app is a Youtube Scraping web tool created using Streamlit. 
                It scrapes the Youtube channel data with the provided youtube channel ID.
                The retrived data are uploaded in to databases.Then we can analyse with few set of questions''')
        image = Image.open(r"C:\Users\Dhinesh Kumar\Downloads\yt.jpg") 
        st.image(image, caption='Youtube Data Harvesting')

    
    elif choice=="Search":

        with st.form(key='form1'):
            st.subheader("Get channel data with channel ID")
            st.write("Enter the channel ID")
            channel_id = st.text_input(label='channel ID',label_visibility='collapsed')
            submit_button = st.form_submit_button(label="get")
            if len(channel_id)==24 or len(channel_id)==0:
                pass
            else:
                valid_channel_id=False
                st.error("Please enter a valid channel ID")
            if submit_button and valid_channel_id:
                st.success(f"Channel Id '{channel_id}' received for scraping".format(channel_id), icon="✅")
                data=construct_file_for_mongodb(channel_id)
                if data != 'Duplicate':
                    migrate_to_mongodb(data)
                    dropdown_values = data_for_dropdown()
                    st.success(f"The data scrapping for the '{channel_id}' has completed successfully".format(channel_id), icon="✅")
                elif data == 'Duplicate':
                    st.error("The data for this channel Id has already scrapped")
                else:
                    st.error("Please enter a valid channel ID")
                
        st.divider()
        with st.form(key='form2'):
            st.subheader("Migrate scrapped data to SQL")
            st.write("Select a channel to migrate")
            option = st.selectbox('Select a channel to migrate',dropdown_values,index=len(dropdown_values)-1,help='Select an option',label_visibility='collapsed')
            # st.write('You selected:', option)
            submit_button = st.form_submit_button(label="migrate")
            if submit_button:
                st.success(f"{option} channel has received for migrating".format(option), icon="✅")
                if migrate_to_sql(get_data_for_option(option)):
                    st.success(f"The {option} data has migrated successfully".format(option), icon="✅")
                else:
                    st.error("The selected channel data has migrated already")
        st.divider()
        st.caption("You can find the analysis questions under questions option in the menu")
        

    elif choice=="Questions":
        with st.form(key='form3'):
            st.subheader("Questions")
            st.write('Select a question')
            question = st.selectbox('Select a question',questions,help='Select a question',label_visibility='collapsed')
            # st.write('You selected:', option)
            submit_button = st.form_submit_button(label="get data")
            if submit_button:
                st.success(question, icon="✅")
                selected_ques=questions_mapped.get(question)
                mycursor.execute(selected_ques.get('query'))
                st.dataframe(pd.DataFrame(mycursor,columns=selected_ques.get('columns')),use_container_width=True)
    elif choice=="About":
        st.header('About tool')
        st.write('''Youtube data scrapper will harvest the data from the public youtube channels.
                   We need to provide the channel ID to this too which we want to scrape the data.
                   once after scrapping, the harvested data is stored into MongoDB as a datalake, 
                   the selected data can be further moved into MySQL and we can do analysis of our data''')

        

main()