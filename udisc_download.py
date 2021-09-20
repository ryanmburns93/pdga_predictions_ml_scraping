# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
import pandas as pd

options = Options()

driver = webdriver.Chrome('C:/Users/Ryan/Downloads/'
                          'chromedriver_win32/chromedriver.exe', options=options)

# Scrape tourney info for each year
tourney_data = pd.DataFrame(columns={'year',
                                     'tourney_name',
                                     'tourney_location',
                                     'month',
                                     'dates',
                                     'tourney_link'})

base_url = 'https://udisclive.com/'
years = ['2016', '2017', '2018', '2019', '2020']
for x in years:
    tourney_data_temp1 = pd.DataFrame(columns={'year',
                                               'tourney_name',
                                               'tourney_location',
                                               'month',
                                               'dates',
                                               'tourney_link'})
    driver.get(base_url + '?y=' + x)
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//td//a'))
            )
        tourney_info_temp = driver.find_elements_by_xpath('/html/body/div/div/div[2]/div[2]/div/div[3]/table/tbody/tr/td[2]')
        tourney_location_temp = (driver.find_elements_by_css_selector("div[style='font-size: 10px; margin-top: 2px; font-weight: 300; color: rgb(68, 68, 68);']"))
        tourney_link_list = driver.find_elements_by_xpath('/html/body/div/div/div[2]/div[2]/div/div[3]/table/tbody/tr/td[2]/a')
        tourney_link_temp = []
        link_counter = 0
        for j in range(1, len(tourney_info_temp)):
            if 'href' in tourney_info_temp[j].get_attribute('innerHTML'):
                tourney_link_temp.append(tourney_link_list[link_counter].get_attribute('href'))
                link_counter += 1
            else:
                tourney_link_temp.append('None')
        tourney_month_temp = (driver.
                              find_elements_by_xpath('/html/body/div/div/div[2]/div[2]/div/div[3]/table/tbody/tr/td[3]/div[1]'))
        tourney_dates_temp = (driver.
                              find_elements_by_xpath('/html/body/div/div/div[2]/div[2]/div/div[3]/table/tbody/tr/td[3]/div[2]'))
        for i in range(len(tourney_info_temp)-1):
            info_list = tourney_info_temp[i+1].text.split('\n')
            if len(info_list) == 3:
                tourney_name_val = info_list[1]
            else:
                tourney_name_val = info_list[0]
            tourney_data_temp2 = pd.DataFrame({'year': x,
                                               'tourney_name': tourney_name_val,
                                               'tourney_location': tourney_location_temp[i].text,
                                               'month': tourney_month_temp[i].text,
                                               'dates': tourney_dates_temp[i].text,
                                               'tourney_link': tourney_link_temp[i]},
                                              index=[0])
            tourney_data_temp1 = tourney_data_temp1.append(tourney_data_temp2)
    except Exception as e:
        print('Exception or error raised in year-level scraper for ' + x)
        raise e
    tourney_data = tourney_data.append(tourney_data_temp1)

tourney_data.reset_index(drop=True, inplace=True)

# Export tourney_data in case of system crash
tourney_data.to_csv('data/udisc_tourney_data_all_years.csv', index=False)

# Scrape player info from each tournament
player_data = pd.DataFrame(columns={'player_name',
                                    'player_gender',
                                    'player_finishing_place',
                                    'player_link',
                                    'tourney_round_count',
                                    'tourney_link'})

tourney_url_caps = ['?t=playerStats&stats=all&d=MPO',
                    '?t=playerStats&stats=all&d=FPO']
