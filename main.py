import logging
import time
import pytz

from datetime import datetime
from client import Client
from notification import GoogleEmail, DummyEmail
from config import save_config, load_config, get_default_config

# logger ---
logging.basicConfig(level=logging.INFO, format='[%(asctime)s][%(levelname)s] %(message)s [%(filename)s:%(lineno)d]')
logger = logging.getLogger('main')

# program ---
def validate(config):
    # 檢查欄位是否丟失
    email_config = config.get('email')
    if not email_config:
        return False
    if  'enabled' not in email_config or \
        'smtp_server' not in email_config or \
        'smtp_port' not in email_config or \
        'username' not in email_config or \
        'password' not in email_config:
        return False
    user_config = config.get('user')
    if not user_config:
        return False
    if 'init' not in user_config or 'unique_id' not in user_config:
        return False

    # 檢查是否需要初始化
    need_init = user_config.get('init')
    if need_init:
        return False
    return True

def init(config):
    config = get_default_config()
    email_config = config.get('email')
    email_config['enabled'] = input('是否啟用 email 通知 (y/n): ') == 'y'
    if email_config['enabled']:
        email_config['smtp_server'] = input('請輸入 smtp 伺服器位址: ').strip()
        email_config['smtp_port'] = int(input('請輸入 smtp 伺服器埠號: ').strip())
        email_config['username'] = input('請輸入 smtp 使用者名稱: ').strip()
        email_config['password'] = input('請輸入 smtp 使用者密碼: ').strip()
    
    user_config = config.get('user')
    user_config['init'] = False
    user_config['unique_id'] = input('請輸入欲查詢之身分證號碼: ')
    save_config(config)
    return config

def main():
    config = load_config()
    if not validate(config):
        config = init(config)

    client = Client()
    email_config = config.get('email')
    username, password = email_config.get('username'), email_config.get('password')
    if email_config.get('enabled'):
        email = GoogleEmail(username, password)
    else:
        email = DummyEmail()
    
    tw = pytz.timezone('Asia/Taipei')
    send_status = True
    current_status = None
    while True:
        current_time = datetime.now(tw)
        start_time = current_time.replace(hour=21, minute=0, second=0, microsecond=0)
        end_time = current_time.replace(hour=23, minute=59, second=59, microsecond=0)
        if start_time < current_time < end_time:
            logger.info(f'目前時間介於 21:00 ~ 23:59，此時段不開放查詢')
        else:
            try:
                order_progress = client.get_order_progress(config.get('user').get('unique_id'))
                if order_progress:
                    claim_no, accept_date, status, close_date = order_progress['claimNo'], order_progress['acceptDate'], order_progress['status'], order_progress['closeDate']
                    logger.info(f"claim_no: {claim_no}, accept_date: {accept_date}, status: {status}, close_date: {close_date}")

                    if (current_status and current_status != status) or send_status == False:
                        send_status = email.send(username, [username], '和泰網路理賠進度通知', f'理賠進度: {status}')

                    if current_status != status:
                        logger.info(f"status changed: {status}")
                        current_status = status
                else:
                    logger.info('no order progress')
            except:
                logger.error("unexpected error", exc_info=True)
        time.sleep(10)

if __name__ == '__main__':
    main()