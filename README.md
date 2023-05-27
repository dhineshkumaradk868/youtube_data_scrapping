
# Youtube data harvesting and warehousing 

Youtube data scrapper will harvest the data from the public youtube channels using youtube V3 api.We need to provide the channel ID to this too which we want to scrape the data.Once after scrapping, the harvested data is stored into MongoDB as a datalake, the selected data can be further moved into MySQL and we can do few analysis of our data.


## Acknowledgements

 - [GUVI](https://www.guvi.in/)
 - [Mentor Mr.Nethaji Nirmal](https://www.linkedin.com/in/nethaji-nirmal/)
 - [Mentor Mr.Santhosh Nagaraj](https://www.linkedin.com/in/santhoshnagaraj94/)
 - [Streamlit docs](https://docs.streamlit.io/)


## Tech Stack

**Language:** Python
**Libraries:** streamlit,google-api-python-client,pymongo,certifi,mysql-connector-python,pandas,Pillow
**SQL Database:**: MySQL
**NoSQL Database:**: MongoDB
**GUI Framework:** Streamlit


## Scraping the channel data
To scrape channel data youtube V3 api is used. Various endpoints are used to get respective data like channel, playlist, video and comments. All the endpoints require an API-key which can be created from google developer account. Each endpoint needs specific input to retrive the data.

## Uploading data in MongoDB
Once the data is scrapped, The data will be structured and constructed as an single embedded document. The document is then pushed into MongoDB, here we are using mongo as a data lake.

## Uploading data in MySQL
At the very next process, retrived the data from mongo and constructed it in the form of quries. Using these quries the data will be inserted in to SQL tables.

## Creating the UI
Used Streamlit app for creating the GUI for Twitter Scraping. Used menus for home, searching and questions

**Menu 1 -- Home**  
Home page of the UI contains title of the app and an intro

**Menu 2 -- Search**  
Search menu is used to search the youtube channel with channel ID and migrate the scrapped data into SQL

**Menu 3 -- Questions**  
Questions menu is used to analyse the scrpped data with the few set of questions

**Menu 4 -- About**  
Under About menu, we can find few descriptions of the major components used


## Creating the UI
Demo of the project is posted in the [Linkedin](https://www.linkedin.com/posts/dhineshkumar-dk_webscraping-datascience-ai-activity-7068244026088456192-YG1K?utm_source=share&utm_medium=member_desktop) 