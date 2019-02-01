# -*- coding: utf-8 -*-
"""
Created on Thu Jun 16 17:07:39 2016

@author: http://cafe.naver.com/rebalancer
"""

import AllStock as ast
import pickle
from pandas import Series, DataFrame
import locale


def CalMF(fileDate):

    MV = 1000   # 시총 (단위 억)
    with open(fileDate + '.stock','rb') as f:
        stock = pickle.load(f)
    
    code = []   # 스크래핑 데이터에서 조건에 맞는 코드를 저장할 리스트를 준비
    per = []    # 스크래핑 데이터에서 조건에 맞는 'PER'를 저장할 리스트를 준비
    roa = []    # 스크래핑 데이터에서 조건에 맞는 'ROA'를 저장할 리스트를 준비
        
    for cd in stock:    
        if len(stock[cd]) < 6:   # PER,ROA,컨센서스 구하기 실패한 경우
            continue
                
        try:
            # 시가총액이 2000억 미만이면 패스
            # 발생주식수 단위는 천
            if int(stock[cd][3]) * int(stock[cd][5][3][1][16][3].replace(',', '')) < MV * 100000:
                # print(cd, stock[cd][0], '시가총액 1000억 미만')
                continue
            
            # 적자기업은 제외
            if stock[cd][4] <= 0:
                # print(cd, stock[cd][0], 'per : ', stock[cd][4], '적자기업 제외')
                continue
            
            '''
            # 부채 비율 150% 이상은 제외
            if float(ast.ReadItem(stock, code, 'debt')) >= 80:
                continue
            
            # ROA 40% 이상은 제외 (일시적인 이익일 가능성이 높다.)
            if float(ast.ReadROA(stock, cd)) >= 30.0:
                continue
            '''            
                            
            # PER는 연환산으로 하는 것이 맞다면 
            #readPER = ast.ReadPER(stock, cd)
            
            # 최근 결산 
            readPER = stock[cd][4]
            
            readROA = ast.ReadROA(stock, cd)
            
            # PER나 ROA값이 없다면 패스
            if readPER == None or readROA == None:
                continue
            
            code.append(cd)
            per.append(float(readPER))
            roa.append(float(readROA))
        except: # 주식수가 없는 경우 있다.
            # print(cd, ' 현재가 or 주식수 오류')    
            pass
            
    # 마법공식 순위 구하기
            
    # PER 순위를 구한다.        
    per_rank = Series(per, index=code).rank(method='min')
    # ROA 순위를 구한다.
    roa_rank = Series(roa, index=code).rank(method='min',ascending=False)
    # PER와 ROA 순위를 합산하여 매직공식 순위를 구한다.
    mf_rank = (per_rank + roa_rank).sort_values() # magicFormula
    
    # 자료를 좀 더 편하게 보기 위하여 DataFrame 형태로 변경 한다.
    # index : '마법공식순위'
    # column : '종목명', '종목코드', 'PER(순위)', 'ROA(순위'), '시장', '업종', '합산점수')
    col_name = []       # '종목명' 컬럼을 위해 리스트 준비
    col_cd = []         # '종목코드' 컬럼을 위해 리스트 준비
    col_price = []      # '주가' 컬럼을 위해 리스트 준비
    col_per_rank = []   # 'PER(순위)' 컬럼을 위해 리스트 준비
    col_roa_rank = []   # 'ROA(순위)' 컬럼을 위해 리스트 준비
    col_market = []     # '시장' 컬럼을 위해 리스트 준비
    col_field = []      # '업종' 컬럼을 위해 리스트 준비
    col_sum = []        # '합산점수' 컬럼을 위해 리스트 준비
    
    row_mf_rank = []    # '마법공식순위' ROW를 위해 리스트 준비
    
    for index, cd in enumerate(mf_rank.index):  # 마법공식 순위 순서대로 루프를 돈다.    
        # print(cd, index)
        row_mf_rank.append(index+1)
        
        col_name.append(stock[cd][0])
        col_cd.append(cd)  
        col_price.append(locale.format("%d", (int)(stock[cd][3]), 1))
        col_per_rank.append(format('%.2f(%.0f)'%(stock[cd][4], per_rank[cd])))
        col_roa_rank.append(format('%s(%.0f)'%(ast.ReadROA(stock, cd), roa_rank[cd])))
        col_market.append(stock[cd][1])
        col_field.append(stock[cd][2])
        col_sum.append(int(mf_rank[cd]))
    
    raw_data = {'종목명':col_name, '종목코드':col_cd, '주가':col_price,
    'PER(순위)':col_per_rank, 'ROA(순위)':col_roa_rank, '시장':col_market,
    '업종':col_field, '순위합산':col_sum}
    
    result = DataFrame(raw_data, 
    columns=['종목명','종목코드','주가','PER(순위)','ROA(순위)','시장','업종','순위합산'], 
    index=row_mf_rank)
        
    return (result, stock)

# 1. border = 0
# 2. 첫 번째 tr align center 
# 3. 첫 번째 tr bgcolor = '#AAFFAA' 추가

'''
maxROA = 0.0
for cd in stock:
    nowROA = float(ast.ReadROA(stock, cd))
    if nowROA > maxROA:
        maxROA = nowROA
        print(cd, maxROA)
'''
if __name__ == "__main__":
    
    locale.setlocale(locale.LC_ALL, '') 
    
    oldDate = '2018-09-07'
    newDate = '2018-09-14'
    
    resultOld, stockOld = CalMF(oldDate)    

    result,stock = CalMF(newDate)
    
    updown = [] # 등락 순위

    for index, newcd in enumerate(result['종목코드']):
        
        # 이전 순위에 있었는지 체크, 없었으면 'NEW'
        if len(resultOld['종목코드'][resultOld['종목코드'] == newcd]) == 0:
            updown.append('NEW')
        else:
            # 이전 순위 찾기
            oldIndex = resultOld['종목코드'][resultOld['종목코드'] == newcd].index[0] - 1
            updown.append(oldIndex - index)

    # HTML로 저장  
    result['등락'] = updown  
    result.ix[1:100].to_html(newDate + '.rank.html')
    
    
    # table border = 0, 
    # 제목 tr bgcolor="#AAFFAA", align=center
    
    
    '''
    topN = 20
    
    print('---- 종목명 ----')
    for n in result[0:topN]['종목명']:
        print(n)
        
    print('---- 종목코드 ----')    
    for c in result[0:topN]['종목코드']:
        if stock[c][1] == 'P':
            print('KRX:%s'%c)
        else:
            print('KOSDAQ:%s'%c)
    '''            
    
        
