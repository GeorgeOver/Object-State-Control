import numpy as np
import cv2
import classification
import time
import os
import cloud_controller
from post_request import sendPostRequest

#
#Basic config
#Initialize starting data for middle value for adaptive algorythm (in classification.py)
#Number of crop iterations (when DAY changing to NIGHT for first time, need to crop CLOSED door, iterations make sure it closed for the number of iterations)
#Frequency of logging
#Paths
#Calibration time needed for adaptive threshold calibration
#Buffer capacity neede to avoid some wrong cases 
#Crop threshold needed when camera mode switches for first time to make crop in start state
#
DEFAULT_MIN_THRESHOLD    = 6
DEFAULT_MAX_THRESHOLD    = 18
DEFAULT_MID_RESULT       = [350, 50] #first el: sum of all elements, second el = number of element; mid res = 350/50=7
SETTING_CROP_ITERATIONS  = 5
FIRST_CUT_PATH           = 'main_original.jpg'
TEMP_ORIGINAL_PATH       = 'temp_1.jpg'
TEMP_CURRENT_PATH        = 'temp_2.jpg'
OUTPUT_PATH              = 'output/'
LOG_PATH                 = 'logs/'
TEMP_PATH                = 'temp/'
ORIGINAL_CUTS_DAY_PATH   = 'original_cuts/day'
ORIGINAL_CUTS_NIGHT_PATH = 'original_cuts/night'
MIN_FRAMES_OUTPUT        = 65
MAX_FRAMES_OUTPUT        = 300
CALIBRATION_TIME         = 20 #seconds
SETTING_CROP_THRESHOLD   = 0.7
DAY_NIGHT_COMP_THRESHOLD = 25
LOGGING                  = True
LOGGING_FREQUENCY        = [1, 3000] #add data every [0] frames, output log file every [1] frames
MAX_SETTING_ATTEMPTS     = 10
FPS_CALIBRATION_TIME     = 10 #sec
BUFFER_CAPACITY_MUL      = 1 #sec
REVERSE_BUFFER_MUL       = 3 #sec

#
#Exceptions
#

class VideoCaptureError(Exception):
    def __init__(self, text):
        self.txt = text

class MaxAttemptsException(Exception):
    def __init__(self, text):
        self.txt = text

def cutFrame(frame, crop):
    try:
        img = frame[crop[0]:crop[1], crop[2]:crop[3]]
        return img
    except Exception as e:
        print("Crop Error: " + str(e))


#
#Crop new original, when camera mode changes
#

