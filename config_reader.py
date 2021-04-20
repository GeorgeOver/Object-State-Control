#
#Data parser and reader from 'config.txt'
#

class ConfigReadError(Exception):
    def __init__(self, text):
        self.txt = text

def readConfig(config):
    try:
        config           = open(config, 'r')
        video            = None
        obj_ids          = []
        camera_id        = None
        crops            = []
        hotel_id         = None
        ch_id            = None
        state_0_list     = []
        state_1_list     = []
        obj_types_list   = []
        event_types_list = []
        cloud_public_key = None
        cloud_secret_key = None
        bucket           = None
        local_output     = None
        cloud_output     = None
        min_duration     = 1
        max_duration     = 10
        post_auth        = None
        debug_mode       = False
        post_enable      = False
        post_url         = None
        at_mr_top        = 10
        at_mr_bot        = 3
        maxr_midr        = 6
        midr_minr        = 6
        at_add_step      = 3
        at_sub_step      = 5
        cap_new_states   = False
        out_video_foramt = 'avi'
        adaptive_mode    = False
        fixed_th         = 17
        og_max           = 100
        for line in config:
            parameter = line.split('===')[0].strip()
            if parameter == 'camera_id':
                camera_id = line.split('===')[1].strip()
            elif parameter == 'input':
                video = line.split('===')[1].strip()
            elif parameter == 'objects':
                objects = line.split('===')[1].strip().split(';')
                for obj in objects:
                    if len(obj) > 10:
                        crop          = []
                        xmin          = None
                        ymin          = None
                        xmax          = None
                        ymax          = None
                        state_0       = None
                        state_1       = None
                        obj_type_id   = None
                        event_type_id = None
                        obj_ids.append(obj.split(':')[0].strip())
                        print(obj)
                        right_part = obj.split(':')[1].split(',')
                        print(right_part)
                        for rp in right_part:
                            rp_param = rp.split('=')[0].strip()
                            if rp_param   == 'ymin':
                                ymin = rp.split('=')[1].strip()
                            elif rp_param == 'ymax':
                                ymax = rp.split('=')[1].strip()
                            elif rp_param == 'xmin':
                                xmin = rp.split('=')[1].strip()
                            elif rp_param == 'xmax':
                                xmax = rp.split('=')[1].strip()
                            elif rp_param == 'state_0':
                                state_0 = rp.split('=')[1].strip()
                            elif rp_param == 'state_1':
                                state_1 = rp.split('=')[1].strip()
                            elif rp_param == 'obj_type_id':
                                obj_type_id = rp.split('=')[1].strip()
                            elif rp_param == 'event_type_id':
                                event_type_id = rp.split('=')[1].strip()
                        crop.append(int(ymin))
                        crop.append(int(ymax))
                        crop.append(int(xmin))
                        crop.append(int(xmax))
                        crops.append(crop)
                        state_0_list.append(state_0)
                        state_1_list.append(state_1)
                        obj_types_list.append(obj_type_id)
                        event_types_list.append(event_type_id)
            elif parameter == 'hotel_id':
                hotel_id = line.split('===')[1].strip()
            elif parameter == 'cloud_public_key':
                cloud_public_key = line.split('===')[1].strip()
            elif parameter == 'cloud_secret_key':
                cloud_secret_key = line.split('===')[1].strip()
            elif parameter == 'cloud_bucket':
                bucket = line.split('===')[1].strip()
            elif parameter == 'local_output':
                local_output = line.split('===')[1].strip()
                if local_output == 'true':
                    local_output = True
                else:
                    local_output = False
            elif parameter == 'cloud_output':
                cloud_output = line.split('===')[1].strip()
                if cloud_output == 'true':
                    cloud_output = True
                else:
                    cloud_output = False
            elif parameter == 'min_duration':
                min_duration = line.split('===')[1].strip()
                if min_duration.isdigit():
                    min_duration = int(min_duration)
                else:
                    min_duration = 25
            elif parameter == 'max_duration':
                max_duration = line.split('===')[1].strip()
                if max_duration.isdigit():
                    max_duration = int(max_duration)
                else:
                    max_duration = 200
            elif parameter == 'post_auth':
                post_auth = line.split('===')[1].strip()
            elif parameter == 'post_enable':
                post_enable = line.split('===')[1].strip()
                if post_enable == 'true':
                    post_enable = True
                else: 
                    post_enable = False
            elif parameter == 'debug_enable':
                debug_mode = line.split('===')[1].strip()
                if debug_mode == 'true':
                    debug_mode = True
                else: 
                    debug_mode = False
            elif parameter == 'ch_id':
                ch_id = line.split('===')[1].strip()
            elif parameter == 'post_url':
                post_url = line.split('===')[1].strip()
            elif parameter == 'at_mr_top':
                at_mr_top = line.split('===')[1].strip()
                if at_mr_top.isdigit():
                    at_mr_top = int(at_mr_top)
                else:
                    at_mr_top = 10 
            elif parameter == 'at_mr_bot':
                at_mr_bot = line.split('===')[1].strip()
                if at_mr_bot.isdigit():
                    at_mr_bot = int(at_mr_bot)
                else:
                    at_mr_bot = 3
            elif parameter == 'maxr_midr':
                maxr_midr = line.split('===')[1].strip()
                if maxr_midr.isdigit():
                    maxr_midr = int(maxr_midr)
                else:
                    maxr_midr = 6
            elif parameter == 'midr_minr':
                midr_minr = line.split('===')[1].strip()
                if midr_minr.isdigit():
                    midr_minr = int(midr_minr)
                else:
                    midr_minr = 6
            elif parameter == 'at_add_step':
                at_add_step = line.split('===')[1].strip()
                if at_add_step.isdigit():
                    at_add_step = int(at_add_step)
                else:
                    at_add_step = 3
            elif parameter == 'at_sub_step':
                at_sub_step = line.split('===')[1].strip()
                if at_sub_step.isdigit():
                    at_sub_step = int(at_sub_step)
                else:
                    at_sub_step = 5
            elif parameter == 'cap_new_states':
                cap_new_states = line.split('===')[1].strip()
                if cap_new_states == 'true':
                    cap_new_states = True
                else:
                    cap_new_states = False
            elif parameter == 'out_video_format':
                ovf_read = line.split('===')[1].strip()
                if ovf_read == 'mp4':
                    out_video_foramt = 'mp4'
                else:
                    out_video_foramt = 'avi'
            elif parameter == 'fixed_th':
                fixed_th = line.split('===')[1].strip()
                if fixed_th.isdigit():
                    fixed_th = int(fixed_th)
                else:
                    fixed_th = 17
            elif parameter == 'adaptive_mode':
                adaptive_mode = line.split('===')[1].strip()
                if adaptive_mode == 'true':
                    adaptive_mode = True
                else:
                    adaptive_mode = False
            elif parameter == 'og_max':
                og_max = line.split('===')[1].strip()
                if og_max.isdigit():
                    og_max = int(og_max)
                else:
                    og_max = 100
    except Exception as e:
        raise ConfigReadError('Config read error: ' + str(e))
    return [camera_id, video, crops, obj_ids, hotel_id, state_0_list, state_1_list, cloud_public_key, cloud_secret_key, bucket, local_output, cloud_output, min_duration, max_duration, ch_id, debug_mode, post_enable, post_auth, post_url, at_mr_top, at_mr_bot, maxr_midr, midr_minr, at_add_step, at_sub_step, cap_new_states, obj_types_list, event_types_list, out_video_foramt, adaptive_mode, fixed_th, og_max]