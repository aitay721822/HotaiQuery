import requests
import ddddocr
import logging

class Client:

    valid_len = 4
    captcha_url = 'https://ec2.hotains.com.tw/B2CAPI/api/common/getCaptcha'
    order_url = 'https://ec2.hotains.com.tw/B2CAPI/api/orders/getAs400OrderProgress'
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/plain, */*',
        'Host': 'ec2.hotains.com.tw',
        'Origin': 'https://ec2.hotains.com.tw',
        'Referer': 'https://ec2.hotains.com.tw/general/query',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
    }

    def __init__(self, logger = logging.getLogger('client')):
        self.logger = logger
        self.classifier = ddddocr.DdddOcr(show_ad=False)
            
    def get_captcha(self):
        resp = requests.post(self.captcha_url, headers=self.headers)
        if resp and resp.status_code == 200:
            resp_json = resp.json()
            code, data, msg = resp_json['code'], resp_json['data'], resp_json['msg']
            if code == 20000:
                return data['code'], ddddocr.base64_to_image(data['codeImgBase64'])
            else:
                self.logger.error(f"[captcha] fetch failed, error: {code}, reason: {msg}")
        else:
            if resp:
                self.logger.error(f"[response] fetch failed, status_code: {resp.status_code}, url: {resp.url}")
            else:
                self.logger.error(f"[response] fetch failed, reason: response is empty")
        return -1, None

    def get_order_progress(self, unique_id):
        code, captcha_img = self.get_captcha()
        if code == -1:
            return None

        captcha = self.classifier.classification(captcha_img)
        if len(captcha) != self.valid_len:
            self.logger.error(f"[classifier] invalid classification result, captcha: {captcha}")
            return None
        
        resp = requests.post(self.order_url, headers={**self.headers, 'Authorization': 'Bearer undefined'}, json={
            'captcha': captcha,
            'code': code,
            'idNo': unique_id,
            'mobile': '',
            'searchType': '2',
        })
        if resp and resp.status_code == 200:
            resp_json = resp.json()
            code, msg, data = resp_json['code'], resp_json['msg'], resp_json['data']
            if code == 20000:
                return data[0] if len(data) > 0 else None
            else:
                self.logger.error(f"[order] fetch failed, error: {code}, reason: {msg}")
        else:
            if resp:
                self.logger.error(f"[response] fetch failed, status_code: {resp.status_code}, url: {resp.url}")
            else:
                self.logger.error(f"[response] fetch failed, reason: response is empty")
        return None