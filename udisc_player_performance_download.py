# -*- coding: utf-8 -*-
"""
Created on Thu Jan 21 12:17:25 2021

@author: Ryan
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

options = Options()
options.add_argument('--headless')
options.add_argument("--log-level=3")

# Note other webdrivers use alternate xpaths to the same data.
# Geckodriver (Firefox) and Opera seemed to work consistently,
# but Edge was confirmed to have different paths.

# Change to local webdriver file: https://sites.google.com/a/chromium.org/chromedriver/downloads
ChromeDriver = webdriver.Chrome('C:/Users/Ryan/Downloads/'
                                'chromedriver_win32/chromedriver.exe',
                                options=options)

exception_list = []


def scrape_data(driver, data, iteration_count, year):
    start = time.perf_counter()
    performance_data = pd.DataFrame(columns={'player_link',
                                             'Round & Hole',
                                             'Round Course',
                                             'Round Card',
                                             'Shots',
                                             'Driving',
                                             'CIR',
                                             'Scramble',
                                             'C1X Putting',
                                             'C2 Putting',
                                             'Throw in Distance',
                                             'OB_Penalty'})
    for x in data:
        try:
            tourney_performance = pd.DataFrame(columns={'player_link',
                                                        'Round & Hole',
                                                        'Round Course',
                                                        'Round Card',
                                                        'Shots',
                                                        'Driving',
                                                        'CIR',
                                                        'Scramble',
                                                        'C1X Putting',
                                                        'C2 Putting',
                                                        'Throw in Distance',
                                                        'OB_Penalty'})
            card_round_titles, round_card_number = set_driver(driver, x)
            tourney_performance = scrape_hole_data(driver, card_round_titles, round_card_number, x)
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
        except Exception as e:
            exception_list.append(e)
            exception_list.append(str('Exception in module scrape_data'
                                      + '(driver, data, iteration_count) raised for '
                                      + str(x)
                                      + ' in iteration '
                                      + str(iteration_count)))
            continue
    unique_filename = ('data/udisc_tourney_performance_'
                       + str(year).strip()
                       + '_' + str(iteration_count)
                       + '_' + str(driver.name)
                       + '.csv')
    performance_data.reset_index(drop=True, inplace=True)
    performance_data = performance_data.set_index(keys=['player_link'], drop=False)
    duration = time.perf_counter() - start
    performance_data.to_csv(unique_filename, index=False)
    return(performance_data, duration)


def set_driver(driver, x):
    driver.get(x)
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.XPATH,
                                                 '//*[@id="react-root"]/div/div[2]/'
                                                 'div[3]/div[1]/div/div/div[2]/div[1]/div[1]'))
            )
        card_round_titles = (driver.
                             find_elements_by_xpath('//*[@id="react-root"]/div/div[2]/'
                                                    'div[3]/div[3]/div/div/div[1]/div[1]/a'))
        round_card_number = (driver.find_elements_by_xpath('/html/body/div/div/div[2]/'
                                                           'div[3]/div[3]/div/div/div[1]/div[2]/a'))
        print(f'WebDriver set for {x}.')
    except Exception as e:
        exception_list.append(e)
        exception_list.append(str('Exception in module set_driver(driver, x) raised for' + str(x)))
    return(card_round_titles, round_card_number)


def scrape_hole_data(driver, card_round_titles, round_card_number, x):
    tourney_performance = pd.DataFrame(columns={'player_link',
                                                'Round & Hole',
                                                'Round Course',
                                                'Round Card',
                                                'Shots',
                                                'Driving',
                                                'CIR',
                                                'Scramble',
                                                'C1X Putting',
                                                'C2 Putting',
                                                'Throw in Distance',
                                                'OB_Penalty'})
    for index, round_title in range(len(card_round_titles)):
        card_hole_count = scrape_card_hole_count(driver, index, x)
        for j in range(1, len(card_hole_count)):
            hole_shots_val = scrape_hole_shots(driver, index, j, x)
            hole_driving_val = scrape_hole_driving(driver, index, j, x)
            hole_CIR_val = scrape_hole_CIR(driver, index, j, x)
            hole_scramble_val = scrape_hole_scramble(driver, index, j, x)
            C1X_putting_val = scrape_hole_C1X_putting(driver, index, j, x)
            C2_putting_val = scrape_hole_C2_putting(driver, index, j, x)
            throw_in_dist_val = scrape_hole_throw_in_distance(driver, index,
                                                              j, x)
            OB_penalty_val = scrape_hole_OB_penalty(driver, index, j, x)
            R_n_H_string = 'R'+str(len(card_round_titles)-index)+'_H'+str(j)
            hole_performance = pd.DataFrame({'player_link': x,
                                             'Round & Hole': R_n_H_string,
                                             'Round Course': round_title.text,
                                             'Round Card': round_card_number[index].text,
                                             'Shots': hole_shots_val,
                                             'Driving': hole_driving_val,
                                             'CIR': hole_CIR_val,
                                             'Scramble': hole_scramble_val,
                                             'C1X Putting': C1X_putting_val,
                                             'C2 Putting': C2_putting_val,
                                             'Throw in Distance': throw_in_dist_val,
                                             'OB_Penalty': OB_penalty_val},
                                            index=[0])
            tourney_performance = tourney_performance.append(hole_performance,
                                                             ignore_index=True)
    print(f'Data scraped for {x}.')
    return(tourney_performance)


def scrape_hole_shots(driver, i, j, x):
    hole_shots = (driver.
                  find_elements_by_xpath('//*[@id="react-root"]/div/div[2]/'
                                         'div[3]/div[3]/div['+str(i+1)+']/div/'
                                         'div[2]/div[2]/div/div[1]/div['+str(j+1)+']'))
    if not hole_shots:
        hole_shots_val = None
    elif hole_shots[0].text == '-':
        hole_shots_val = None
    else:
        hole_shots_val = hole_shots[0].text
    print(f'Round {i+1} hole {j} - {x} - Hole shot count scraped.')
    return(hole_shots_val)


def scrape_card_hole_count(driver, i, x):
    card_hole_count = (driver.
                       find_elements_by_xpath('//*[@id="react-root"]/div/div[2]/'
                                              'div[3]/div[3]/div['+str(i+1)+']/div/'
                                              'div[2]/div[1]/div/div/div/div[1]'))
    print(f'Round {i+1} hole-count scraped for {x}.')
    return(card_hole_count)


def scrape_hole_driving(driver, i, j, x):
    hole_driving = (driver.
                    find_elements_by_xpath('//*[@id="react-root"]/div/div[2]/'
                                           'div[3]/div[3]/div['+str(i+1)+']/div/'
                                           'div[2]/div[2]/div/div[2]/div[1]/div['+str(j+1)+']/i'))
    if not hole_driving:
        hole_driving_val = None
    else:
        hole_driving_val = hole_driving[0].get_attribute('title')
    print(f'Round {i+1} hole {j} - {x} - Hole driving data scraped.')
    return(hole_driving_val)


def scrape_hole_CIR(driver, i, j, x):
    hole_CIR = (driver.
                find_elements_by_xpath('//*[@id="react-root"]/div/div[2]/'
                                       'div[3]/div[3]/div['+str(i+1)+']/div/'
                                       'div[2]/div[2]/div/div[2]/div[2]/'
                                       'div['+str(j+1)+']/i'))
    if not hole_CIR:
        hole_CIR_val = None
    else:
        hole_CIR_val = hole_CIR[0].get_attribute('title')
    print(f'Round {i+1} hole {j} - {x} - Hole CIR data scraped.')
    return(hole_CIR_val)


def scrape_hole_scramble(driver, i, j, x):
    hole_scramble = (driver.
                     find_elements_by_xpath('//*[@id="react-root"]/div/div[2]/'
                                            'div[3]/div[3]/div['+str(i+1)+']/div/'
                                            'div[2]/div[2]/div/div[2]/div[3]/'
                                            'div['+str(j+1)+']/i'))
    if not hole_scramble:
        hole_scramble_val = None
    else:
        hole_scramble_val = hole_scramble[0].get_attribute('title')
    print(f'Round {i+1} hole {j} - {x} - Hole scramble data scraped.')
    return(hole_scramble_val)


def scrape_hole_C1X_putting(driver, i, j, x):
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
    print(f'Round {i+1} hole {j} - {x} - Hole C1X putting data scraped.')
    return(C1X_putting_val)


def scrape_hole_C2_putting(driver, i, j, x):
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
    print(f'Round {i+1} hole {j} - {x} - Hole C2 putting data scraped.')
    return(C2_putting_val)


def scrape_hole_throw_in_distance(driver, i, j, x):
    hole_throw_in_distance = (driver.
                              find_elements_by_xpath('//*[@id="react-root"]/div/div[2]/'
                                                     'div[3]/div[3]/div['+str(i+1)+']/'
                                                     'div/div[2]/div[2]/div/div[2]/'
                                                     'div[6]/div['+str(j+1)+']'))
    if not hole_throw_in_distance:
        throw_in_dist_val = None
    else:
        throw_in_dist_val = hole_throw_in_distance[0].text
    print(f'Round {i+1} hole {j} - {x} - Hole throw-in-distance scraped.')
    return(throw_in_dist_val)


def scrape_hole_OB_penalty(driver, i, j, x):
    hole_OB_penalty = (driver.
                       find_elements_by_xpath('//*[@id="react-root"]/div/div[2]/'
                                              'div[3]/div[3]/div['+str(i+1)+']/div/'
                                              'div[2]/div[2]/div/div[2]/div[7]/'
                                              'div['+str(j+1)+']/i'))
    if not hole_OB_penalty:
        OB_penalty_val = False
    else:
        OB_penalty_val = True
    print(f'Round {i+1} hole {j} - {x} - Hole OB Penalty data scraped.')
    return(OB_penalty_val)


def main():
    tourney_player_data = pd.read_csv('data/udisc_tourney_player_data_all_years.csv')
    year = input('What year would you like to scrape? Enter here:')
    tourney_player_data_filtered = (tourney_player_data[
        tourney_player_data['tourney_link'].str.contains(year)])
    performance_data = pd.DataFrame(columns={'player_link',
                                             'Round & Hole',
                                             'Round Course',
                                             'Round Card',
                                             'Shots',
                                             'Driving',
                                             'CIR',
                                             'Scramble',
                                             'C1X Putting',
                                             'C2 Putting',
                                             'Throw in Distance',
                                             'OB_Penalty'})
    duration_log = []
    iterations = int(len(tourney_player_data_filtered)/300.0)+1
    for i in range(iterations):
        full_round_data = tourney_player_data_filtered['player_link'][300*i:300*(i+1)-1]
        result, duration = scrape_data(ChromeDriver, full_round_data, i, year)
        performance_data = performance_data.append(result, ignore_index=True)
        duration_log.append(duration)
    merge_excel_iterated_outputs()


def merge_excel_iterated_outputs():
    complete_dataset = pd.DataFrame(columns={'player_link',
                                             'Round & Hole',
                                             'Round Course',
                                             'Round Card',
                                             'Shots',
                                             'Driving',
                                             'CIR',
                                             'Scramble',
                                             'C1X Putting',
                                             'C2 Putting',
                                             'Throw in Distance',
                                             'OB_Penalty'})
    years = ['2016', '2017', '2018', '2019', '2020', '2021']
    for j in years:
        i = 0
        while i > -1:
            try:
                more_data = pd.read_csv('data/udisc_tourney_performance_'
                                        + j + '_'
                                        + str(i)
                                        + '_chrome.csv')
                complete_dataset = complete_dataset.append(more_data, ignore_index=True)
                i += 1
            except Exception:
                i = -2
    complete_dataset.reset_index(inplace=True, drop=True)
    complete_dataset.to_csv('data/complete_udisc_performance_data_18.19.20.csv')


if __name__ == '__main__':
    main()
