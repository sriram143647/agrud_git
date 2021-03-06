from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import csv
import time
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import os
domain = os.getcwd().split('\\')[-1].replace(' ','_')
output_file = f'{domain}_data_links.csv'
country_change = 0

def write_header():
    with open(output_file,"a",newline="") as file:
        writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(['master id','isin name','factsheet link','prospectus link'])

def write_output(data):
    with open(output_file,"a",newline="") as file:
        writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(data)

def csv_filter():
    filtered_df = pd.DataFrame()
    unique_isin = []
    cols = ["master id","isin name","factsheet link","prospectus link"]
    try:
        df = pd.read_csv(output_file)
    except FileNotFoundError:
        write_header()
        return 0
    for isin,grouped_df in df.groupby(by=['isin name']):
        for i,row in grouped_df.iterrows():
            if row[2] is not np.nan and row[3] is not np.nan:
                if isin not in unique_isin:
                    unique_isin.append(isin)
                    filtered_df = filtered_df.append(pd.DataFrame([row],columns=cols),ignore_index=True)
    try:
        filtered_df.to_csv(output_file,columns=cols,index=False)
    except:
        pass

def get_driver():
    s=Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(service=s,options=options)
    # driver.minimize_window()
    return driver

def priv_investor_gen_case(driver,isin,master_id):
    print(isin)
    global country_change
    factsheet_link = ''
    prospectus_link = ''
    country_list = ['Luxembourg','Singapore','Hong&#32;Kong','Switzerland','United&#32;Kingdom','Ireland','Germany','Sweden']
    for country in country_list:
        if country_change == 1:
            try:
                country_change = WebDriverWait(driver,3).until(EC.element_to_be_clickable((By.XPATH,'//*[@class="fund-market selected"]')))
                driver.execute_script("arguments[0].click();", country_change)
            except:
                pass

        try:
            country_select = WebDriverWait(driver,3).until(EC.visibility_of_element_located((By.XPATH,'//*[@class="country-selector"]')))
            country_select.click()
        except:
            pass

        try:
            select_country = WebDriverWait(driver,3).until(EC.element_to_be_clickable((By.XPATH,f'//*[@data-cname="{country}"]')))
            driver.execute_script("arguments[0].click();", select_country)
        except:
            pass
    
        # try:
        #     investor_type = WebDriverWait(driver,3).until(EC.visibility_of_element_located((By.XPATH,'//*[@for="professional"]/span')))
            # driver.execute_script("arguments[0].click();", investor_type)
        # except Exception as e:
        #     pass

        try:
            tick_mark = WebDriverWait(driver,3).until(EC.element_to_be_clickable((By.XPATH,'//*[@for="fund-market-checkbox-mandatory"]/span')))
            driver.execute_script("arguments[0].click();", tick_mark)
        except:
            pass
        
        try:
            confirm = WebDriverWait(driver,3).until(EC.element_to_be_clickable((By.XPATH,'//*[@class="btn fundmarket-btn confirm"]')))
            confirm.click()
        except:
            pass

        try:
            search_ele = WebDriverWait(driver,3).until(EC.visibility_of_element_located((By.XPATH,'//*[@placeholder="Place your search request here ( fund name / ISIN / WKN / Valor No )"]')))
            search_ele.clear()
        except:
            pass

        try:
            search_ele = WebDriverWait(driver,3).until(EC.visibility_of_element_located((By.XPATH,'//*[@placeholder="Place your search request here ( fund name / ISIN / WKN / Valor No )"]')))
            search_ele.send_keys(str(isin))
        except:
            pass

        try:
            btn = WebDriverWait(driver,3).until(EC.visibility_of_element_located((By.XPATH,'//*[@class="searchButton"]')))
            btn.click()
        except:
            pass
        
        count = 1
        while count < 5:
            time.sleep(5)
            try:
                url_ele_1 = driver.find_element(By.XPATH,'//*[@data-name="MR"]')
                hover_act = ActionChains(driver).move_to_element(url_ele_1)
                hover_act.perform()
            except:
                pass

            try:
                drop_down_btn = WebDriverWait(driver,3).until(EC.visibility_of_element_located((By.XPATH,'//*[@class="collapse collapse-open"]')))
                drop_down_btn.click()
            except:
                pass

            try:
                url_ele_2 = driver.find_element(By.XPATH,'//*[@data-name="PR"]')
                hover_act = ActionChains(driver).move_to_element(url_ele_2)
                hover_act.perform()
            except:
                pass

            soup = BeautifulSoup(driver.page_source,'html5lib')
            try:
                if isin in soup.find('div',{'class':'fund-info'}).find_all('div')[-1].text:                
                    try:
                        if factsheet_link == '':
                            factsheet_link = soup.find('div',{'data-name':'MR'}).find('a').get('href')
                            if f'en_{isin}' not in factsheet_link:
                                factsheet_link = ''
                            print(f'factsheet link found')
                    except:
                        pass
                    
                    try:
                        if prospectus_link == ''    :
                            prospectus_link = soup.find('div',{'data-name':'PR'}).find('a').get('href')
                            if f'en_{isin}' not in factsheet_link:
                                factsheet_link = ''
                            print(f'prospectus link found')
                    except:
                        pass
                    
                    if factsheet_link != '' and prospectus_link != '':
                        country_change = 0
                        row = [master_id,isin,factsheet_link,prospectus_link]
                        write_output(row)
                        return 0
                    else:
                        count += 1
                        country_change = 1
                        continue
            except:
                country_change = 1
                break
        if country_change == 1:
            continue
    row = [master_id,isin,factsheet_link,prospectus_link]
    write_output(row)

def isin_downloaded():
    isin_downloaded = []
    with open(output_file,"r") as file:
        csvreader = csv.reader(file)
        header = next(csvreader)
        for row in csvreader:
            isin_downloaded.append(row[1])
    return isin_downloaded

def start_fundinfo_private_scraper():
    csv_filter()
    downloaded_isin = isin_downloaded()
    driver = get_driver()
    link = 'https://www.fundinfo.com/en'
    driver.get(link)
    try:
        accept_btn = WebDriverWait(driver,3).until(EC.visibility_of_element_located((By.XPATH,'//*[@id="qc-cmp2-ui"]/div[2]/div/button[2]')))
        accept_btn.click()
    except:
        pass
    df = pd.read_csv(data_file,encoding="utf-8")
    df = df.drop_duplicates(subset=['master_id'])
    df = df[~df['symbol'].isin(downloaded_isin)]
    for i,row in df.iterrows():
        isin = row[3]
        master_id = row[0]
        priv_investor_gen_case(driver,isin,master_id)
    driver.quit()
    csv_filter()
            
if __name__ == '__main__':
    for file in os.listdir():
        if 'Factsheet_Prospectus' in file and '.csv' in file:
            data_file = os.getcwd()+'\\'+file
            break  
    start_fundinfo_private_scraper()