import os 
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python_operator import PythonOperator
import pandas as pd 
import numpy as np 
from sqlalchemy import create_engine
from time import time

# URL = 'https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv'
URL = 'https://data.cityofnewyork.us/api/views/kxp8-n2sj/rows.csv?accessType=DOWNLOAD'


#path_to_home = "D:\\courses\\airflow\\output.csv"
path_to_home = os.environ.get('AIRFLOW_HOME' , "/opt/airflow/")

def load_data_sql():
    arr =np.array([0,1,2])
    print("Hello from PythonOperator" , arr)
    engine = create_engine('postgresql://airflow:airflow@postgres/airflow')
    engine.connect()
    query = """
        SELECT 1 as number;
        """

    data = pd.read_sql(query, con=engine)
    print(data)
    df_iter = pd.read_csv('output.csv', iterator=True, chunksize=100000)
    df = next(df_iter)
    df.head(n=0).to_sql(name='yellow_taxi_data', con=engine, if_exists='replace')
    while True: 
        t_start = time()
        try :
            df = next(df_iter)
            
        except :
            break 
        df.tpep_pickup_datetime = pd.to_datetime(df.tpep_pickup_datetime)
        df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime)
        
        df.to_sql(name='yellow_taxi_data', con=engine, if_exists='append')

        t_end = time()

        print('inserted another chunk, took %.3f second' % (t_end - t_start))

default_args = {
    'owner': 'omar',
    'retries': 10,
    'retry_delay': timedelta(minutes=2)
}

with DAG(
    dag_id='our_first_dag_v2',
    default_args=default_args,
    description='This is our first dag that we write',
    start_date=datetime(2024, 1, 26, 2),
    schedule_interval='@daily'
) as dag:
    wget_task = BashOperator(
        task_id='wget',
        #bash_command= f'curl -sS {URL} > {path_to_home}/output.csv'
        bash_command= 'echo hello'
    )
ingest_task = BashOperator(
        task_id='seceond_task',
        bash_command= f'wc -l {path_to_home}/output.csv'
    )

convert_data =PythonOperator(
     task_id='load_data',
    python_callable=load_data_sql
)

wget_task >> ingest_task >> convert_data