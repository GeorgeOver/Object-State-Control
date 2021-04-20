import os
import time
import classification
import process_video
import sys
import argparse
import cloud_controller
from config_reader import readConfig
from config_reader import ConfigReadError

#
#Basic config (dir names and logging debug mode ON/OFF)
#
OUTPUT_PATH              = 'output/'
LOG_PATH                 = 'logs/'
TEMP_PATH                = 'temp/'
ORIGINAL_CUTS_PATH       = 'original_cuts'
ORIGINAL_CUTS_DAY_PATH   = 'original_cuts/day'
ORIGINAL_CUTS_NIGHT_PATH = 'original_cuts/night'
LOGGING                  = True
if LOGGING:
    log_string = ''

#
#Read arguments from command line
#
parser = argparse.ArgumentParser()
parser.add_argument("--config", help = "Path of the input config", required=False, default='config.txt')
args = parser.parse_args()
config = args.config

#
#Read config file
#
try:    
    arguments   = readConfig(config)
    print('[INF] Введены данные: ' + str(arguments))
    if LOGGING:
        log_string = log_string + 'Input: ' + str(arguments) + '\n'
    camera_id        = arguments[0]
    video            = arguments[1]
    crops            = arguments[2]
    obj_ids          = arguments[3]
    hotel_id         = arguments[4]
    state_0_list     = arguments[5]
    state_1_list     = arguments[6]
    cloud_public_key = arguments[7]
    cloud_secret_key = arguments[8]
    bucket           = arguments[9]
    local_output     = arguments[10]
    cloud_output     = arguments[11]
    min_duration     = arguments[12]
    max_duration     = arguments[13]
    ch_id            = arguments[14]
    debug_mode       = arguments[15] 
    post_enable      = arguments[16]
    post_auth        = arguments[17]
    post_url         = arguments[18]
    at_mr_top        = arguments[19]
    at_mr_bot        = arguments[20]
    maxr_midr        = arguments[21]
    midr_minr        = arguments[22]
    at_add_step      = arguments[23]
    at_sub_step      = arguments[24]
    cap_new_states   = arguments[25]
    obj_types_list   = arguments[26]
    event_types_list = arguments[27]
    out_video_format = arguments[28]
    adaptive_mode    = arguments[29]
    fixed_th         = arguments[30]
    og_max           = arguments[31]
except ConfigReadError as e:
    if LOGGING:
        log_string = log_string + 'Read config error: ' + str(e) + '\n'
        process_video.outputLog(LOG_PATH + 'error/log_' + str(time.time()) + '.txt', log_string, None, None, True, False)
    sys.exit('[ERR] Ошибка во время чтения конфиг файла: ' + str(e))
if len(crops) != len(obj_ids) or len(state_0_list) != len(obj_ids) or len(state_1_list) != len(obj_ids):
    sys.exit('[ERR] Неправильно заполнен конфиг файл')


#
#Configuration (cloud, checking data format, creating paths, etc.)
#
cloud_session = None
try:
    cloud_session = cloud_controller.createConnection(cloud_public_key, cloud_secret_key)
except cloud_controller.CloudConnectionFailed as e:
    print('[ERR] Соединение с облаком не установлено')
    if LOGGING:
        log_string = log_string + 'Cloud connection failed\n'

if not os.path.exists(TEMP_PATH):
    os.makedirs(TEMP_PATH)
if not os.path.exists(ORIGINAL_CUTS_PATH):
    os.makedirs(ORIGINAL_CUTS_PATH)
if not os.path.exists(ORIGINAL_CUTS_DAY_PATH):
    os.makedirs(ORIGINAL_CUTS_DAY_PATH)
if not os.path.exists(ORIGINAL_CUTS_NIGHT_PATH):
    os.makedirs(ORIGINAL_CUTS_NIGHT_PATH)
if not os.path.exists(OUTPUT_PATH):
    os.makedirs(OUTPUT_PATH)
if not os.path.exists(LOG_PATH):
    os.makedirs(LOG_PATH)
if not os.path.exists(OUTPUT_PATH + hotel_id):
    os.makedirs(OUTPUT_PATH + hotel_id)
