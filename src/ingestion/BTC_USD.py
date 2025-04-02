from pycoingecko import CoinGeckoAPI
import pandas as pd
from google.cloud import bigquery

cg = CoinGeckoAPI()
ohlc = cg.get_coin_ohlc_by_id(id='bitcoin', vs_currency='usd', days='7')

df = pd.DataFrame(ohlc)
df.columns=['date','open','high','low','close']
df['date'] = pd.to_datetime(df['date'], unit='ms')
df.set_index('date',inplace=True)
# print(df)

client=bigquery.Client()
table_id = "erag-cbec-qna.for_dev.btc_usd_ohlc"
job_config = bigquery.LoadJobConfig(
    schema=[
        bigquery.SchemaField("date",bigquery.enums.SqlTypeNames.TIME)
    ]
)
job=client.load_table_from_dataframe(df, table_id, job_config=job_config)
job.result()