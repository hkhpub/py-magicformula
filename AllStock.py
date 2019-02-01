# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 11:26:02 2016

@author: 리밸런서 (cafe.naver.com/rebalancer)
"""
import sys
import urllib.request                # 웹페이지 호출
from urllib.error import URLError, HTTPError
from bs4 import BeautifulSoup        # 웹페이지 파싱
import re                            # 정규식
import time                          # 시간 딜레이
import pickle                        # 자료형 저장

# Daum 전종목 시세 페이지를 파싱해 전종목코드와 업종 시세, 재무정보를 읽어 파일로 저장한다.

# 파싱한 정보를 저장할 전역 변수
# 종목코드로 종목코드에 해당하는 정보를 찾을 수 있게 Dictionary 형태로 구성
stock = {}  # {종목코드:[종목명,시장구분,업종,현재가,PER,재무정보,추정실적 컨센서스]}

# gubun='P'이면 코스피, gubun='Q'이면 코스닥 시장의 종목 정보를 가져온다.
def GetStockCode(gubun):
    url = 'http://finance.daum.net/quote/all.daum?type=U&stype=' + gubun
    
    while True:
        try:
            f = urllib.request.urlopen(url).read()
        except HTTPError as e:
            # do something
            print('Error code: ', e.code, ' 10초 대기')
            time.sleep(10)
        except URLError as e:
            # do something
            print('Reason: ', e.reason, ' 10초 대기')
            time.sleep(10)
        else:
            # do something
            #print('good!')
            break
            
    
    soup = BeautifulSoup(f, 'html.parser')
    
    # 'class'속성의 값이 'fl_le'인 'h4'태그를 모두 찾는다.
    fields = soup.find_all('h4',{'class':'fl_le'})
    
    for field in fields: # 검색된 모든 'h4' 태그에 대하여 for문 안의 작업을 수행
        fieldName = field.get_text().split('|')[0]
        if fieldName == '금융업': # 금융업은 제외 시킨다.
            continue
        
        # 'h4' 태그 다음에 있는 'table' 태그를 table 변수로 가져 온다.
        table = field.find_next_sibling('table')
        # 'table' 내에서 'class'속성값이 'txt'인 'td'를 모두 찾는다.
        tds = table.find_all('td',{'class':'txt'})
        for td in tds: # 검색된 모든 'td'에 대하여 for문 안의 작업을 수행
            code = td.a['href'].split('=')[1]    # 종목코드를 구한다.
            name = td.get_text()                 # 종목명을 구한다.
            
            if code[5] != '0':                   # 우선주 제외
                continue
            if name.find('스팩') > 0:            # 스팩 제외
                continue
            
            # 현재가를 구하기 위해 다음 'td'를 찾는다.
            nextTd = td.find_next_sibling('td')  
            price = nextTd.get_text().replace(',','')  # 현재가를 구한다.
        
            # 전역변수 stock 에 파싱된 정보를 추가 한다.
            stock[code] = [name, gubun, fieldName, price]

# 종목의 PER를 가져온다.
# 에러 발생시 에러메시지를 리턴한다. 
def GetPER(code):
    url = 'http://wisefn.stock.daum.net/company/c1010001.aspx?cmp_cd=' + code
    
    while True:
        try:
            f = urllib.request.urlopen(url).read()
        except HTTPError as e:
            # do something
            print('Error code: ', e.code, ' 10초 대기')
            time.sleep(10)
        except URLError as e:
            # do something
            print('Reason: ', e.reason, ' 10초 대기')
            time.sleep(10)
        else:
            # do something
            #print('good!')
            break;
    
    soup = BeautifulSoup(f, 'html.parser')
    
    # 요청한 종목코드와 결과 페이지의 종목코드가 동일한지 확인
    span = soup.find('span',{'class':'cd'})
    codeInPage = span.get_text()
    if code != codeInPage:
        return '요청 code : ' + code + ' , 페이지 code : ' + codeInPage + ' - in GetPER()'
        
    # 'class'속성값이 'num'인 'b' 태그를 모두 찾는다.   
    bs = soup.find_all('b',{'class':'num'})
    if len(bs) != 6:
        return '[EPS, BPS, PER, 업종PER, PBR, 배당수익률] 형식과 다르다. 체크 필요 - in GetPER()'
        
    try:
        for index, b in enumerate(bs):
            if index == 2:
                stock[code].append(float(b.get_text().replace(',','')))
                break
    except:
        return '[' + code + '] PER 검출 실패'
        
# 종목의 재무정보를 가져온다.  
# 에러 발생 시 에러 메시지를 리턴한다. 
def GetFinaceInfo(code):
    url = 'http://wisefn.stock.daum.net/company/cF1001.aspx?cmp_cd=' + code
    
    while True:
        try:
            f = urllib.request.urlopen(url).read()
        except HTTPError as e:
            # do something
            print('Error code: ', e.code, ' 10초 대기')
            time.sleep(10)
        except URLError as e:
            # do something
            print('Reason: ', e.reason, ' 10초 대기')
            time.sleep(10)
        else:
            # do something
            #print('good!')
            break;
            
    soup = BeautifulSoup(f, 'html.parser')
    
    # 요청한 종목코드와 결과 페이지의 종목코드가 동일한지 확인
    form = soup.find('form')
    codeInPage = form['action'].split('=')[1]
    if code != codeInPage:
        return '요청 code : ' + code + ' , 페이지 code : ' + codeInPage + ' - in GetFinaceInfo()'

    # 다차원 배열 문자열을 찾기 위해 패턴 설정
    p = re.compile("changeFinData.*?\;", re.DOTALL)
    cfd_list = p.findall(soup.prettify())
    # 불필요한 문자열 제거
    cfd_str = cfd_list[0].replace('\n','').replace('changeFinData = ','').replace(';','')
    cfd = eval(cfd_str)
    
    stock[code].append(cfd)    
    
# 추정실적 컨센서스
def GetConsensus(code):
    url = 'http://wisefn.stock.daum.net/company/cF1002.aspx?cmp_cd=' + code
    
    while True:
        try:
            f = urllib.request.urlopen(url).read()
        except HTTPError as e:
            # do something
            print('Error code: ', e.code, ' 10초 대기')
            time.sleep(10)
        except URLError as e:
            # do something
            print('Reason: ', e.reason, ' 10초 대기')
            time.sleep(10)
        else:
            # do something
            #print('good!')
            break;
            
    soup = BeautifulSoup(f, 'html.parser')
    
    
    
    # 요청한 종목코드와 결과 페이지의 종목코드가 동일한지 확인
    form = soup.find('form')
    codeInPage = form['action'].split('=')[1]
    
    ##print(codeInPage)
    #return
    
    if code != codeInPage:
        return '요청 code : ' + code + ' , 페이지 code : ' + codeInPage + ' - in GetConsensus()'

    # 다차원 배열 문자열을 찾기 위해 패턴 설정
    p = re.compile("changeCns.*?\;", re.DOTALL)
    cns_list = p.findall(soup.prettify())
    # 불필요한 문자열 제거
    cns_str = cns_list[0].replace('\n','').replace('changeCns = ','').replace(';','')
    cns_str = cns_str.replace('tid', '"tid"').replace('dest', '"dest"') # 딕셔너리 키를 문자열로 변경
    #print(cns_str)
    #return
    
    cns = eval(cns_str)
    
    stock[code].append(cns)      


# 웹 파싱 후 호출해야 된다.
# 재무정보에서 최근 분기 PER를 구한다.
def ReadPER(allStock, code):          
    try:
        '''
        '5' 는 재무정보를 의미
        '3' 은 CAPEX부터 발행주식수 영역을 의미
        '1' 은 분기를 의미
        '10' 은 PER를 의미
        '3' 은 가장 최근 분기를 의미, '2'는 직전 분기 (연환산 데이터임)
        '''
        if allStock[code][5][3][1][10][3] != '':
            return allStock[code][5][3][1][10][3].replace(',','')
        elif allStock[code][5][3][1][10][2] != '':
            return allStock[code][5][3][1][10][2].replace(',','')
    except:
        return None
    
    return None
    
# n년 평균 PER를 구함
def ReadAvgPER(allStock, code, year):
    try:
        per = allStock[code][5][3][0][10][1:] # 4년전부터 작년까지 4개의 PER를 구함
                
        if len(per) != year: # 최근 n년의 PER 데이터가 하나라도 없다면
            return None
            
        for i in range(len(per)):
            if per[i] == '' or per[i] == None:
                return None
            per[i] = float(per[i].replace(',',''))
                    
        #per = [float(i) for i in per]
            
        return sum(per, 0.0) / len(per)
                            
    except:
        print(code, ' - in ReadAvgPER')
        return None
    
# 웹 파싱 후 호출해야 된다.
# 재무정보에서 최근 분기 ROA를 구한다.
def ReadROA(allStock, code):          
    try:
        '''
        '5' 는 재무정보를 의미
        '3' 은 CAPEX부터 발행주식수 영역을 의미
        '1' 은 분기를 의미
        '6' 은 ROA를 의미
        '3' 은 가장 최근 분기를 의미, '2'는 직전 분기
        '''
        if allStock[code][5][3][1][6][3] != '':
            return allStock[code][5][3][1][6][3].replace(',','')
        elif allStock[code][5][3][1][6][2] != '':
            return allStock[code][5][3][1][6][2].replace(',','')
    except:
        return None
    
    return None

# 재무정보에서 특정 항목의 최근 분기값을 구한다.
# 최근 분기값이 공시전이라 표시가 안되는 경우가 있으므로
# 최근 분기값이 없으면 직전 분기 값으로 대체한다.
def ReadItem(allStock, code, item):
    
    ItemIndex = -1
    
    ITEM = item.upper()
    if ITEM == 'ROA':
        ItemIndex = 6
    elif ITEM == 'DEBT':
        ItemIndex = 7
    elif ITEM == 'PBR':
        ItemIndex = 12
    else:
        print('Invalid item : [', item, ']')
        return False
    
    try:
        if allStock[code][5][3][1][ItemIndex][3] != '':
            return allStock[code][5][3][1][ItemIndex][3].replace(',','')
        elif allStock[code][5][3][1][ItemIndex][2] != '':
            return allStock[code][5][3][1][ItemIndex][2].replace(',','')
    except:
        return None
    
    return None

        
if __name__ == "__main__":
    
    # 종목코드를 구한다.
    GetStockCode('P')    # 코스피 
    GetStockCode('Q')    # 코스닥
    
    now = time.localtime()
    # 전체 종목에 대해 웹에서 정보를 가져오는 것은 시간이 많이 소요되고,
    # 해당 서버의 트래픽을 계속 발생시킨다.
    # 시간과 트래픽을 아끼기 위해 전체 파싱을 완료 한 후 파싱 된 데이터를 파일로 저장한다.
    # 파싱 데이터를 저장할 파일명은 날짜 형식으로 한다.
    fileName = ('%04d-%02d-%02d.stock' % (now.tm_year, now.tm_mon, now.tm_mday))
    startTime = ('%02d:%02d:%02d' % (now.tm_hour, now.tm_min, now.tm_sec))
    
    # 에러메시지를 log.txt 파일에 저장한다.
    with open('log.txt', 'a') as f:
        f.write('\n' + fileName + ' ' + startTime + ' start \n')
        for index, code in enumerate(stock): # 전 정목에 대하여 수행
            retMsg = GetPER(code)    # code에 해당하는 PER를 구한다.
            if retMsg != None:       # PER구하기 실패시 로그에 출력
                f.write(retMsg + '\n')
            else:                    # PER를 잘 구했다면
                retMsg = GetFinaceInfo(code)   # 재무정보를 구한다.
                if retMsg != None:             # 재무정보 구하기 실패시 로그에 출력
                    f.write(retMsg + '\n')
                retMsg = GetConsensus(code)     # 추정실적 컨센서스 구한다.
                if retMsg != None:
                    f.write(retMsg + '\n')
            
            # 진행상황 표시
            print(index+1, '/', len(stock) , ' ', code)
            sys.stdout.flush()
            
            # 순간적으로 과도한 트래픽이 발생되지 않도록 쉬어 준다.
            time.sleep(0.1)
                        
        # 파싱 완료
        now = time.localtime()
        endTime = ('%02d:%02d:%02d' % (now.tm_hour, now.tm_min, now.tm_sec))        
        f.write(fileName + ' ' + endTime + ' end \n')
        
    # 파싱 된 정보를 파일로 저장한다.
    with open(fileName,'wb') as f:
        pickle.dump(stock, f)

    '''
    다시 읽어올 때는 요렇게 하면 된다.
    with open('2016-06-17.stock', 'rb') as f:
        stock = pickle.load(f)
    '''


        