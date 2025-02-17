#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests, time, socket
from bs4 import BeautifulSoup
from collections import defaultdict
from .urls import base_url, details


def is_connected(server='www.google.com'):
    try:
        host = socket.gethostbyname(server)
        socket.create_connection((host, 80), 2)
        return True
    except:
        return False


def get_tz_offset():
    offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
    return offset / 60 / 60 * -1


def get_livescores_url(name, type):
    tz_offset = get_tz_offset()
    url = details.get(type).get(name).get('url') + f'/?tz={tz_offset}'
    return url


def get_soup(name='bpl', event_type='competition'):
    url = get_livescores_url(name, event_type)
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'html.parser')
    return soup


def get_match_id(url):
    res = 0
    for e in url.split('/'):
        if e.isdigit():
            res = int(e.strip())
    return res


'''
    returns a dict of games;
    key: date, value: list of match


    games = {
        'December 30, 2022':
        [
            {
                'match_status': 'FT',
                'home_team': 'Chelsea',
                'away_team': 'Liverpool',
                'home_score': '0',
                'away_score': '0',
            }
        ]
    }
'''

def parse_games(soup):
    sp = soup.find('div', 'xb').find_all('div', recursive=False)

    games = defaultdict(list)
    date = ''

    for line in sp:
        if line.get('class') == ['bb']:
            date = line.find('span', 'cb').text.strip()
        else:
            spp = line.find_all(lambda tag: tag.name == 'a' and tag.get('class') == ['qd'])
            spp = [k for k in spp if k.find('span', 'Kg') is not None]
            match = {}

            for l in spp:
                match_details_url = l.get('href')
                match_id = get_match_id(match_details_url)

                mst = l.find('span', attrs={'data-testid': f'match_row_time-status_or_time_{match_id}'}).text
                ht = l.find('span', attrs={'data-testid': f'football_match_row-home_team_{match_id}'}).text
                hts = l.find('span', attrs={'data-testid': f'football_match_row-home_score_{match_id}'}).text
                at = l.find('span', attrs={'data-testid': f'football_match_row-away_team_{match_id}'}).text
                ats = l.find('span', attrs={'data-testid': f'football_match_row-away_score_{match_id}'}).text

                match = {
                    'match_status': mst,
                    'home_team': ht,
                    'home_score': int(hts) if hts.isdigit() else hts,
                    'away_team': at,
                    'away_score': int(ats) if ats.isdigit() else ats,
                    'match_details_url': base_url + match_details_url
                }
            games[date].append(match) if date and match else None
    return games


def get_games(name='bpl', event_type='competition'):
    soup = get_soup(name, event_type)
    games = parse_games(soup)
    return games


'''
    returns a list of rows, which is a list of table elements;

    table = [['LP', '', 'Team Name', 'GP', 'W', 'D', 'L', 'GF', 'GA', 'GD', 'Pts']
    ['1', 'Champions League', 'Arsenal', '19', '16', '2', '1', '45', '16', '29', '50']
    ['2', 'Champions League', 'Manchester City', '20', '14', '3', '3', '53', '20', '33', '45']
    ['3', 'Champions League', 'Newcastle United', '20', '10', '9', '1', '33', '11', '22', '39']
    ...]

'''
def parse_table(soup):
    lt = soup.find('div', attrs={'data-testid': 'league_table-container'})
    body = lt.find('tbody')
    
    header = ['LP', '', 'Team Name', 'GP', 'W', 'D', 'L', 'GF', 'GA', 'GD', 'Pts']
    table = []
    table.append(header)
    for l in body.find_all('tr'):
        temp = l.find_all(text=True)
        if not l.find('span', attrs={'class': 'wj'}):
            temp.insert(1, '')
        table.append(temp)
    
    return table


def get_table(name, event_type='competition'):
    soup = get_soup(name, event_type)
    table = parse_table(soup)
    return table