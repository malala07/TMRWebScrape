from xmlrpc.client import boolean
from flask import Flask, request, render_template, jsonify
import random
import time
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db,firestore
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By

#Initialize Flask app
app = Flask(__name__, static_url_path='/static')
db_instance = None
data = [] #Defined the data var at the beignning 

# Firebase authentication
c_path= r"TMRWebScrape-main\TMRWebScrape-main\TMR_v2\tmr-project-8f8de-firebase-adminsdk-8xj0a-4696ee732a.json"
login=credentials.Certificate(c_path)
firebase_app=firebase_admin.initialize_app(login)
db=firestore.client()

# Route to render the main page with data
@app.route('/')
def index():
  return render_template('TMR.html', data = data)

@app.route('/get_data')
def get_data():
    job_info_data = get_job_info_data()
    return jsonify(job_info_data)
# Created this function to retrieve job information data from Firebase
def get_job_info_data():
    job_info_data = []
    job_info_collection = db.collection('new_web_data').stream()

    for job_info_doc in job_info_collection:
        job_info = job_info_doc.to_dict()
        job_info_data.append(job_info)

    return job_info_data

# Route to handle the web scrapping process
@app.route('/scraped', methods=['POST'])
def my_link():
    #TMR indeed webscraper
    global data
    data =[]
    
    # This function will perform a web scrape on the Indeed website
    def getData(url,index)->list:
    
        #Start web browser driver to emulate a real browser visiting the site to avoid captcha or bot recognition
        browser_options = ChromeOptions()
        driver = Chrome(options=browser_options)
        # This sets the user agent to avoid bot recognition
        driver.execute_cdp_cmd('Emulation.setUserAgentOverride', {

               "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win32; x86) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36",

               #"platform": "Win32",

               #"acceptLanguage":"ro-RO"

       })
        driver.get(url)

        time.sleep(10)
                          
        #Finds each indiviudal job listing and places it in a list
        job_page = driver.find_element(By.XPATH,'//*[@id="mosaic-provider-jobcards"]')
        job_listings = job_page.find_elements(By.CLASS_NAME,"job_seen_beacon")

        #Searches through the list of job listings and selects the html elements containing desired info to be collected
        for listing in job_listings:
            title = listing.find_element(By.CSS_SELECTOR,"h2 > a")
            company = listing.find_element(By.XPATH, '//*[@id="mosaic-provider-jobcards"]/ul/li[1]/div/div[1]/div/div[1]/div/table[1]/tbody/tr/td/div[2]/div/span')
            salary = listing.find_element(By.XPATH, '//*[@id="mosaic-provider-jobcards"]/ul/li[1]/div/div[1]/div/div[1]/div/table[1]/tbody/tr/td/div[3]/div[1]')

            jobInfo = {
                'title':title.text,
                'Company':company.text,
                'salary':salary.text,
                'index':index
            }

            #Save the data to the database
            doc_ref=db.collection('new_web_data').document(title.text.replace("/","_"))
            doc_ref.set({ 
                'title':title.text,
                'Company':company.text,
                'salary':salary.text,
                'index':index})
            

            #Data added
            data.append(jobInfo)
   
        driver.quit()
        return data
    # This checks the database to see if the given text is the same as an index in the db
    def check_db(txt)->boolean:#checkls the database if a givinen txt is in the job index returns boolean
        jobs = db.collection('Job Index').stream()
        for job in jobs:
            holder=job.to_dict()
            print(holder.get('title'))
            if holder.get('title')==txt:
                print('ture')
                return True
        print('flase')
        return False

    #This function will count the number of job index's in the database
    def count_db()->int:
        holder=0
        jobs= db.collection('Job Index').stream()
        for job in jobs:
            holder+=1
        return holder+1

    def main():
        global data
        data = []
        text = request.form['text']
        text = text.replace(" ","-")
        doc_ref=db.collection('Job Index').document(text)
        count=0
        index=0

        if check_db(text):#check to see if the  search text is already in the database if true get the # of listings 
           new_ref=db.collection('Job Index').stream()
           for job in new_ref:
               holder = job.to_dict()
               if holder.get('title')==text:
                 count=holder.get('number of listings')
                 index=holder.get('index')
        else:
            
            index=count_db()    
        # This will make the program run (2) times for more data
        for i in range(2):
            data += getData(("https://www.indeed.com/q-" + text + "-jobs.html"),index)
            count+=len(data)
            #pausing for random amount of time to emulate real user
            time.sleep(random.random())
        #wirte the search to the database 
        doc_ref.set({
            'title':text,
            'number of listings':count,
            'index':index
        })    
        #Converting raw data to a csv file which organizes data cleanly in a file that can be viewed in google sheets
        df = pd.DataFrame(data)
        print(df.head())
        df.to_csv('scraped6.csv')

    main()

    return render_template('TMR.html', data=data)

if __name__ == '__main__':
  app.run(debug=True)
