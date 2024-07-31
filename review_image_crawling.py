from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time

import pandas as pd
import re
import requests
import os

from pytz import timezone
import datetime

import warnings
warnings.filterwarnings('ignore')

options = webdriver.ChromeOptions()
options.add_argument('--no-sandbox') # 보안 기능인 샌드박스 비활성화
options.add_argument('--disable-dev-shm-usage') # dev/shm 디렉토리 사용 안함

service = ChromeService(executable_path=ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

if not os.path.exists('images'):
    os.makedirs('images')

def musinsa_collector(url):
    df = pd.DataFrame() # 빈 데이터프레임 정의
    driver.get(url)
    time.sleep(3)

    # 사람인 척 하기 동적 이벤트 주기 -> 스크롤 내리기(js 명령어)
    driver.execute_script('window.scrollTo(0,800)')
    time.sleep(1)

    # 메인페이지 데이터 수집 시작(상품이름, 가격)
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')

    # 상품정보가 담긴 틀
    div = soup.find_all('div', {'class':'info'})

    for index_div, div_el in enumerate(div[1:11]): # 랭킹 2번째부터 11번째 상품
        # 상품 이름
        pdt_a = div_el.find('a', {'class':'name ampl-catch-click'})
        pdt_name = pdt_a.text

        # 상품 가격
        pdt_em = div_el.find('em', {'class':'sale grid'})
        pdt_price = pdt_em.text[:-1].replace(',', '')

        # 상품 식별 번호
        pdt_link_a = div_el.find('a', {'class':'name ampl-catch-click'}).attrs['href']
        pdt_link_num = pdt_link_a.split('/')[-1]

        # 상품별 url
        product_url = f'https://www.musinsa.com/app/goods/{pdt_link_num}'
        driver.get(product_url) # 상품별 페이지 접속
        time.sleep(5)

        # 댓글 확인하기 위해 하단 최대치에 근접하도록 스크롤
        driver.execute_script('window.scrollTo(0,9000)')
        time.sleep(10)

        # 상품 페이지 소스 가져오기
        html_rev = driver.page_source
        soup_rev = BeautifulSoup(html_rev, 'html.parser')

        # 댓글 박스(div) 가져오기
        review = soup_rev.find_all('div', {'class':'review-list'})
       
        # 상품 이미지 저장하기
        img_tag = driver.find_element(By.CSS_SELECTOR, 'img[src].sc-1jl6n79-4.AqRjD')
        img_src = img_tag.get_attribute('src')
        img_name = f"{index_div+1}_{pdt_link_num}.jpg" # 순서와 상품 식별 번호를 포함한 파일명
        img_path = os.path.join('images', img_name)
        response = requests.get(img_src)
        with open(img_path, 'wb') as file:
            file.write(response.content)
           
           
        # 댓글 정보 수집
        for rev in review:

            star = rev.find('span', {'class':'review-list__rating__active'}).attrs['style'].split()[1].replace('%','')
            comment = rev.find('div', {'class':'review-contents__text'})
            comment = str(comment).replace('<br/>', ' ')
            cleaner = re.compile('<.*?>')
            clean_comment = re.sub(cleaner, '', comment)
            clean_comment = re.sub('\s+', ' ', clean_comment)
            tmp_df = pd.DataFrame({'상품명':[pdt_name],
                                   '가격':[pdt_price],
                                   '별점':[star],
                                   '댓글':[clean_comment]})
            df = pd.concat([df, tmp_df], axis=0)

    df.to_csv('./무신사_어스_TOP10_추출파일.csv', index=False, encoding='utf-8-sig')
    print('무신사 어스 상품 TOP10 수집 완료')
    driver.close()

# 무신사 어스 후기순 랭킹 페이지
url = 'https://www.musinsa.com/spc/earth/goods?includeSoldOut=false&sortCode=REVIEW&listViewType=3GridView&page=1&size=120&useCustomPrice=false'
musinsa_collector(url)