if not os.path.exists(LOG_PATH + hotel_id):
    os.makedirs(LOG_PATH + hotel_id)
if not os.path.exists(OUTPUT_PATH + hotel_id + '/' + camera_id):
    os.makedirs(OUTPUT_PATH + hotel_id + '/' + camera_id)
if not os.path.exists(LOG_PATH + hotel_id + '/' + camera_id):
    os.makedirs(LOG_PATH + hotel_id + '/' + camera_id)
if not os.path.exists(LOG_PATH + hotel_id + '/' + camera_id + '/inputs'):
    os.makedirs(LOG_PATH + hotel_id + '/' + camera_id + '/inputs')
if not os.path.exists(LOG_PATH + 'error'):
    os.makedirs(LOG_PATH + 'error')
for obj_id in obj_ids:
    if not os.path.exists(OUTPUT_PATH + hotel_id + '/' + camera_id + '/' + obj_id):
        os.makedirs(OUTPUT_PATH + hotel_id + '/' + camera_id + '/' + obj_id)
    if not os.path.exists(LOG_PATH + hotel_id + '/' + camera_id + '/' + obj_id):
        os.makedirs(LOG_PATH + hotel_id + '/' + camera_id + '/' + obj_id)

for crop in crops:
    if len(crop) != 4:
        if LOGGING:
            log_string = log_string + 'Invalid coordinates\n'
            process_video.outputLog(LOG_PATH + 'error/log_' + str(time.time()) + '.txt', log_string, cloud_session, bucket, local_output, cloud_output)
        sys.exit('[ERR] Неправильно введены координаты объекта. Должно быть 4 координаты: Ymin Ymax Xmin Xmax')
    for coordinate in crop:
        if int(coordinate) < 0:
            if LOGGING:
                log_string = log_string + 'Invalid coordinates\n'
                process_video.outputLog(LOG_PATH + 'error/log_' + str(time.time()) + '.txt', log_string, cloud_session, bucket, local_output, cloud_output)
            sys.exit('[ERR] Как минимум одна координата не равна целому положительному числу.')   
    if int(crop[0]) > int(crop[1]) or int(crop[2]) > int(crop[3]):
        if LOGGING:
            log_string = log_string + 'Invalid coordinates\n'
            process_video.outputLog(LOG_PATH + 'error/log_' + str(time.time()) + '.txt', log_string, cloud_session, bucket, local_output, cloud_output)
        sys.exit('[ERR] Неправильно введены координаты объекта. Должно быть 4 координаты: Ymin Ymax Xmin Xmax')
if not os.path.exists('temp'):
    os.makedirs('temp')
if min_duration > max_duration:
    if LOGGING:
        log_string = log_string + 'Invalid duration\n'
        process_video.outputLog(LOG_PATH + 'error/log_' + str(time.time()) + '.txt', log_string, cloud_session, bucket, local_output, cloud_output)
    sys.exit('[ERR] Max_duration < min_duration?')

if LOGGING:
    process_video.outputLog(LOG_PATH + hotel_id + '/' + camera_id + '/inputs/log_' + str(time.time()) + '.txt', log_string, cloud_session, bucket, local_output, cloud_output)


#
#Run main process cycle
#
print('[INF] Начало работы с видеопотоком "' + video + '"')
try:
    process_video.processVideoStream(video, crops, camera_id, obj_ids, hotel_id, state_0_list, state_1_list, cloud_session, bucket, local_output, cloud_output, min_duration, max_duration, ch_id, debug_mode, post_enable, post_auth, post_url, at_mr_top, at_mr_bot, maxr_midr, midr_minr, at_add_step, at_sub_step, cap_new_states, obj_types_list, event_types_list, out_video_format, adaptive_mode, fixed_th, og_max)
except process_video.VideoCaptureError as VCE:
    print('[ERR] Ошибка при подключение к видеопотоку (проверьте корректность введенных данных): ' + str(VCE))
    sys.exit()
except classification.ImageClassificationError as ICE:
    print('[ERR] Ошибка работы классификатора: ' + str(ICE))
    sys.exit()
except KeyboardInterrupt:
    print('[OK] Программа завершена с помощью Ctrl + C')
    sys.exit()
print('[OK] Программа завершена')
sys.exit()


    