for link in tourney_data['tourney_link']:
    if link == 'None':
        player_data_temp = pd.DataFrame({'player_name': 'None',
                                         'player_gender': 'None',
                                         'player_finishing_place': 'None',
                                         'player_link': 'None',
                                         'tourney_round_count': 0,
                                         'tourney_link': link}, index=[0])
        player_data = player_data.append(player_data_temp)
    else:
        for url_cap in tourney_url_caps:
            driver.get(x + url_cap)
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH,
                                                         '//*[@id="main-content"]/div/'
                                                         'div[2]/div/div[2]/a'))
                    )
                player_info_temp = (driver.
                                    find_elements_by_xpath('//*[@id="main-content"]/div/div[2]/div/div[2]/a'))
                player_finish_temp = (driver.find_elements_by_xpath('/html/body/div/div/div[2]/div[2]/div/div[2]/div/div[1]'))
                player_finish_list = []
                for j in range(1, len(player_finish_temp)):
                    try:
                        player_finish_val = player_finish_temp[j].text
                        if len(player_finish_val) == 0:
                            continue
                        else:
                            player_finish_list.append(player_finish_temp[j].text)
                    except StaleElementReferenceException:
                        pass
                tourney_round_counter = (driver.
                                         find_elements_by_xpath('//*[@id="react-root"]/div/div[2]/div[1]/div[1]/div/div[2]/div[4]/div[2]/button'))
                for index, player_info in enumerate(player_info_temp):
                    player_data_temp = pd.DataFrame({'player_name': player_info.text,
                                                     'player_gender': tourney_url_caps[y][0],
                                                     'player_finishing_place': player_finish_list[index],
                                                     'player_link': (player_info.
                                                                     get_attribute('href')),
                                                     'tourney_round_count': len(tourney_round_counter),
                                                     'tourney_link': link}, index=[0])
                    player_data = player_data.append(player_data_temp)
            except Exception as e:
                print('Exception or error raised in tourney-level scraper for ' + link)
                print(e)
                continue

# Kept getting duplicates, could not figure out why...
# bailed and removed duplicates after scrape
player_data.drop_duplicates(inplace=True)
player_data.reset_index(drop=True, inplace=True)
tourney_data = tourney_data.set_index(keys=['tourney_link'])
tourney_player_data = player_data.join(tourney_data,
                                       on=['tourney_link'],
                                       how='left',
                                       lsuffix="_p",
                                       rsuffix="_t")
tourney_player_data.drop_duplicates(inplace=True)
# tourney_player_data.drop(columns={'tourney_link_t', 'tourney_link_p'}, inplace=True)

# Second backup in case of crash
tourney_player_data.to_csv('data/udisc_tourney_player_data_all_years.csv', index=False)

# %%
# sys.exit('Completed scrape through tourney performance')
tourney_player_data = pd.read_csv('C:/Users/Ryan/OneDrive - Northwestern University/Personal/data/udisc_tourney_player_data.csv')

performance_data = pd.DataFrame(columns={'player_link',
                                         'Round & Hole',
                                         'Shots',
                                         'Driving',
                                         'CIR',
                                         'Scramble',
                                         'C1X Putting',
                                         'C2 Putting',
                                         'Throw in Distance',
                                         'OB_Penalty'})

iterations = int(len(tourney_player_data)/300.0)+1