def settingOriginalCropImage(cap, day, crop, obj_id, camera_id):
    logging_output = ''
    attempts = 0
    error_status = False
    try:
        cut_path     = ''
        reverse_path = ''
        if not os.path.exists(ORIGINAL_CUTS_DAY_PATH + '/' + str(camera_id)):
            os.makedirs(ORIGINAL_CUTS_DAY_PATH + '/' + str(camera_id))
        if not os.path.exists(ORIGINAL_CUTS_DAY_PATH + '/' + str(camera_id) + '/' + str(obj_id)):
            os.makedirs(ORIGINAL_CUTS_DAY_PATH + '/' + str(camera_id) + '/' + str(obj_id))
        if not os.path.exists(ORIGINAL_CUTS_NIGHT_PATH + '/' + str(camera_id)):
            os.makedirs(ORIGINAL_CUTS_NIGHT_PATH + '/' + str(camera_id))
        if not os.path.exists(ORIGINAL_CUTS_NIGHT_PATH + '/' + str(camera_id) + '/' + str(obj_id)):
            os.makedirs(ORIGINAL_CUTS_NIGHT_PATH + '/' + str(camera_id) + '/' + str(obj_id))
        if day:
            cut_path     = ORIGINAL_CUTS_DAY_PATH + '/' + str(camera_id) + '/' + str(obj_id) + '/' + FIRST_CUT_PATH
            reverse_path = ORIGINAL_CUTS_NIGHT_PATH + '/' + str(camera_id) + '/' + str(obj_id) + '/' + FIRST_CUT_PATH
        else:
            cut_path     = ORIGINAL_CUTS_NIGHT_PATH + '/' + str(camera_id) + '/' + str(obj_id) + '/' + FIRST_CUT_PATH
            reverse_path = ORIGINAL_CUTS_DAY_PATH + '/' + str(camera_id) + '/' + str(obj_id) + '/' + FIRST_CUT_PATH
        if not os.path.exists(cut_path):
            print('[INF] Настройка фрагмента наблюдаемого объекта "' + str(obj_id) + '"... \nУбедитесь, что объект находится в начальном состоянии.')
            counter = 0
            cut_img = ''
            while counter < SETTING_CROP_ITERATIONS:
                if attempts < MAX_SETTING_ATTEMPTS:
                    ret, frame = cap.read()
                    if counter != 0:
                        prev_cut_img = cv2.imread(cut_path)
                        cut_img = frame[crop[0]:crop[1], crop[2]:crop[3]]
                        compare_result = classification.compare_images(prev_cut_img, cut_img)
                        logging_output = logging_output + '\tsetting crop comp result: ' + str(compare_result) + '\n'
                        if float(compare_result) < SETTING_CROP_THRESHOLD:
                            print('[INF] Объект изменил своё состояние во время настройки')
                            counter = 0
                            attempts = attempts + 1
                            time.sleep(3)
                        else:
                            time.sleep(3)
                            counter = counter + 1
                            #print('[INF] Итерация: ' + str(counter)) 
                    else:
                        print('[INF] Начало настройки')
                        cut_img = frame[crop[0]:crop[1], crop[2]:crop[3]]
                        cv2.imwrite(cut_path, cut_img)
                        counter = counter + 1
                        if os.path.exists(reverse_path):
                            #reverse_img = cv2.imread(reverse_path)
                            day_night_compare = classification.compare_hash(reverse_path, cut_path)
                            logging_output = logging_output + '\tday_night_compare: ' + str(day_night_compare) + '\n'
                            #print('day night compare: ' + str(int(day_night_compare)))
                            if int(day_night_compare) > DAY_NIGHT_COMP_THRESHOLD:
                                print('[INF] Объект находится не в начальном состоянии.')
                                os.remove(cut_path)
                                attempts = attempts + 1
                                counter = 0
                        time.sleep(3)
                else:
                    error_status = True
                    return [logging_output, error_status]
            print('[INF] Настройка завершена')
        return [logging_output, error_status]
    except Exception as e:
        error_status = True
        print("[ERR] Ошибка во время настройки области наблюдения за объектом: " + str(e))
        return [logging_output, error_status]


#
#Output functions
#

def outputVideo(name, frame_array, resolution, camera_id, obj_id, ter_id, cloud_session, bucket, local_output, cloud_output, fps, cap_new_states, crop, out_video_format):
    fourcc = None
    video_name = OUTPUT_PATH + ter_id + '/' + camera_id + '/' + str(obj_id) + '/' + name
    if out_video_format == 'mp4':
        #fourcc = cv2.VideoWriter_fourcc(*'MP4V')
        fourcc = 0x00000021
        video_name = video_name + '.mp4'
    else:
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        video_name = video_name + '.avi'
    image_name = OUTPUT_PATH + ter_id + '/' + camera_id + '/' + str(obj_id) + '/' + name + '.jpg'
    image_cut_name = OUTPUT_PATH + ter_id + '/' + camera_id + '/' + str(obj_id) + '/' + name + '_CUT.jpg'
    cv2.imwrite(image_name, frame_array[0])
    if cap_new_states == True:
        img_cut = cutFrame(frame_array[0], crop)    
        cv2.imwrite(image_cut_name, img_cut)
    out_video = cv2.VideoWriter(video_name, fourcc, fps, resolution)
    output = video_name
    for frame in frame_array:
        out_video.write(frame)
    out_video.release()
    if cloud_output == True:
        try:
            cloud_controller.uploadFile(cloud_session, video_name, bucket)
            cloud_controller.uploadFile(cloud_session, image_name, bucket)
            output = 's3://' + bucket + '/' + video_name
        except cloud_controller.CloudUploadFailed as e:
            if local_output != True:
                os.remove(video_name)
                os.remove(image_name)
                output = 'None'
            print('Upload failed: ' + str(e))
    if local_output != True:
        os.remove(video_name)
        os.remove(image_name)
    if local_output != True and cloud_output != True:
        output = 'None'
    return output

