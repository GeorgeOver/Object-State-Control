import requests
import time

#
#Normalizing data to proper syntaxis and sending post request
#Change data fromat in getTime
#Change syntax in normalize
#Change data in post
#


def getTime():
    timee = str(time.ctime(time.time()))
    print(timee)
    timee = timee.split(' ')
    year = timee[-1]
    t    = timee[-2]
    c    = timee[2].strip()
    if c == '':
        c = timee[3].strip()
    if len(c) == 1:
        c = '0' + c
    mon  = timee[1]
    if mon == 'Jan':
        mon = '01'
    elif mon == 'Feb':
        mon = '02'
    elif mon == 'Mar':
        mon = '03'
    elif mon == 'Apr':
        mon = '04'
    elif mon == 'May':
        mon = '05'
    elif mon == 'Jun':
        mon = '06'
    elif mon == 'Jul':
        mon = '07'
    elif mon == 'Aug':
        mon = '08'
    elif mon == 'Sep':
        mon = '09'
    elif mon == 'Oct':
        mon = '10'
    elif mon == 'Nov':
        mon = '11'
    elif mon == 'Dec':
        mon = '12'
    timee = year + '-' + mon + '-' + c + ' ' + t
    return timee

def normalize_data(auth, hotel_id, cam_id, ch_id, event_time, event_record, event_picture, object_id, object_type_id, event_type_id):
    if object_id.isdigit():
        object_id = int(object_id)
    if object_type_id.isdigit():
        object_type_id = int(object_type_id)
    data_dict = {'auth': auth,
                 'hotel_id': hotel_id,
                 'cam_id': cam_id,
                 'channel_id': ch_id,
                 'event_time': event_time,
                 'event_record': event_record,
                 'event_picture': event_picture,
                 'object_id': object_id,
                 'object_type_id': object_type_id,
                 'event_type_id': event_type_id}
    return data_dict

def sendPostRequest(url, auth, hotel_id, cam_id, ch_id, event_record, event_picture, object_id, object_type_id, event_type_id):
    event_time = getTime()
    data_dict = normalize_data(auth, hotel_id, cam_id, ch_id, event_time, event_record, event_picture, object_id, object_type_id, event_type_id)
    print('[INF] Состав запроса: ' + url + ' ' + str(data_dict)) 
    response = requests.post(url, json=data_dict)
    return response

#data_dict = normalize_data('$2y$10$uzsy1VGyAQ.QuPZKBEfUOeFVJi4/9zV2aP5/JhHL0wxbGL8rxlIGO', '1', '0', 'ch01', '2020-01-29 10:35:07', 's3://doors/01.mp4', 's3://doors/01.jpg')
#print(data_dict)



"""
url = 'https://r.8h.ru/api/event/create.php'
print(url)
t = getTime()
response = sendPostRequest(url, '$2y$10$uzsy1VGyAQ.QuPZKBEfUOeFVJi4/9zV2aP5/JhHL0wxbGL8rxlIGO', '1', '0', 'ch01', 'test', 'test', 1, 1)
print(response)
"""