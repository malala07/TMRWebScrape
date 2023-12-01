from xmlrpc.client import boolean
from flask import Flask, request, render_template
import random
import time
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db,firestore
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By


app = Flask(__name__)

@app.route('/')
def index():
  return render_template('TMR.html')

@app.route('/', methods=['POST'])
def my_link():
    #TMR indeed webscraper 
    
    #authenticate the database
    c_path= r"tmr-project-8f8de-firebase-adminsdk-8xj0a-4696ee732a.json"
    login=credentials.Certificate(c_path)
    app=firebase_admin.initialize_app(login)
    db=firestore.client()
    
    def getData(url,index)->list:
        data = []
        #Start web browser driver to emulate a real browser visiting the site to avoid captcha or bot recognition
        browser_options = ChromeOptions()
        driver = Chrome(options=browser_options)

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

    def count_db()->int:
        holder=0
        jobs= db.collection('Job Index').stream()
        for job in jobs:
            holder+=1
        return holder+1

    def main():
        data = []
        text = request.form['text']
        text = text.replace(" ","-")
        doc_ref=db.collection('Job Index').document(text)
        count=0
        index=0
        if check_db(text):#check to see if the  search text is already in the database if true get the # of listings 
           new_ref=db.collection('Job Index').stream()
           for job in new_ref:
               holder=job.to_dict()
               if holder.get('title')==text:
                 count=holder.get('number of listings')
                 index=holder.get('index')
        else:
            
            index=count_db()

        #print('count:'+count+'index'+index)
        for i in range(3):
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

    return 'scraped'

if __name__ == '__main__':
  app.run(debug=True)