def outputLog(name, log_string, cloud_session, bucket, local_output, cloud_output):
    log_file = open(name, 'w')
    log_file.write(log_string)
    log_file.close()

def outputTimeFile(name, camera_id, obj_id, ter_id, state_1, cloud_session, bucket, local_output, cloud_output, day):
    name = OUTPUT_PATH + ter_id + '/' + camera_id + '/' + str(obj_id) + '/' + name + '.txt'
    time_file = open(name, 'w')
    time_file.write('Time: ' + str(time.ctime(time.time())) + '\nTerritory: ' + str(ter_id) + '\nCamera: ' + str(camera_id) + '\nObject: ' + str(obj_id) + '\nState: ' + str(state_1) + '\nDay: ' + str(day))
    time_file.close()
    if local_output != True:
        os.remove(name)

#
#Main cycle
#Video processing
#

def processVideoStream(video, crops, camera_id, obj_ids, ter_id, state_0_list, state_1_list, cloud_session, bucket, local_output, cloud_output, min_duration, max_duration, ch_id, debug_mode, post_enable, post_auth, post_url, at_mr_top, at_mr_bot, maxr_midr, midr_minr, at_add_step, at_sub_step, cap_new_states, obj_types_list, event_types_list, out_video_format, adaptive_mode, fixed_th, og_max):
    #
    #setting variables
    #
    old_day         = None
    calibrated      = False
    start_cal_time  = False
    fps             = None
    fps_counter     = 0
    fps_calibrated  = False
    fps_start_time  = None
    crop_time       = 0.0
    log_counter     = dict.fromkeys(obj_ids, 0)
    out_video_arr   = dict.fromkeys(obj_ids)
    rev_video_arr   = dict.fromkeys(obj_ids)
    log_string      = dict.fromkeys(obj_ids, '')
    threshold       = dict.fromkeys(obj_ids, 0)
    compare_result  = dict.fromkeys(obj_ids, '')
    output_gate     = dict.fromkeys(obj_ids, False)
    reverse_gate    = dict.fromkeys(obj_ids, False)
    og_counter      = dict.fromkeys(obj_ids, 0)
    min_res         = dict.fromkeys(obj_ids)
    max_res         = dict.fromkeys(obj_ids)
    mid_res_array   = dict.fromkeys(obj_ids)
    threshold       = dict.fromkeys(obj_ids)
    compare_result  = dict.fromkeys(obj_ids)
    result          = dict.fromkeys(obj_ids)
    output_buffer   = dict.fromkeys(obj_ids, 0)
    reverse_counter = dict.fromkeys(obj_ids, 0)
    buffer_capacity = 0
    min_frames      = None
    max_frames      = None
    for key in out_video_arr.keys():
        out_video_arr[key] = ['']
        out_video_arr[key].clear()
    for key in rev_video_arr.keys():
        rev_video_arr[key] = ['']
        rev_video_arr[key].clear()
    #
    #Video capture start
    #
    try:
        cap = None
        try:
            cap = cv2.VideoCapture(video)
        except Exception as e:
            if LOGGING == True:
                outputLog(LOG_PATH + 'error/log_' + str(camera_id) + '_' + str(time.time()) + '.txt', 'VCErr Msg: ' + str(e), cloud_session, bucket, local_output, cloud_output)
            raise VideoCaptureError('VCErr Msg: ' + str(e))
        while(cap.isOpened()):
            ret, frame = cap.read() 
            if not(ret):
                try:
                    cap = cv2.VideoCapture(video)
                except Exception as e:
                    if LOGGING == True:
                        outputLog(LOG_PATH + 'error/log_' + str(camera_id) + '_' + str(time.time()) + '.txt', 'VCErr Msg: ' + str(e), cloud_session, bucket, local_output, cloud_output)
                    raise VideoCaptureError('VCErr Msg: ' + str(e))
                continue
            #
            #FPS Calibration
            #
            if fps_calibrated == False:
                if fps_counter == 0:
                    print('[INF] Рассчет FPS...')
                    fps_start_time = time.time()
                fps_counter = fps_counter + 1
                if (time.time() - fps_start_time) > FPS_CALIBRATION_TIME:
                    fps = fps_counter / (time.time() - fps_start_time)
                    buffer_capacity = int(fps * BUFFER_CAPACITY_MUL)
                    reverse_buffer  = int(fps * REVERSE_BUFFER_MUL)
                    min_frames = int(fps) * min_duration
                    max_frames = int(fps) * max_duration
                    if debug_mode:
                        print('[INF] FPS: ' + str(fps) + '; BUFFER CAPACITY: ' + str(buffer_capacity) + '; MIN FRAMES: ' + str(min_frames) + '; MAX FRAMES: ' + str(max_frames))
                    fps_calibrated = True
                else:
                    continue
            #
            #DAY NIGHT mode classification
            #
            try:
                day = classification.captureModeClassification(frame)
            except classification.CapModeClassificationError as e:
                continue
            if day != old_day:
                camera_mode = ''
                if day:
                    camera_mode = 'день'
                else:
                    camera_mode = 'ночь'
                print('[INF] Режим работы видеокамеры: ' + camera_mode)
                for obj_id in obj_ids:
                    min_res[obj_id]       = DEFAULT_MIN_THRESHOLD
                    max_res[obj_id]       = DEFAULT_MAX_THRESHOLD
                    mid_res_array[obj_id] = [350, 50]
                    output_gate[obj_id]   = False
                    calibrated = False
            #
            #Adaptive threshold calibration
            #
            if calibrated == False and start_cal_time == False:
                print('[INF] Начало калибровки порогового значения. ')
                start_cal_time = time.time()
            #
            #Every object comparsion
            #
            for obj_id, crop, state_0, state_1, obj_type_id, event_type_id in zip(obj_ids, crops, state_0_list, state_1_list, obj_types_list, event_types_list):
                if LOGGING == True and ((log_counter[obj_id] % LOGGING_FREQUENCY[0] == 0) or log_counter[obj_id] == 0):
                    log_string[obj_id] = log_string[obj_id] + 'Time: ' + str(time.ctime(time.time())) + '\n'
                    log_string[obj_id] = log_string[obj_id] + 'Day: ' + str(day) + '\n'
                start_crop_time = time.time()
                output_soci = settingOriginalCropImage(cap, day, crop, obj_id, camera_id)
                crop_time = crop_time + (time.time() - start_crop_time)
                if LOGGING == True and output_soci[0]:
                    log_string[obj_id] = log_string[obj_id] + 'Crop Settings: \n' + output_soci[0]
                if output_soci[1] == True:
                    if LOGGING == True:
                        outputLog(LOG_PATH + 'error/log_' + str(camera_id) + '_' + str(obj_id) + '_' + str(time.time()) + '.txt', log_string[obj_id] + '\n[ERR] Максимум попыток при настройке области наблюдения за объектом.\n', cloud_session, bucket, local_output, cloud_output)
                        log_string[obj_id] = ''
                    raise MaxAttemptsException('[ERR] Максимум попыток при настройке области наблюдения за объектом.')       
                img = cutFrame(frame, crop)    
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                cv2.imwrite(TEMP_PATH + str(camera_id) + '_' + str(obj_id) + '_' + TEMP_CURRENT_PATH, img)
                original_paths = []
                if day:
                    original_paths = os.listdir(ORIGINAL_CUTS_DAY_PATH + '/' + str(camera_id) + '/' + str(obj_id))
                else:
                    original_paths = os.listdir(ORIGINAL_CUTS_NIGHT_PATH + '/' + str(camera_id) + '/' + str(obj_id))
                true_results_counter = 0
                comparsions_number = len(original_paths)
                state = None
                if debug_mode:
                    print('Object id: ' + str(obj_id))
                for op in original_paths:
                    if debug_mode:
                        print('\tObject path: ' + str(op))
                    if state == None:
                        if day:
                            original_path = ORIGINAL_CUTS_DAY_PATH + '/' + str(camera_id) + '/' + str(obj_id) + '/' + op
                        else:
                            original_path = ORIGINAL_CUTS_NIGHT_PATH + '/' + str(camera_id) + '/' + str(obj_id) + '/' + op
                        original = cv2.imread(original_path)
                        original = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
                        cv2.imwrite(TEMP_PATH + str(camera_id) + '_' + str(obj_id) + '_' + TEMP_ORIGINAL_PATH, original)
                        #
                        #Comparsion function here
                        #
                        try:
                            out = classification.processSingleImage(TEMP_PATH + str(camera_id) + '_' + str(obj_id) + '_' + TEMP_ORIGINAL_PATH, TEMP_PATH + str(camera_id) + '_' + str(obj_id) + '_' + TEMP_CURRENT_PATH, min_res[obj_id], max_res[obj_id], mid_res_array[obj_id], threshold[obj_id], debug_mode, at_mr_top, at_mr_bot, maxr_midr, midr_minr, at_add_step, at_sub_step, adaptive_mode, fixed_th)
                        except classification.ImageClassificationError as ICE:
                            if LOGGING == True:
                                outputLog(LOG_PATH + 'error/log_' + str(camera_id) + '_' + str(obj_id) + '_' + str(time.time()) + '.txt', log_string[obj_id] + '\n' + str(ICE) + '\n', cloud_session, bucket, local_output, cloud_output)
                            raise classification.ImageClassificationError(str(ICE))
                        result[obj_id]         = out[0]
                        min_res[obj_id]        = out[1]
                        max_res[obj_id]        = out[2]
                        mid_res_array[obj_id]  = out[3]
                        threshold[obj_id]      = out[4]
                        compare_result[obj_id] = out[5]     
                        if result[obj_id] == True:
                            true_results_counter = true_results_counter + 1
                            if true_results_counter == comparsions_number:
                                state = state_1
                        else:
                            state = state_0
                if LOGGING == True and ((log_counter[obj_id] % LOGGING_FREQUENCY[0] == 0) or log_counter[obj_id] == 0 or result[obj_id] == True):
                    log_string[obj_id] = log_string[obj_id] + 'Classification Output: \n\t' + 'Time: ' + str(time.ctime(time.time())) + '\n\tState: ' + str(state) + '\n\tAdaptive Threshold: ' + str(threshold[obj_id]) + '\n\tCompare Result: ' + str(compare_result[obj_id]) + '\n\tMin: ' + str(min_res[obj_id]) + '\n\tMax: ' + str(max_res[obj_id]) + '\n\tMid: ' + str(mid_res_array[obj_id]) + '\n'
                if LOGGING == True and log_counter[obj_id] == LOGGING_FREQUENCY[1]:
                    log_counter[obj_id] = 0
                    outputLog(LOG_PATH + ter_id + '/' + str(camera_id) + '/' + str(obj_id) + '/log_' + str(camera_id) + '_' + str(obj_id) + '_' + str(time.time()) + '.txt', log_string[obj_id], cloud_session, bucket, local_output, cloud_output)
                    log_string[obj_id] = ''
                log_counter[obj_id] = log_counter[obj_id] + 1
                if debug_mode:
                    print('\tState: ' + str(state) + ' Gate: ' + str(output_gate[obj_id]))
                if calibrated == False:
                    if int(time.time() - start_cal_time - crop_time) > CALIBRATION_TIME:
                        calibrated = True
                        start_cal_time = False
                        print('[INF] Калибровка порогового значения завершена')
                    else:
                        continue   
                
                #
                #Output block
                #When state changes, programm goes to save frames and outputs it, when state returns to normal
                #

                #
                #State 0 -> 1 Block
                #
                if state == state_1:
                    og_counter[obj_id] = 0
                    reverse_counter[obj_id] = 0
                    if output_gate[obj_id] == True:
                        output_buffer[obj_id] = 0
                        out_video_arr[obj_id].append(frame)
                        if len(out_video_arr[obj_id]) > max_frames:
                            if debug_mode:
                                    print('Enter 1:')
                            print('[INF] ' + str(time.ctime(time.time())) + ' Состояние контролируемого объекта "' + str(obj_id) +  '" изменено c "' + str(state_0) + '" на "' + str(state_1) + '"')
                            name = str(obj_id) + '_' + str(int(time.time())) + '_' + str(state_1)
                            video_out_location = outputVideo(name, out_video_arr[obj_id], (int(cap.get(3)),int(cap.get(4))), camera_id, obj_id, ter_id, cloud_session, bucket, local_output, cloud_output, fps, cap_new_states, crop, out_video_format)
                            image_out_location = None
                            if video_out_location != None:
                                image_out_location = video_out_location.split('.')[0] + '.jpg'
                            output_gate[obj_id] = False
                            reverse_gate[obj_id] = True
                            og_counter[obj_id] = 0
                            out_video_arr[obj_id].clear() 
                            outputTimeFile(name, camera_id, obj_id, ter_id, state_1, cloud_session, bucket, local_output, cloud_output, day)
                            if post_enable:
                                try:
                                    request = sendPostRequest(post_url, post_auth, ter_id, camera_id, ch_id, video_out_location, image_out_location, obj_id, obj_type_id, event_type_id)
                                    print('[INF] POST запрос отправлен. Ответ: ' + str(request))
                                except Exception as e:
                                    print('[WRN] Ошибка при отправке POST запроса: ' + str(e))
                    else:
                        og_counter[obj_id] = 0
                        out_video_arr[obj_id].clear() 
                        if reverse_gate[obj_id] == True:
                            rev_video_arr[obj_id].append(frame)
                            while len(rev_video_arr[obj_id]) > reverse_buffer:
                                rev_video_arr[obj_id].pop(0)
                #
                #State 1 -> 0 Block
                #When duration < max_duration
                #
                elif out_video_arr[obj_id]:
                    og_counter[obj_id] = 0
                    if output_gate[obj_id] == True:
                        if len(out_video_arr[obj_id]) > min_frames:
                            if output_buffer[obj_id] >= buffer_capacity or len(out_video_arr[obj_id]) >= max_frames:
                                if debug_mode:
                                    print('Enter 2:')
                                print('[INF] ' + str(time.ctime(time.time())) + ' Состояние контролируемого объекта "' + str(obj_id) +  '" изменено c "' + str(state_0) + '" на "' + str(state_1) + '" и обратно')
                                name = str(obj_id) + '_' + str(int(time.time())) + '_' + str(state_1) + '_' + str(state_0)
                                video_out_location = outputVideo(name, out_video_arr[obj_id], (int(cap.get(3)),int(cap.get(4))), camera_id, obj_id, ter_id, cloud_session, bucket, local_output, cloud_output, fps, cap_new_states, crop, out_video_format)
                                image_out_location = None
                                if video_out_location != None:
                                    image_out_location = video_out_location.split('.')[0] + '.jpg'
                                out_video_arr[obj_id].clear() 
                                outputTimeFile(name, camera_id, obj_id, ter_id, state_1, cloud_session, bucket, local_output, cloud_output, day)
                                output_buffer[obj_id] = 0
                                output_gate[obj_id] = False
                                reverse_gate[obj_id] = False
                                og_counter[obj_id] = 0
                                if post_enable:
                                    try:
                                        request = sendPostRequest(post_url, post_auth, ter_id, camera_id, ch_id, video_out_location, image_out_location, obj_id, obj_type_id, event_type_id)
                                        print('[INF] POST запрос отправлен. Ответ: ' + str(request))
                                        #print('[INF] Состав запроса: \n\tURL: ' + post_url + '\n\t"auth": ' + post_auth + '\n\t"hotel_id": ' + ter_id + '\n\t"cam_id": ' + camera_id + '\n\t"ch_id": ' + ch_id + '\n\t"event_record": ' + video_out_location + '\n\t"event_picture": ' + image_out_location)
                                    except Exception as e:
                                        print('[WRN] Ошибка при отправке POST запроса: ' + str(e))
                            else:
                                out_video_arr[obj_id].append(frame)
                                output_buffer[obj_id] = output_buffer[obj_id] + 1
                        else:
                            out_video_arr[obj_id].clear()
                            if output_gate[obj_id] == False:
                                og_counter[obj_id] = og_counter[obj_id] + 1
                                if og_counter[obj_id] > og_max:
                                    og_counter[obj_id] = 0
                                    output_gate[obj_id] = True
                    else:
                        out_video_arr[obj_id].clear()
                        if output_gate[obj_id] == False:
                            og_counter[obj_id] = og_counter[obj_id] + 1
                            if og_counter[obj_id] > og_max:
                                og_counter[obj_id] = 0
                                output_gate[obj_id] = True
                #
                #Reverse State Block 
                #Happens, when state = 1 duration > Maximal duration
                #
                elif rev_video_arr[obj_id]:
                    og_counter[obj_id] = 0
                    if reverse_gate[obj_id] == True:
                        if reverse_counter[obj_id] >= reverse_buffer or len(rev_video_arr[obj_id]) >= max_frames:
                            if debug_mode:
                                print('Enter 3:')
                            print('[INF] ' + str(time.ctime(time.time())) + ' Состояние контролируемого объекта "' + str(obj_id) +  '" изменено c "' + str(state_1) + '" на "' + str(state_0) + '"')
                            name = str(obj_id) + '_' + str(int(time.time())) + '_' + str(state_0)
                            video_out_location = outputVideo(name, rev_video_arr[obj_id], (int(cap.get(3)),int(cap.get(4))), camera_id, obj_id, ter_id, cloud_session, bucket, local_output, cloud_output, fps, cap_new_states, crop, out_video_format)
                            image_out_location = None
                            if video_out_location != None:
                                image_out_location = video_out_location.split('.')[0] + '.jpg'
                            out_video_arr[obj_id].clear() 
                            outputTimeFile(name, camera_id, obj_id, ter_id, state_1, cloud_session, bucket, local_output, cloud_output, day)
                            output_buffer[obj_id] = 0
                            reverse_gate[obj_id] = False
                            og_counter[obj_id] = 0
                            if post_enable:
                                try:
                                    request = sendPostRequest(post_url, post_auth, ter_id, camera_id, ch_id, video_out_location, image_out_location, obj_id, obj_type_id, event_type_id)
                                    print('[INF] POST запрос отправлен. Ответ: ' + str(request))
                                    #print('[INF] Состав запроса: \n\tURL: ' + post_url + '\n\t"auth": ' + post_auth + '\n\t"hotel_id": ' + ter_id + '\n\t"cam_id": ' + camera_id + '\n\t"ch_id": ' + ch_id + '\n\t"event_record": ' + video_out_location + '\n\t"event_picture": ' + image_out_location)
                                except Exception as e:
                                    print('[WRN] Ошибка при отправке POST запроса: ' + str(e))
                        else:
                            rev_video_arr[obj_id].append(frame)
                            reverse_counter[obj_id] = reverse_counter[obj_id] + 1
                    else:
                        rev_video_arr[obj_id].clear()
                        output_buffer[obj_id] = 0
                        reverse_counter[obj_id] = 0
                        if output_gate[obj_id] == False:
                            og_counter[obj_id] = og_counter[obj_id] + 1
                            if og_counter[obj_id] > og_max:
                                og_counter[obj_id] = 0
                                output_gate[obj_id] = True
                #
                #Usual Block
                #When state not changing 
                #
                else:
                    out_video_arr[obj_id].clear()
                    rev_video_arr[obj_id].clear()
                    output_buffer[obj_id] = 0
                    reverse_counter[obj_id] = 0
                    if output_gate[obj_id] == False:
                        og_counter[obj_id] = og_counter[obj_id] + 1
                        if og_counter[obj_id] > og_max:
                            og_counter[obj_id] = 0
                            output_gate[obj_id] = True
            if debug_mode:
                print('\t(add inf: og_counter = ' + str(og_counter[obj_id]) + ', buffer_counter = ' + str(output_buffer[obj_id]) + ', og_max = ' + str(og_max) + ', buffer_capacity = ' + str(buffer_capacity) + ')')
            old_day = day
        cap.release()
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception as e:
        print('[UNK_ERR] ' + str(e))
        print('[INF] Restart...')
