from datetime import datetime
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
import markets_ft.markets_ft_com_scraper as market
import fundsquare.fundsquare_net_scraper as fundsquare
import fundinfo.fundinfo_private_investor_scraper as priv_fundinfo
import fundinfo.fundinfo_professional_investor_scraper as prof_fundinfo
import sg_morningstar.sg_morningstar_scraper as morningstar
import pandas as pd
import smtplib,ssl
import os
import logging as log
# file_path = '/home/ubuntu/rentech/nav_scraping/'
file_path = r'D:\\sriram\\agrud\\NAV_scraping\\server_files\\'
data_file = file_path+'MF List - Final.csv'
output_file = file_path+'scraped_data.csv'
non_scraped_isin_file = file_path+'non_scraped_data.csv'
log_file = file_path+'scraper_run_log.txt'
log.basicConfig(filename = log_file,filemode='a',level=log.INFO)
my_log = log.getLogger()

def send_email(row_count=0,status=None,err_text=None):
    sender_email = 'agrud.scrapersmail123@gmail.com'
    email_password = 'qwerty@123'
    receivers_email_list = ["prince.chaturvedi@agrud.com","sayan.sinharoy@agrud.com","soumodip.pramanik@agrud.com","vidyut.lakhotia@agrud.com","bhavesh.bansal@agrud.com","jayati.kayet@agrud.com"]
    subject = f"Nav Scraping data ingestion: {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}"
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ','.join(receivers_email_list)
    msg['Subject'] = subject
    body = f"Total records inserted: {row_count}\ncronjob status: {status}\nError:{err_text}"
    msg.attach(MIMEText(body,'plain'))
    attach_file_name = non_scraped_isin_file
    with open(attach_file_name,'rb') as send_file:
        msg.attach(MIMEApplication(send_file.read(), Name='non_scraped_data.csv'))
    text = msg.as_string()
    context = ssl.create_default_context()
    server = smtplib.SMTP('smtp.gmail.com',587)
    server.starttls(context=context)
    server.login(sender_email,email_password)
    server.sendmail(sender_email,receivers_email_list,text)
    server.quit()
    my_log.info(f'email sent')

def db_insert(df):
    import mysql.connector
    result = df[['master id','price','date']].values.tolist()
    try:
        db_conn = mysql.connector.connect(host='54.237.79.6',user='rentech_user',database = 'rentech_db',password='N)baegbgqeiheqfi3e9314jnEkekjb',auth_plugin='mysql_native_password')
        cursor = db_conn.cursor()
        sql = """INSERT INTO `raw_data` 
        (`id`, `master_id`, `indicator_id`, `value_data`, `json_data`, `data_type`, `ts_date`, `ts_hour`, `job_id`, `batch_id`, `timestamp`) 
        VALUES (NULL, %s, 371, %s, NULL, 0, %s, '0:0:0', 12, NULL, NOW()) ON DUPLICATE KEY UPDATE 
        master_id = VALUES(master_id), indicator_id = VALUES(indicator_id), value_data = VALUES(value_data), json_data = VALUES(json_data),
        data_type = VALUES(data_type), ts_date = VALUES(ts_date) ,ts_hour = VALUES(ts_hour), job_id = VALUES(job_id), batch_id = VALUES(batch_id);"""
        cursor.executemany(sql, result)
        rows = cursor.rowcount
        my_log.info(f'{rows} rows inserted')
        db_conn.commit()
        send_email(row_count=rows,status='success') 
    except Exception as e:
        pass
        my_log.info(f'Exception: {e}')
    finally:
        if (db_conn.is_connected()):
            cursor.close()
            db_conn.close()
            my_log.info('Connection closed')

def vars_func(scraper_var):
    scraper_var.output_file = output_file
    scraper_var.data_file = data_file
    # scraper_var.non_scraped_isin_file = non_scraped_isin_file

def retry(func,retries=1):
    def retry_wrapper(*args,**kwargs):
        attempt = 0
        while attempt <= retries:
            try:
                my_log.info(f'Attempt {attempt}')
                return func(*args,**kwargs)
            except:
                my_log.info('Exception occured')
                attempt += 1
    return retry_wrapper

@retry
def market_ft_func():
    # market_ft scraper
    my_log.info(f'{datetime.now()} market_ft scraping started')
    vars_func(market)
    market.start_markets_ft_scraper()
    my_log.info(f'{datetime.now()} market_ft scraping ended')

@retry
def fundsquare_func():
    # fundsquare scraper
    my_log.info(f'{datetime.now()} fundsquare scraping started')
    vars_func(fundsquare)
    fundsquare.start_fundsquare_scraper()
    my_log.info(f'{datetime.now()} fundsquare scraping ended')

@retry
def priv_fundinfo_func():
    # priv_fundinfo scraper
    my_log.info(f'{datetime.now()} fundinfo private scraping started')
    vars_func(priv_fundinfo)
    priv_fundinfo.start_fundinfo_priv_scraper()
    my_log.info(f'{datetime.now()} fundinfo private scraping ended')

@retry
def prof_fundinfo_func():
    # prof_fundinfo scraper
    my_log.info(f'{datetime.now()} fundinfo professional scraping started')
    vars_func(prof_fundinfo)
    prof_fundinfo.start_fundinfo_prof_scraper()
    my_log.info(f'{datetime.now()} fundinfo professional scraping ended')

@retry
def morningstar_func():
    # morningstar scraper
    my_log.info(f'{datetime.now()} morningstar scraping started')
    vars_func(morningstar)
    morningstar.start_sg_morningstar_scraper()
    my_log.info(f'{datetime.now()} morningstar scraping ended')

def non_scraped_isin():
    downloaded_isin = pd.read_csv(output_file)['isin name'].values.tolist()
    df = pd.read_csv(data_file,encoding="utf-8")
    df = df[~df['Symbol'].isin(downloaded_isin)]
    df.to_csv(non_scraped_isin_file,encoding='utf-8',index=False,header=None)
    
def start():
    my_log.info(f'-------------------start time: {datetime.now()}-------------------')
    # files deletion
    if os.path.exists(output_file):
        os.remove(output_file)
    else:
        pass
    
    if os.path.exists(non_scraped_isin_file):
        os.remove(non_scraped_isin_file)
    else:
        pass

    # scraper tasks
    my_log.info('task started')
    market_ft_func()
    fundsquare_func()
    morningstar_func()
    priv_fundinfo_func()
    prof_fundinfo_func()
    non_scraped_isin()
    my_log.info('task ended')

    # db insertion
    # df = pd.read_csv(output_file,encoding='utf-8')
    # db_insert(df)
    my_log.info(f'-------------------end time: {datetime.now()}-------------------')

if __name__ == '__main__':
    start()