import scrython
import requests
from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
import asyncio

URL = "https://mtg.wtf"
PAGEURL = "https://mtg.wtf/deck"

def split_list(inputlist:list, separator:str="|"):
    list_1 = []
    list_2 = []
    for item in inputlist:
        separated = item.split(separator)
        list_1.append(separated[0])
        list_2.append(separated[1])
    return list_1, list_2

def check_for_card(url, card):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        for link in soup.find_all('a'):
            if card.lower() in link.text.strip().lower():
                return True
    return False

def get_card_from_precon(mainurl, edition, card):
    results = []
    response = requests.get(mainurl)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        target_div = soup.find('div', string=lambda text: text and edition in text)
        if target_div:
            links = []
            for sibling in target_div.find_next_siblings():
                if sibling.name == 'div':
                    break
                if sibling.name == 'ul':
                    links.extend(sibling.find_all('a'))

            result = [link.text.strip() + "|" + URL + link['href'] for link in links]
            
            for item in result:
                name, link = item.split("|")
                if check_for_card(link, card):
                    results.append(f"{edition}|{name}")
    else:
        st.error("Failed to fetch the webpage")
    return results

def get_or_create_eventloop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError as ex:
        if "There is no current event loop in thread" in str(ex):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return asyncio.get_event_loop()
        
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

cardname = st.text_input("Card name:")
btnsearch = st.button("Search")

if btnsearch and cardname != "":
    data = scrython.cards.Search(q="++{}".format(cardname))

    results = []
    for card in data.data():
        results.append(f"{card['set'].upper()}|{card['set_name']}")

    results = unique_values = list(set(results))

    abb_lst, name_lst = split_list(results)

    all_results = []
    for val in abb_lst:
        res = get_card_from_precon(PAGEURL, val, cardname)
        all_results.extend(res)

    results_dict = {}
    for result in all_results:
        key = result[:3]
        if key in results_dict:
            results_dict[key].append(result)
        else:
            results_dict[key] = [result]

    merged_list = []
    for item in results:
        key = item[:3]
        if key in results_dict:
            results = results_dict[key]
            merged_list.extend([f"{item}|{result.split('|')[1]}" for result in results])
        else:
            merged_list.append(item)

    merged_list_sorted = sorted(merged_list)

    split_result = [item.split('|') for item in merged_list_sorted]

    df = pd.DataFrame(split_result)

    st.data_editor(df, hide_index=True, use_container_width=True)

        