for i in range(iterations):

    # Scrape player round cards for each tourney
    for x in tourney_player_data['player_link'][:300*(i+1)]:
        tourney_performance = pd.DataFrame(columns={'player_link',
                                                    'Round & Hole',
                                                    'Shots',
                                                    'Driving',
                                                    'CIR',
                                                    'Scramble',
                                                    'C1X Putting',
                                                    'C2 Putting',
                                                    'Throw in Distance',
                                                    'OB_Penalty'})
        driver.get(x)
        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH,
                                                     '//*[@id="react-root"]/div/div[2]/'
                                                     'div[3]/div[1]/div/div/div[2]/div[1]/div[1]'))
                )
    # Opted out of scraping tourney-level position and score, can be calculated from collected data
    #        tourney_position_and_score = (driver.
    #                                      find_elements_by_xpath('//*[@id="react-root"]/div/div[2]/'
    #                                                             'div[3]/div[1]/div/div/div[2]/div/'
    #                                                             'div[1]'))
    #        round_scores = (driver.
    #                        find_elements_by_xpath('//*[@id="react-root"]/div/'
    #                                               'div[2]/div[3]/div[1]/div/div/div[3]/div/div[1]'))
    #        tourney_performance_temp = pd.DataFrame(
    #            columns={'Position': tourney_position_and_score[0].text,
    #                     'Total_Score': tourney_position_and_score[1].text})
            card_round_titles = (driver.
                                 find_elements_by_xpath('//*[@id="react-root"]/div/div[2]/'
                                                        'div[3]/div[3]/div/div/div[1]/div[1]/a'))
            for i in range(len(card_round_titles)):
                card_hole_count = (driver.
                                   find_elements_by_xpath('//*[@id="react-root"]/div/div[2]/div[3]/div[3]/div[' +
                                                          str(i+1) +
                                                          ']/div/div[2]/div[1]/div/div/div/div[1]'))
                for j in range(1, len(card_hole_count)):
                    hole_shots = (driver.
                                  find_elements_by_xpath('//*[@id="react-root"]/div/div[2]/div[3]/div[3]/div[' +
                                                         str(i+1) +
                                                         ']/div/div[2]/div[2]/div/div[1]/div[' +
                                                         str(j+1) +
                                                         ']'))

                    if not hole_shots:
                        hole_shots_val = None
                    elif hole_shots[0].text == '-':
                        hole_shots_val = None
                    else:
                        hole_shots_val = hole_shots[0].text
                    hole_driving = (driver.
                                    find_elements_by_xpath('//*[@id="react-root"]/div/div[2]/div[3]/div[3]/div[' +
                                                           str(i+1) +
                                                           ']/div/div[2]/div[2]/div/div[2]/div[1]/div[' +
                                                           str(j+1) +
                                                           ']/i'))
                    if not hole_driving:
                        hole_driving_val = None
                    else:
                        hole_driving_val = hole_driving[0].get_attribute('title')
                    hole_CIR = (driver.
                                find_elements_by_xpath('//*[@id="react-root"]/div/div[2]/div[3]/div[3]/div[' +
                                                       str(i+1) +
                                                       ']/div/div[2]/div[2]/div/div[2]/div[2]/div[' +
                                                       str(j+1) +
                                                       ']/i'))
                    if not hole_CIR:
                        hole_CIR_val = None
                    else:
                        hole_CIR_val = hole_CIR[0].get_attribute('title')
                    hole_scramble = (driver.
                                     find_elements_by_xpath('//*[@id="react-root"]/div/div[2]/div[3]/div[3]/div[' +
                                                            str(i+1) +
                                                            ']/div/div[2]/div[2]/div/div[2]/div[3]/div[' +
                                                            str(j+1) +
                                                            ']/i'))
                    if not hole_scramble:
                        hole_scramble_val = None
                    else:
                        hole_scramble_val = hole_scramble[0].get_attribute('title')
                    hole_C1X_putting = (driver.
                                        find_elements_by_xpath('//*[@id="react-root"]/div/div[2]/'
                                                               'div[3]/div[3]/div['+str(i+1)+']/div/'
                                                               'div[2]/div[2]/div/div[2]/div[4]/'
                                                               'div['+str(j+1)+']'))
                    if not hole_C1X_putting:
                        C1X_putting_val = None
                    elif 'font-weight' in hole_C1X_putting[0].get_attribute('style'):
                        C1X_putting_val = hole_C1X_putting[0].text + ' putt made'
                    else:
                        C1X_putting_val = hole_C1X_putting[0].text
                    hole_C2_putting = (driver.
                                       find_elements_by_xpath('//*[@id="react-root"]/div/div[2]/'
                                                              'div[3]/div[3]/div['+str(i+1)+']/div/'
                                                              'div[2]/div[2]/div/div[2]/div[5]/'
                                                              'div['+str(j+1)+']'))
                    if not hole_C2_putting:
                        C2_putting_val = None
                    elif 'font-weight' in hole_C2_putting[0].get_attribute('style'):
                        C2_putting_val = hole_C2_putting[0].text + ' putt made'
                    else:
                        C2_putting_val = hole_C2_putting[0].text
                    hole_throw_in_distance = (driver.
                                              find_elements_by_xpath('//*[@id="react-root"]/div/div[2]/'
                                                                     'div[3]/div[3]/div['+str(i+1)+']/'
                                                                     'div/div[2]/div[2]/div/div[2]/'
                                                                     'div[6]/div['+str(j+1)+']'))
                    if not hole_throw_in_distance:
                        throw_in_dist_val = None
                    else:
                        throw_in_dist_val = hole_throw_in_distance[0].text
                    hole_OB_penalty = (driver.
                                       find_elements_by_xpath('//*[@id="react-root"]/div/div[2]/'
                                                              'div[3]/div[3]/div['+str(i+1)+']/div/'
                                                              'div[2]/div[2]/div/div[2]/div[7]/'
                                                              'div['+str(j+1)+']/i'))
                    if not hole_OB_penalty:
                        OB_penalty_val = False
                    else:
                        OB_penalty_val = True
                    hole_performance = pd.DataFrame({'player_link': x,
                                                     'Round & Hole': 'R'+str(len(card_round_titles)-i)+'_H'+str(j),
                                                     'Shots': hole_shots_val,
                                                     'Driving': hole_driving_val,
                                                     'CIR': hole_CIR_val,
                                                     'Scramble': hole_scramble_val,
                                                     'C1X Putting': C1X_putting_val,
                                                     'C2 Putting': C2_putting_val,
                                                     'Throw in Distance': hole_throw_in_distance[0].text,
                                                     'OB_Penalty': OB_penalty_val}, index=[0])
                    tourney_performance = tourney_performance.append(hole_performance, ignore_index=True)
                    # convert dtypes of dataframe columns to reduce memory consumption
                    numerical = ['Shots', 'Throw in Distance']
                    categorical = ['Driving', 'CIR', 'Scramble', 'C1X Putting', 'C2 Putting']
                    for col in numerical:
                        tourney_performance[col] = pd.to_numeric(tourney_performance[col],
                                                                 downcast='unsigned')
                    for col in categorical:
                        tourney_performance[col] = tourney_performance[col].astype('category')
                    tourney_performance['OB_Penalty'] = tourney_performance['OB_Penalty'].astype('bool')
            performance_data = performance_data.append(tourney_performance, ignore_index=True)
        except Exception:
            print('Exception or error in player-level scraper raised for ' + x)
            raise Exception
    filename = 'data/udisc_tourney_performance_' + str(i+1)
    performance_data.to_csv(filename, index=False)

# Export a backup before Ryan risks trying to merge/join and ruining frame
performance_data.to_csv('data/udisc_tourney_performance.csv', index=False)

performance_data.reset_index(drop=True, inplace=True)
tourney_player_data = tourney_player_data.set_index(keys=['player_link'], drop=False)

udisc_full_data = performance_data.join(tourney_player_data,
                                        on=['player_link'],
                                        how='left',
                                        lsuffix="_x",
                                        rsuffix="_y")

udisc_full_data.to_csv('data/udisc_full_dataset.csv', index=False)

# %%

complete_dataset = pd.read_csv('data/complete_udisc_performance_data.csv')
tourney_player_data = pd.read_csv('data/udisc_tourney_player_data.csv')

tourney_player_data = tourney_player_data.set_index(keys=['player_link'])

complete_udisc_dataset = complete_dataset.join(tourney_player_data,
                                               on=['player_link'],
                                               how='left',
                                               lsuffix='_x',
                                               rsuffix='_y')

complete_udisc_dataset.to_csv('data/udisc_dataset.csv')
