#TMR indeed webscraper 
import random
import time
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
import pandas as pd

def getData(url)->list:
    data = []
    
    #Start web browser driver to emulate a real browser visiting the site to avoid captcha or bot recognition
    browser_options = ChromeOptions()
    browser_options.headless = True
    driver = Chrome(options=browser_options)
    browser_options.add_argument("start-maximized")
    
    #Nagivate to desired URL
    driver.get(url)
    
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
            'salary':salary.text
        }

        #Data added
        data.append(jobInfo)

    
    driver.quit()
    return data
    

def main():
    data = []
    for i in range(3):
        data += getData("https://www.indeed.com/q-python-jobs.html")
        #pausing for random amount of time to emulate real user
        time.sleep(random.random())
    
    #Converting raw data to a csv file which organizes data cleanly in a file that can be viewed in google sheets
    df = pd.DataFrame(data)
    print(df.head())
    df.to_csv('scraped2.csv')

main()