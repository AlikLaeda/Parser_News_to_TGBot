# 
# Модуль парсит новостной сайт regions.ru - вытаскивает 
# новости с первой страницы раздела "новости" заданного
# города.
#
# Новости сохраняются списком в json-файл, чтобы 
# не повторяться. Чтобы не пропускать новости надо 
# запускать модуль не реже раза в день.

import requests
from bs4 import BeautifulSoup
import json
import time
import re

# список слов, если статья не содержит, хотя бы одного из них,
# то она не пройдёт дальше в результат поиска. В список старых 
# статей попадёт.
# Использовать только нижний регистр. 
# Случайное положительное срабатывание приемлемо.
word_list=[
    'ВСТАСТАВИТЬ'
]


# Функция преобразует дату из строки со словами "Сегодня" и "Вчера"
# или вида ДД.ММ, 
# а ещё время вида ЧЧ:ММ 
# в дату-время в секундах с начала эпохи.
# Устанавливается год даже если сегодня январь, а новость декабрьская.
#
def str_to_time(time_str):
    print(time_str)
    if time_str.count('назад'):
        current_day = time.mktime(time.localtime())
        current_day -= time.localtime(current_day).tm_sec
        date = current_day - (int(time_str[:2]) * 60)

        
    else:
        # Записываем текущее время в секундах и вычитаем время от начала
        # суток, чтобы было время 00:00:00
        current_day = time.mktime(time.localtime())
        current_day -= time.localtime(current_day).tm_hour * 3600
        current_day -= time.localtime(current_day).tm_min * 60
        current_day -= time.localtime(current_day).tm_sec
    #    curr_yday = (time.localtime().tm_yday - 1) * 86400

        # Если вместо даты стоят слова "Сегодня" или "Вчера" то
        # присваиваем секунды сего или вчерашнего дня.
        if time_str.count('Сегодня'):
            date = current_day
        elif time_str.count('Вчера'):
            date = current_day - 86400
    #        date = time.strftime("%d.%m ", time.gmtime(current_day - 86400))

        # Если стоит дата, то высчитываем и присваиваем секунды дня года из
        # даты вида 'ДД.ММ' из начала строки. Пока без года.
        else:
            date = (time.strptime(time_str[:5], '%d.%m').tm_yday - 1) * 86400
    #        time.mktime(time.strptime("2024", '%Y'))

            # Если сейчас январь, а статья декабрьская, то прибавляем секунды 
            # прошлого года.
            if (time_str[3:5] == '12') & (time.localtime(current_day).tm_mon == 1):
                current_year = time.localtime(current_day).tm_year
                date += time.mktime(time.strptime(str(current_year - 1), '%Y'))
                
            # А обычно прибавляем секунды этого года.
            else:
                current_year = time.localtime(current_day).tm_year
                date += time.mktime(time.strptime(str(current_year), '%Y'))

        # Время вида ЧЧ:ММ из конца строки пересчитываем в секунды и прибавляем.         
        date += (int(time_str[-5:-3]) * 3600) + (int(time_str[-2:]) * 60)
    return date
#    


# Основная функция модуля принимает string название города 
# латиницей, из адресной строки сайта. На выходе - dict 
# новостей с ключами из уникальных индетификаторов сайта
# и словарём:
# Дата и время.
# Название новости.
# Категория.
# Ссылка на статью.
# Ссылка на картинку.
# Текст статьи.
# Автор
# Фотограф
#

def parse_regions_ru(sity):
    # В articles_regions_ru.json сохранены все имеющиеся новости за последнее время 
    # забираем оттуда всю инфу в список.
    try:
        with open("articles_regions_ru.json", "r", encoding="utf-8") as f:
            dict_of_articles = json.load(f)
    # или создаём такой список, если файла нет. 
    except FileNotFoundError:
        dict_of_articles = {}

# Удаляем из словаря новости старше 30 дней (примерно, без учёта часовых поясов)
    Older_news = []
    for One_news in dict_of_articles:
#        if time.time() - time.mktime(time.strptime(One_news["article_date"], '%d.%m.%Y')) > 2592000:
        if time.time() - dict_of_articles[One_news]["date"] > 2592000:
        # Из словаря нельзя удалять записи, пока он в for'е, а то наступит неожиданный конец.
        # Сохраняем удаляемые новасти в специальный список.
            Older_news.append(One_news)
    # И только теперь удаляем.
    for One_news in Older_news:
        dict_of_articles.pop(One_news)

    # Словарь только для новых новостей 
    fresh_dict = {}

    # Делаем запрос к сайту и варим из ответа суп.
    url = "https://regions.ru/"+sity+"/news"
    response = requests.get(url)
#    print(response.status_code)
    soup = BeautifulSoup(response.text, 'lxml')
    # Находим удаляем тэг, внутри которого тэги и классы 
    # с именами такими же как искомые    
    soup.find('div', class_='zone-left').decompose()
    # Находим все статьи на странице
    articles = soup.find_all("div", class_="story article")
    for art in articles:
        a_link = 'https://regions.ru' + art.find("a", class_="headline").get("href")
        a_name = a_link.split('/')[-1]
        if a_name in dict_of_articles:
            continue
        else:
            a_date = str_to_time(art.find("div", class_="update").string)
            a_head = art.find("a", class_="headline").string
            a_cat = art.find("a", class_="category").string
            response_i = requests.get(a_link)
            soup_i = BeautifulSoup(response_i.text, 'lxml')
            a_img = soup_i.find("figure").find("img").get("src")
            try:
                a_text = soup_i.find("div", class_="short-desc").get_text()
            except:
                a_text = ''
            a_text = a_text + soup_i.find("div",
                            class_="article news-content news-article").get_text()
            a_text = re.sub(r'\n+.+\n.+\n+.+ \d\d:\d\d\n\s+','',a_text,count=1)
            a_text = re.sub(r'\n+.+\n.+\n+\s+\d+ минут назад\s+','',a_text,count=1)
            a_text = re.sub(r'\n+\s+ Фото: .+\s+',r'\n',a_text,count=0)
            a_text = re.sub(r'\n\s+',r'\n',a_text,count=0)
            try:
                a_author = soup_i.find("div", class_="author").string.replace('Автор:', '', 1).strip()
            except:
                a_author = ''
            try:
                a_author_foto = soup_i.find("figcaption").string.replace('Фото:', '', 1).strip()
            except:
                a_author_foto = ''
            a_dict = {
                'date' : a_date,
                'head' : a_head,
                'category' : a_cat,
                'link' : a_link,
                'image' : a_img,
                'text' : a_text,
                'author' : a_author,
                'author photo' : a_author_foto}
            
            dict_of_articles.update({a_name : a_dict})
            fresh_dict.update({a_name : a_dict})
# Сохраняем словарь всех новостей обратно в файл                
    with open("articles_regions_ru.json", "w", encoding="utf-8") as file:
        json.dump(dict_of_articles, file, indent=4, ensure_ascii=False) 

# Возвращаем словарь свежих новостей
    return fresh_dict
        
        




if __name__ == "__main__":
    parse_regions_ru("kotelniki")
##    print(time.localtime(str_to_time("45 минут назад")))
##    print(time.localtime(str_to_time("Сегодня в 00:03")))
##    print(time.localtime(str_to_time("Вчера в 11:28")))
##    print(time.localtime(str_to_time("19.02 в 23:40")))

    

    
