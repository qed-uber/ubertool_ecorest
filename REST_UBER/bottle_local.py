"""
    Backend server script runnig Bottle, a lightweight Python server. 
    All incoming requests to the backend server are handled here including 
    model run execution and MongoDB querying. 

    To run this script locally you will need MongoDB installed and running 
    on your machine on its default port (27017).  To start the server, 
    open terminal in this file's location and run the followning command:

    'python bottle_local.py'

    The Bottle serve will now be running and you view the logs in real time 
    in the terminal window.  "ctrl + C" to stop the server.
"""

import bottle
from bottle import route, run, post, request, auth_basic, abort, response
import keys_Picloud_S3
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from boto.s3.bucket import Bucket
import os
import json
import warnings

try:
    import pandas as pd
except:
    pass

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
os.environ.update({
    "PROJECT_ROOT": PROJECT_ROOT
})
print os.environ['PROJECT_ROOT']

# Enable console logging
bottle.debug(True)
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

#####The folloing two lines could let the REST servers to handle multiple requests##
########################(not necessary for local dev. env.)#########################
# from gevent import monkey
# monkey.patch_all()

##########################################################################################
#####AMAZON KEY, store output files. You might have to write your own import approach#####
##########################################################################################
s3_key = keys_Picloud_S3.amazon_s3_key
s3_secretkey = keys_Picloud_S3.amazon_s3_secretkey
rest_key = keys_Picloud_S3.picloud_api_key
rest_secretkey = keys_Picloud_S3.picloud_api_secretkey
###########################################################################################
bottle.BaseRequest.MEMFILE_MAX = 1024 * 1024 # (or whatever you want)

class NumPyArangeEncoder(json.JSONEncoder):
    def default(self, obj):
        import numpy as np
        if isinstance(obj, np.ndarray):
            return obj.tolist() # or map(int, obj)
        return json.JSONEncoder.default(self, obj)

try:
    import pymongo
    client = pymongo.MongoClient('localhost', 27017)
    db = client.ubertool
except Exception:
    logging.exception(Exception)


def check(user, passwd):
    if user == keys_Picloud_S3.picloud_api_key and passwd == keys_Picloud_S3.picloud_api_secretkey:
        return True
    return False

all_result = {}

# the decorator
def enable_cors(fn):
    def _enable_cors(*args, **kwargs):
        # set CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

        if bottle.request.method != 'OPTIONS':
            # actual request; reply with the actual response
            return fn(*args, **kwargs)

    return _enable_cors

def errorMessage(error, jid):
    """Returns exception error message as valid JSON string to caller"""
    logging.exception(error)
    e = str(error)
    return {'user_id':'admin', 'result': {'error': e}, '_id':jid}


def model_caller(model, jid):
    """
        Method to call the model Python modules
    """
    try:
        import importlib
        # Dynamically import the model Python module
        model_module = importlib.import_module('.'+model+'_model_rest', model+'_rest')
        # Set the model Object to a local variable (class name = model)
        model_object = getattr(model_module, model)
        
        logging.info(json.dumps(request.json))

        try:
            run_type = request.json["run_type"]
        except KeyError, e:
            return errorMessage(e, jid)

        if run_type == "qaqc":
            logging.info('============= QAQC Run =============')

            # pd_obj = pd.io.json.read_json(json.dumps(request.json["inputs"]))
            pd_obj = pd.DataFrame.from_dict(request.json["inputs"], dtype='float64')
            # pd_obj_exp = pd.io.json.read_json(json.dumps(request.json["out_exp"]))
            pd_obj_exp = pd.DataFrame.from_dict(request.json["out_exp"], dtype='float64')

            result_json_tuple = model_object(run_type, pd_obj, pd_obj_exp).json

        elif run_type == "batch":
            logging.info('============= Batch Run =============')
            # pd_obj = pd.io.json.read_json(json.dumps(request.json["inputs"]))
            pd_obj = pd.DataFrame.from_dict(request.json["inputs"], dtype='float64')

            result_json_tuple = model_object(run_type, pd_obj, None).json

        else:
            logging.info('============= Single Run =============')
            pd_obj = pd.DataFrame.from_dict(request.json["inputs"], dtype='float64')

            result_json_tuple = model_object(run_type, pd_obj, None).json

        # Values returned from model run: inputs, outputs, and expected outputs (if QAQC run)
        inputs_json = json.loads(result_json_tuple[0])
        outputs_json = json.loads(result_json_tuple[1])
        exp_out_json = json.loads(result_json_tuple[2])

        model_obj_dict = {'user_id':'admin', 'inputs': inputs_json, 'outputs': outputs_json, 'exp_out': exp_out_json, '_id':jid, 'run_type': run_type}

        if model != 'sam':
            try:
                save_to_mongo(model, {'user_id':'admin', 'inputs': json.dumps(inputs_json), 'outputs': json.dumps(outputs_json), 'exp_out': exp_out_json, '_id':jid, 'run_type': run_type})
            except:
                pass

        return model_obj_dict

    except Exception, e:
        return errorMessage(e, jid)


def save_to_mongo(model, model_obj_dict):

    logging.info("save_to_mongo() called")

    logging.info(model_obj_dict)

    db[model].save(model_obj_dict)
    logging.info("Saved to mongo!")

##################################terrplant#############################################
@route('/terrplant/<jid>', method='POST') 
# @auth_basic(check)
def terrplant_rest(jid):
    # try:
    #     from terrplant_rest import terrplant_model_rest
        
    #     logging.info(json.dumps(request.json))
    #     logging.info(type(request.json))

    #     try:
    #         run_type = request.json["run_type"]
    #     except KeyError, e:
    #         return errorMessage(e, jid)

    #     if run_type == "qaqc":
    #         logging.info('============= QAQC Run =============')

    #         pd_obj = pd.io.json.read_json(json.dumps(request.json["inputs"]))
    #         pd_obj_exp = pd.io.json.read_json(json.dumps(request.json["out_exp"]))

    #         result_json_tuple = terrplant_model_rest.terrplant(run_type, pd_obj, pd_obj_exp).json

    #     elif run_type == "batch":
    #         logging.info('============= Batch Run =============')
    #         pd_obj = pd.io.json.read_json(json.dumps(request.json["inputs"]))

    #         result_json_tuple = terrplant_model_rest.terrplant(run_type, pd_obj, None).json

    #     else:
    #         logging.info('============= Single Run =============')
    #         pd_obj = pd.io.json.read_json(json.dumps(request.json["inputs"]))

    #         result_json_tuple = terrplant_model_rest.terrplant(run_type, pd_obj, None).json

    #     # Values returned from model run: inputs, outputs, and expected outputs (if QAQC run)
    #     inputs_json = json.loads(result_json_tuple[0])
    #     outputs_json = json.loads(result_json_tuple[1])
    #     exp_out_json = json.loads(result_json_tuple[2])

    #     return {'user_id':'admin', 'inputs': inputs_json, 'outputs': outputs_json, 'exp_out': exp_out_json, '_id':jid, 'run_type': run_type}
    # except Exception, e:
    #     return errorMessage(e, jid)
    return model_caller('terrplant', jid)
        
##################################terrplant#############################################

##################################sip#############################################
@route('/sip/<jid>', method='POST') 
# @auth_basic(check)
def sip_rest(jid):
    # try:
    #     for k, v in request.json.iteritems():
    #         exec '%s = v' % k
    #     all_result.setdefault(jid,{}).setdefault('status','none')
    #     from sip_rest import sip_model_rest
    #     result = sip_model_rest.sip(chemical_name, bw_bird, bw_quail, bw_duck, bwb_other, bw_rat, bwm_other, b_species, m_species, bw_mamm, sol, ld50_a, ld50_m, aw_bird, mineau, aw_mamm, noaec, noael)
    #     # if (result):
    #     #     all_result[jid]['status']='done'
    #     #     all_result[jid]['input']=request.json
    #     #     all_result[jid]['result']=result
    #     return {'user_id':'admin', 'result': result.__dict__, '_id':jid}
    # except Exception, e:
    #     return errorMessage(e, jid)
    return model_caller('sip', jid)

##################################sip#############################################

##################################stir#############################################
@route('/stir/<jid>', method='POST') 
# @auth_basic(check)
def stir_rest(jid):
    try:
        for k, v in request.json.iteritems():
            exec '%s = v' % k
        all_result.setdefault(jid,{}).setdefault('status','none')
        from stir_rest import stir_model_rest
        result = stir_model_rest.stir(run_type,chemical_name,application_rate,column_height,spray_drift_fraction,direct_spray_duration, 
                                      molecular_weight,vapor_pressure,avian_oral_ld50,body_weight_assessed_bird,body_weight_tested_bird,mineau_scaling_factor, 
                                      mammal_inhalation_lc50,duration_mammal_inhalation_study,body_weight_assessed_mammal,body_weight_tested_mammal, 
                                      mammal_oral_ld50)
        # if (result):
        #     all_result[jid]['status']='done'
        #     all_result[jid]['input']=request.json
        #     all_result[jid]['result']=result
        return {'user_id':'admin', 'result': result.__dict__, '_id':jid}
    except Exception, e:
        return errorMessage(e, jid)

##################################sip#############################################

##################################dust#############################################
@route('/dust/<jid>', method='POST') 
# @auth_basic(check)
def dust_rest(jid):
    try:
        for k, v in request.json.iteritems():
            exec '%s = v' % k
        all_result.setdefault(jid,{}).setdefault('status','none')
        from dust_rest import dust_model_rest
        result = dust_model_rest.dust(chemical_name, label_epa_reg_no, ar_lb, frac_pest_surface, dislodge_fol_res, bird_acute_oral_study, bird_study_add_comm,
                                      low_bird_acute_ld50, test_bird_bw, mineau_scaling_factor, mamm_acute_derm_study, mamm_study_add_comm, mam_acute_derm_ld50, mam_acute_oral_ld50, test_mam_bw)
        # if (result):
        #     all_result[jid]['status']='done'
        #     all_result[jid]['input']=request.json
        #     all_result[jid]['result']=result
        return {'user_id':'admin', 'result': result.__dict__, '_id':jid}
    except Exception, e:
        return errorMessage(e, jid)

##################################sip#############################################

##################################trex2#############################################
@route('/trex2/<jid>', method='POST') 
# @auth_basic(check)
def trex2_rest(jid):
    try:
        for k, v in request.json.iteritems():
            exec '%s = v' % k
        all_result.setdefault(jid,{}).setdefault('status','none')
        from trex2_rest import trex2_model_rest
        result = trex2_model_rest.trex2(chem_name, use, formu_name, a_i, Application_type, seed_treatment_formulation_name, seed_crop, seed_crop_v, r_s, b_w, p_i, den, h_l, n_a, ar_lb, day_out,
                                        ld50_bird, lc50_bird, NOAEC_bird, NOAEL_bird, aw_bird_sm, aw_bird_md, aw_bird_lg, 
                                        Species_of_the_tested_bird_avian_ld50, Species_of_the_tested_bird_avian_lc50, Species_of_the_tested_bird_avian_NOAEC, Species_of_the_tested_bird_avian_NOAEL, 
                                        tw_bird_ld50, tw_bird_lc50, tw_bird_NOAEC, tw_bird_NOAEL, x, ld50_mamm, lc50_mamm, NOAEC_mamm, NOAEL_mamm, aw_mamm_sm, aw_mamm_md, aw_mamm_lg, tw_mamm,
                                        m_s_r_p)
        if (result):
            result_json = json.dumps(result.__dict__, cls=NumPyArangeEncoder)
            # all_result[jid]['status']='done'
            # all_result[jid]['input']=request.json
            # all_result[jid]['result']=result
        return {'user_id':'admin', 'result':result_json, '_id':jid}
    except Exception, e:
        return errorMessage(e, jid)

##################################trex2#############################################

##################################therps#############################################
@route('/therps/<jid>', method='POST') 
# @auth_basic(check)
def therps_rest(jid):
    try:
        for k, v in request.json.iteritems():
            exec '%s = v' % k
        all_result.setdefault(jid,{}).setdefault('status','none')
        from therps_rest import therps_model_rest
        result = therps_model_rest.therps(chem_name, use, formu_name, a_i, h_l, n_a, i_a, a_r, avian_ld50, avian_lc50, avian_NOAEC, avian_NOAEL, 
                                          Species_of_the_tested_bird_avian_ld50, Species_of_the_tested_bird_avian_lc50, Species_of_the_tested_bird_avian_NOAEC, Species_of_the_tested_bird_avian_NOAEL,
                                          bw_avian_ld50, bw_avian_lc50, bw_avian_NOAEC, bw_avian_NOAEL,
                                          mineau_scaling_factor, bw_herp_a_sm, bw_herp_a_md, bw_herp_a_lg, wp_herp_a_sm, wp_herp_a_md, 
                                          wp_herp_a_lg, c_mamm_a, c_herp_a)
        if (result):
            result_json = json.dumps(result.__dict__, cls=NumPyArangeEncoder)
            # all_result[jid]['status']='done'
            # all_result[jid]['input']=request.json
            # all_result[jid]['result']=result
        return {'user_id':'admin', 'result':result_json, '_id':jid}
    except Exception, e:
        return errorMessage(e, jid)

##################################therps#############################################

##################################iec#############################################
@route('/iec/<jid>', method='POST') 
# @auth_basic(check)
def iec_rest(jid):
    try:
        for k, v in request.json.iteritems():
            exec '%s = v' % k
        all_result.setdefault(jid,{}).setdefault('status','none')
        from iec_rest import iec_model_rest
        result = iec_model_rest.iec(dose_response, LC50, threshold)
        # if (result):
        #     all_result[jid]['status']='done'
        #     all_result[jid]['input']=request.json
        #     all_result[jid]['result']=result
        return {'user_id':'admin', 'result': result.__dict__, '_id':jid}
    except Exception, e:
        return errorMessage(e, jid)

##################################iec#############################################

##################################agdrift#############################################
@route('/agdrift/<jid>', method='POST') 
# @auth_basic(check)
def agdrift_rest(jid):
    try:
        for k, v in request.json.iteritems():
            exec '%s = v' % k
        all_result.setdefault(jid,{}).setdefault('status','none')
        from agdrift_rest import agdrift_model_rest
        result = agdrift_model_rest.agdrift(drop_size, ecosystem_type, application_method, boom_height, orchard_type, application_rate, distance, aquatic_type, calculation_input, init_avg_dep_foa, avg_depo_gha, avg_depo_lbac, deposition_ngL, deposition_mgcm, nasae, y, x, express_y)
        # if (result):
        #     all_result[jid]['status']='done'
        #     all_result[jid]['input']=request.json
        #     all_result[jid]['result']=result
        return {'user_id':'admin', 'result': result.__dict__, '_id':jid}
    except Exception, e:
        return errorMessage(e, jid)

##################################agdrift#############################################

##################################earthworm#############################################
@route('/earthworm/<jid>', method='POST') 
# @auth_basic(check)
def earthworm_rest(jid):
    try:
        for k, v in request.json.iteritems():
            exec '%s = v' % k
        all_result.setdefault(jid,{}).setdefault('status','none')
        from earthworm_rest import earthworm_model_rest
        result = earthworm_model_rest.earthworm(k_ow, l_f_e, c_s, k_d, p_s, c_w, m_w, p_e)
        # if (result):
        #     all_result[jid]['status']='done'
        #     all_result[jid]['input']=request.json
        #     all_result[jid]['result']=result
        return {'user_id':'admin', 'result': result.__dict__, '_id':jid}
    except Exception, e:
        return errorMessage(e, jid)

##################################earthworm#############################################

##################################rice#############################################
@route('/rice/<jid>', method='POST') 
# @auth_basic(check)
def rice_rest(jid):
    try:
        for k, v in request.json.iteritems():
            exec '%s = v' % k
        all_result.setdefault(jid,{}).setdefault('status','none')
        from rice_rest import rice_model_rest
        result = rice_model_rest.rice(chemical_name, mai, dsed, a, pb, dw, osed, kd)
        # if (result):
        #     all_result[jid]['status']='done'
        #     all_result[jid]['input']=request.json
        #     all_result[jid]['result']=result
        return {'user_id':'admin', 'result': result.__dict__, '_id':jid}
    except Exception, e:
        return errorMessage(e, jid)

##################################rice#############################################

##################################kabam#############################################
@route('/kabam/<jid>', method='POST') 
# @auth_basic(check)
def kabam_rest(jid):
    try:
        for k, v in request.json.iteritems():
            exec '%s = v' % k
        all_result.setdefault(jid,{}).setdefault('status','none')
        from kabam_rest import kabam_model_rest
        result = kabam_model_rest.kabam(chemical_name, l_kow, k_oc, c_wdp, water_column_EEC, c_wto, mineau_scaling_factor, x_poc, x_doc, c_ox, w_t, c_ss, oc, k_ow, Species_of_the_tested_bird, bw_quail, bw_duck, bwb_other, avian_ld50, avian_lc50, avian_noaec, m_species, bw_rat, bwm_other, mammalian_ld50, mammalian_lc50, mammalian_chronic_endpoint, lf_p_sediment, lf_p_phytoplankton, lf_p_zooplankton, lf_p_benthic_invertebrates, lf_p_filter_feeders, lf_p_small_fish, lf_p_medium_fish, mf_p_sediment, mf_p_phytoplankton, mf_p_zooplankton, mf_p_benthic_invertebrates, mf_p_filter_feeders, mf_p_small_fish, sf_p_sediment, sf_p_phytoplankton, sf_p_zooplankton, sf_p_benthic_invertebrates, sf_p_filter_feeders, ff_p_sediment, ff_p_phytoplankton, ff_p_zooplankton, ff_p_benthic_invertebrates, beninv_p_sediment, beninv_p_phytoplankton, beninv_p_zooplankton, zoo_p_sediment, zoo_p_phyto, s_lipid, s_NLOM, s_water, v_lb_phytoplankton, v_nb_phytoplankton, v_wb_phytoplankton, wb_zoo, v_lb_zoo, v_nb_zoo, v_wb_zoo, wb_beninv, v_lb_beninv, v_nb_beninv, v_wb_beninv, wb_ff, v_lb_ff, v_nb_ff, v_wb_ff, wb_sf, v_lb_sf, v_nb_sf, v_wb_sf, wb_mf, v_lb_mf, v_nb_mf, v_wb_mf, wb_lf, v_lb_lf, v_nb_lf, v_wb_lf, kg_phytoplankton, kd_phytoplankton, ke_phytoplankton, mo_phytoplankton, mp_phytoplankton, km_phytoplankton, km_zoo, k1_phytoplankton, k2_phytoplankton, k1_zoo, k2_zoo, kd_zoo, ke_zoo, k1_beninv, k2_beninv, kd_beninv, ke_beninv, km_beninv, k1_ff, k2_ff, kd_ff, ke_ff, km_ff, k1_sf, k2_sf, kd_sf, ke_sf, km_sf, k1_mf, k2_mf, kd_mf, ke_mf, km_mf, k1_lf, k2_lf, kd_lf, ke_lf, km_lf, rate_constants, s_respire, phyto_respire, zoo_respire, beninv_respire, ff_respire, sfish_respire, mfish_respire, lfish_respire)
        if (result):
            result_json = json.dumps(result.__dict__, cls=NumPyArangeEncoder)
            # all_result[jid]['status']='done'
            # all_result[jid]['input']=request.json
            # all_result[jid]['result']=result
        return {'user_id':'admin', 'result':result_json, '_id':jid}
    except Exception, e:
        return errorMessage(e, jid)

##################################kabam#############################################

##################################geneec#############################################
@route('/geneec/<jid>', method='POST') 
# @auth_basic(check)
def geneec_rest(jid):
    try:
        for k, v in request.json.iteritems():
            exec '%s = v' % k
        all_result.setdefault(jid,{}).setdefault('status','none')
        from geneec_rest import gfix
        # print request.json
        result = gfix.geneec2(APPRAT,APPNUM,APSPAC,KOC,METHAF,WETTED,METHOD,AIRFLG,YLOCEN,GRNFLG,GRSIZE,ORCFLG,INCORP,SOL,METHAP,HYDHAP,FOTHAP)
        # from geneec_rest import geneec_model_rest
        # result = geneec_model_rest.geneec(APPRAT,APPNUM,APSPAC,KOC,METHAF,WETTED,METHOD,AIRFLG,YLOCEN,GRNFLG,GRSIZE,ORCFLG,INCORP,SOL,METHAP,HYDHAP,FOTHAP)

        # if (result):
            # all_result[jid]['status']='done'
            # all_result[jid]['input']=request.json
            # all_result[jid]['result']=result

        return {'user_id':'admin', 'result': result.__dict__, '_id':jid}
    except Exception, e:
        return errorMessage(e, jid)

##################################geneec#############################################


##################################przm5#############################################
@route('/przm5/<jid>', method='POST') 
# @auth_basic(check)
def przm5_rest(jid):
    try:
        for k, v in request.json.iteritems():
            exec '%s = v' % k
        all_result.setdefault(jid,{}).setdefault('status','none')

        from przm5_rest import PRZM5_pi_win
        result = PRZM5_pi_win.PRZM5_pi(pfac, snowmelt, evapDepth, 
                                     uslek, uslels, uslep, fieldSize, ireg, slope, hydlength,
                                     canopyHoldup, rootDepth, canopyCover, canopyHeight,
                                     NumberOfFactors, useYears,
                                     USLE_day, USLE_mon, USLE_year, USLE_c, USLE_n, USLE_cn,
                                     firstyear, lastyear,
                                     dayEmerge_text, monthEmerge_text, dayMature_text, monthMature_text, dayHarvest_text, monthHarvest_text, addYearM, addYearH,
                                     irflag, tempflag,
                                     fleach, depletion, rateIrrig,
                                     albedo, bcTemp, Q10Box, soilTempBox1,
                                     numHoriz,
                                     SoilProperty_thick, SoilProperty_compartment, SoilProperty_bulkden, SoilProperty_maxcap, SoilProperty_mincap, SoilProperty_oc, SoilProperty_sand, SoilProperty_clay,
                                     rDepthBox, rDeclineBox, rBypassBox,
                                     eDepthBox, eDeclineBox,
                                     appNumber_year, totalApp,
                                     SpecifyYears, ApplicationTypes, PestAppyDay, PestAppyMon, Rela_a, app_date_type, DepthIncorp, PestAppyRate, localEff, localSpray,
                                     PestDispHarvest,
                                     nchem, convert_Foliar1, parentTo3, deg1To2, foliarHalfLifeBox,
                                     koc_check, Koc,
                                     soilHalfLifeBox,
                                     convertSoil1, convert1to3, convert2to3)
        # if (result):
            # all_result[jid]['status']='done'
            # all_result[jid]['input']=request.json
            # all_result[jid]['result']=result

        # print request.json
        # print all_result
        # print list(ff)[0][0]

        return {'user_id':'admin', 'result': result, '_id':jid}
    except Exception, e:
        return errorMessage(e, jid)

##################################przm5#############################################


################################# VVWM #############################################
@route('/vvwm/<jid>', method='POST') 
# @auth_basic(check)
def vvwm_rest(jid):
    try:
        for k, v in request.json.iteritems():
            exec '%s = v' % k
        all_result.setdefault(jid,{}).setdefault('status','none')

        from vvwm_rest import VVWM_pi_win
        result = VVWM_pi_win.VVWM_pi(working_dir,
                                    koc_check, Koc, soilHalfLifeBox, soilTempBox1, foliarHalfLifeBox,
                                    wc_hl, w_temp, bm_hl, ben_temp, ap_hl, p_ref, h_hl, mwt, vp, sol, Q10Box,
                                    convertSoil, convert_Foliar, convertWC, convertBen, convertAP, convertH,
                                    deg_check, totalApp,
                                    SpecifyYears, ApplicationTypes, PestAppyDay, PestAppyMon, appNumber_year, app_date_type, DepthIncorp, PestAppyRate, localEff, localSpray,
                                    scenID,
                                    buried, D_over_dx, PRBEN, benthic_depth, porosity, bulk_density, FROC2, DOC2, BNMAS,
                                    DFAC, SUSED, CHL, FROC1, DOC1, PLMAS,
                                    firstYear, lastyear, vvwmSimType,
                                    afield, area, depth_0, depth_max,
                                    ReservoirFlowAvgDays)

        # all_result[jid]['status']='done'
        # all_result[jid]['input']=request.json
        # all_result[jid]['result']=result

        return {'user_id':'admin', 'result': result, '_id':jid}
    except Exception, e:
        return errorMessage(e, jid)

################################# VVWM #############################################

##################################przm##############################################
@route('/przm/<jid>', method='POST') 
# @auth_basic(check)

def przm_rest(jid):
    try:
        import time
        for k, v in request.json.iteritems():
            exec '%s = v' % k
        all_result.setdefault(jid,{}).setdefault('status','none')

        from przm_rest import PRZM_pi_win
        result = PRZM_pi_win.PRZM_pi(noa, met, inp, run, MM, DD, YY, CAM_f, DEPI_text, Ar_text, EFF, Drft)
        return {'user_id':'admin', 'result': result, '_id':jid}
    except Exception, e:
        return errorMessage(e, jid)
    
##################################przm##############################################

# ##################################przm_batch##############################################
# result_all=[]
# @route('/przm_batch/<jid>', method='POST') 
# @auth_basic(check)
# def przm_rest(jid):
#     from przm_rest import PRZM_pi_new
#     for k, v in request.json.iteritems():
#         exec '%s = v' % k
#     zz=0
#     for przm_obs_temp in przm_objs:
#         print zz
#         # przm_obs_temp = przm_objs[index]
#         result_temp = PRZM_pi_new.PRZM_pi(przm_obs_temp['NOA'], przm_obs_temp['met_o'], przm_obs_temp['inp_o'], przm_obs_temp['run_o'], przm_obs_temp['MM'], przm_obs_temp['DD'], przm_obs_temp['YY'], przm_obs_temp['CAM_f'], przm_obs_temp['DEPI_text'], przm_obs_temp['Ar_text'], przm_obs_temp['EFF'], przm_obs_temp['Drft'])
#         result_all.append(result_temp)
#         zz=zz+1
#     # element = {"user_id":"admin", "_id":jid, "run_type":'batch', "output_html": 'output_html', "model_object_dict":result_all}
#     # print element
#     # from przm_rest import PRZM_batch_control
#     # result = PRZM_pi_new.PRZM_pi(noa, met, inp, run, MM, DD, YY, CAM_f, DEPI_text, Ar_text, EFF, Drft)

#     return {"user_id":"admin", "result": result_all, "_id":jid}
    
# ##################################przm_batch##############################################

##################################przm_batch##############################################
@route('/przm_batch/<jid>', method='POST') 
# @auth_basic(check)
def przm_rest(jid):
    try:
        from przm_rest import PRZM_pi_new
        for k, v in request.json.iteritems():
            exec '%s = v' % k
        
        result_all=[]
        zz=0

        for przm_obs_temp in przm_objs:
            print zz
            # przm_obs_temp = przm_objs[index]
            result_temp = PRZM_pi_new.PRZM_pi(przm_obs_temp['NOA'], przm_obs_temp['met_o'], przm_obs_temp['inp_o'], przm_obs_temp['run_o'], przm_obs_temp['MM'], przm_obs_temp['DD'], przm_obs_temp['YY'], przm_obs_temp['CAM_f'], przm_obs_temp['DEPI_text'], przm_obs_temp['Ar_text'], przm_obs_temp['EFF'], przm_obs_temp['Drft'])
            przm_obs_temp['link'] = result_temp[0]
            przm_obs_temp['x_precip'] = [float(i) for i in result_temp[1]]
            przm_obs_temp['x_runoff'] = [float(i) for i in result_temp[2]]
            przm_obs_temp['x_et'] = [float(i) for i in result_temp[3]]
            przm_obs_temp['x_irr'] = [float(i) for i in result_temp[4]]
            przm_obs_temp['x_leachate'] = [float(i)/100000 for i in result_temp[5]]
            przm_obs_temp['x_pre_irr'] = [i+j for i,j in zip(przm_obs_temp['x_precip'], przm_obs_temp['x_irr'])]
            result_all.append(przm_obs_temp)
            zz += 1
        element={"user_id":"admin", "_id":jid, "run_type":'batch', "output_html": "", "model_object_dict":result_all}
        
        # Save batch results to MongoDB   --> Is this the best place for this to be called???
        db['przm'].save(element)
        # return {"user_id":"admin", "result": result_all, "_id":jid}
    except Exception, e:
        return errorMessage(e, jid)
    
##################################przm_batch##############################################


##################################exams##############################################
@route('/exams/<jid>', method='POST') 
# @auth_basic(check)
def exams_rest(jid):
    try:
        import time
        for k, v in request.json.iteritems():
            exec '%s = v' % k
        all_result.setdefault(jid,{}).setdefault('status','none')

        from exams_rest import exams_pi_win
        result = exams_pi_win.exams_pi(chem_name, scenarios, met, farm, mw, sol, koc, vp, aem, anm, aqp, tmper, n_ph, ph_out, hl_out)
        return {'user_id':'admin', 'result': result, '_id':jid}
    except Exception, e:
        return errorMessage(e, jid)
    
##################################exams##############################################

##################################pfam##############################################
@route('/pfam/<jid>', method='POST') 
# @auth_basic(check)

def pfam_rest(jid):
    try:
        import time
        for k, v in request.json.iteritems():
            exec '%s = v' % k
            # print k,'=',v
        # all_result.setdefault(jid,{}).setdefault('status','none')

        from pfam_rest import pfam_pi_win
        result = pfam_pi_win.pfam_pi(wat_hl,wat_t,ben_hl,ben_t,unf_hl,unf_t,aqu_hl,aqu_t,hyd_hl,mw,vp,sol,koc,hea_h,hea_r_t,
               noa,dd_out,mm_out,ma_out,sr_out,weather,wea_l,nof,date_f1,nod_out,fl_out,wl_out,ml_out,to_out,
               zero_height_ref,days_zero_full,days_zero_removal,max_frac_cov,mas_tras_cof,leak,ref_d,ben_d,
               ben_por,dry_bkd,foc_wat,foc_ben,ss,wat_c_doc,chl,dfac,q10,area_app)
        return {'user_id':'admin', 'result': result.__dict__, '_id':jid}
    except Exception, e:
        return errorMessage(e, jid)
    
##################################pfam##############################################

##################################przm_exams##############################################
@route('/przm_exams/<jid>', method='POST') 
# @auth_basic(check)
def przm_exams_rest(jid):
    try:
        for k, v in request.json.iteritems():
            exec '%s = v' % k
            # print k, '=', v
        # all_result.setdefault(jid,{}).setdefault('status','none')

        from przm_exams_rest import PRZM_EXAMS_pi_win
        result = PRZM_EXAMS_pi_win.PRZM_EXAMS_pi(chem_name, noa, scenarios, unit, met, inp, run, exam, MM, DD, YY, CAM_f, DEPI, Ar, EFF, Drft, 
                                             farm, mw, sol, koc, vp, aem, anm, aqp, tmper, n_ph, ph_out, hl_out)
        return {'user_id':'admin', 'result': result, '_id':jid}
    except Exception, e:
        return errorMessage(e, jid)

##################################przm_exams##############################################

################################## SAM ##############################################
@route('/sam/<jid>', method='POST')
def sam_rest(jid):

    try:
        import sam_rest.sam_rest_model as sam

        try:
            run_type = request.json["run_type"]
        except KeyError, e:
            return errorMessage(e, jid)

        if run_type == "qaqc":
            logging.info('============= QAQC Run =============')


        elif run_type == "batch":
            logging.info('============= Batch Run =============')


        else:
            logging.info('============= Single Run =============')
            inputs_json = json.dumps(request.json["inputs"])

            logging.info(inputs_json)

            result_json_tuple = sam.sam(inputs_json, jid, run_type)

        # Values returned from model run: inputs, outputs, and expected outputs (if QAQC run)
        # inputs_json = json.loads(result_json_tuple[0])
        outputs_json = result_json_tuple
        exp_out_json = ""

        return {'user_id':'admin', 'inputs': inputs_json, 'outputs': outputs_json, 'exp_out': exp_out_json, '_id':jid, 'run_type': run_type}

    except Exception, e:
        return errorMessage(e, jid)

################################## SAM ##############################################

"""
    Amazon S3 File Uploads
"""

##################File upload####################
@route('/file_upload', method='POST') 
# @auth_basic(check)
def file_upload():
    import shutil
    for k, v in request.json.iteritems():
        exec '%s = v' % k

    ##upload file to S3
    conn = S3Connection(s3_key, s3_secretkey)
    bucket = Bucket(conn, model_name)
    k=Key(bucket)
    print src1
    os.chdir(src1)
    k.key=name1
    link='https://s3.amazonaws.com/'+model_name+'/'+name1

    print 'begin upload'
    k.set_contents_from_filename('test.zip')
    k.set_acl('public-read-write')
    print 'end upload'
    src1_up=os.path.abspath(os.path.join(src1, '..'))
    os.chdir(src1_up)
    shutil.rmtree(src1)

"""
    MongoDB-specific calls
"""

##########insert results into mongodb#########################
@route('/save_history_html', method='POST')
# @auth_basic(check)
def insert_output_html():
    """
    DEPRECATED: Use save_model_object(model_object_dict, model_name, run_type) instead
    """
    warnings.warn("DEPRECATED: Use save_model_object(model_object_dict, model_name, run_type) instead", DeprecationWarning)

    for k, v in request.json.iteritems():
        exec "%s = v" % k
    element = { "user_id": "admin",
                "_id": _id,
                "run_type": run_type,
                "output_html": output_html,
                "model_object_dict": model_object_dict
                }
    db[model_name].save(element)
    logging.info("Save history, _id = "+_id)
    print _id


@route('/save_history', method='POST')
# @auth_basic(check)
def insert_model_obj():
    """
    Save model object to MongoDB as new document
    """
    for k, v in request.json.iteritems():
        exec "%s = v" % k
    element = { "user_id": "admin",
                "_id": _id,
                "run_type": run_type,
                "model_object_dict": model_object_dict
                }
    db[model_name].save(element)
    # logging.info("Save history test, _id = "+_id)
    

@route('/get_model_object', method='POST')
# @auth_basic(check)
def get_model_object():
    """
        Return model object from MongoDB to be loaded into view (e.g. Django)
    """
    for k, v in request.json.iteritems():
        exec '%s = v' % k

    try:

        if model_name == 'sam':  # SAM changed "_id" to "jid" Mongo key
            model_object_c = db[model_name].find(
                { "jid": jid },
                { "_id": 0, "model_object_dict": 1 }
            )
        else:
            # Cursor          Mongo collection     Document      Projection (fields to return)
            model_object_c = db[model_name].find(
                { "_id": jid },
                { "model_object_dict": 1, "_id": 0 }
            )
        for i in model_object_c:
            # print i
            model_object = i['model_object_dict']
        # logging.info({"model_object": model_object})
        return { "model_object": model_object, "jid": jid }

    except Exception, e:
        return { "model_object": None, "error": str(e) }


@route('/get_sam_huc_output', method='POST')
# @auth_basic(check)
def get_model_object():
    """
        Return model object from MongoDB to be loaded into view (e.g. Django)
    """
    for k, v in request.json.iteritems():
        exec '%s = v' % k

    try:
        # Cursor          Mongo collection
        cursor = db.sam.aggregate([
            { '$match': { "jid": jid } },             # Filter document by "jid" / Mongo "_id"
            { '$project' : { "_id": 0, "model_object_dict.output": { huc12: 1 } } }  # Return only desired HUC
        ])
        # print cursor
        # print type(cursor)
        # for i in cursor['result']:
        #     print i
        #     huc12_output = i[huc12]
        logging.info({ "huc12_output": cursor['result'], "jid": jid })
        return { "huc12_output": cursor['result'], "jid": jid }

    except Exception, e:
        return { "huc12_output": None, "error": str(e) }


@route('/update_html', method='POST')
# @auth_basic(check)
def update_output_html():
    """
    DEPRECATED: no replacement method as model's output page as HTML is no longer being stored in MongoDB
    """
    warnings.warn("DEPRECATED: no replacement method as model's output page as HTML is no longer being stored in MongoDB", DeprecationWarning)

    for k, v in request.json.iteritems():
        exec "%s = v" % k
    # print request.json
    db[model_name].update( { "_id" : _id }, { '$set': { "output_html": output_html } } )


###############Check History####################
@route('/ubertool_history/<model_name>/<jid>')
# @auth_basic(check)
def get_document(model_name, jid):
    entity = db[model_name].find_one( { '_id': jid } )
    # print entity
    if not entity:
        abort(404, 'No document with jid %s' % jid)
    return entity


@route('/user_history', method='POST')
# @auth_basic(check)
def get_user_model_hist():
    """
        Return python list of all model run entries from MongoDB
    """
    for k, v in request.json.iteritems():
        exec '%s = v' % k
    hist_all = []

    if model_name == 'sam':  # SAM changed "_id" to "jid" Mongo key

        entity = db.sam.find( { 'user_id': user_id } ).sort("jid", -1).limit(20)

        for i in entity:
            i.pop('_id', None)  # Remove '_id' key, which is a Mongo ObjectId, bc it cannot be serialized
            hist_all.append(i)
        if not entity:
            abort(404, 'No document with jid %s' % jid)

        return { "hist_all": hist_all }

    else:
        entity = db[model_name].find( { 'user_id': user_id } ).sort("_id", -1)
        for i in entity:
            hist_all.append(i)
        if not entity:
            abort(404, 'No document with jid %s' % jid)

        return { "hist_all": hist_all }

@route('/get_html_output', method='POST')
# @auth_basic(check)
def get_html_output():
    """
    DEPRECATED: Use get_model_object(jid, model_name) instead
    """
    warnings.warn("DEPRECATED: Use get_model_object(jid, model_name) instead", DeprecationWarning)

    for k, v in request.json.iteritems():
        exec '%s = v' % k
    html_output_c = db[model_name].find( { "_id" :jid }, { "output_html":1, "_id":0 } )
    for i in html_output_c:
        # print i
        html_output = i['output_html']
    return { "html_output":html_output }

@route('/get_przm_batch_output', method='POST')
# @auth_basic(check)
def get_przm_batch_output():
    for k, v in request.json.iteritems():
        exec '%s = v' % k
    result_output_c = db[model_name].find( { "_id" :jid }, { "model_object_dict":1, "_id":0 } )
    for i in result_output_c:
        # print i
        result = i['model_object_dict']
    return { "result":result }

@route('/get_pdf', method='POST')
# @auth_basic(check)
def get_pdf():
    for k, v in request.json.iteritems():
        exec '%s = v' % k
    final_str = pdf_t
    final_str = final_str + """<br>"""
    if (int(pdf_nop)>0):
        for i in range(int(pdf_nop)):
            final_str = final_str + """<img id="imgChart1" src="%s" />"""%(pdf_p[i])
            final_str = final_str + """<br>"""

    from generate_doc import generatepdf_pi
    result=generatepdf_pi.generatepdf_pi(final_str)
    return { "result":result }

@route('/get_html', method='POST')
# @auth_basic(check)
def get_html():
    for k, v in request.json.iteritems():
        exec '%s = v' % k
    final_str = pdf_t
    final_str = final_str + """<br>"""
    if (int(pdf_nop)>0):
        for i in range(int(pdf_nop)):
            final_str = final_str + """<img id="imgChart1" src="%s" />"""%(pdf_p[i])
            final_str = final_str + """<br>"""

    from generate_doc import generatehtml_pi
    result=generatehtml_pi.generatehtml_pi(final_str)
    return { "result":result }


"""
=============================================================================================
                              O R E  T E S T I N G
=============================================================================================
"""

# @auth_basic(check)
# @enable_cors
@route('/ore/load/<query>', method='GET')
def ore_rest_category_query(query):

    from ore_rest import ore_db
    # print query

    result = ore_db.loadChoices(query)

    return { "result": result }

@route('/ore/category', method='POST')
def ore_rest_category_query():

    from ore_rest import ore_db

    query = {}
    for k, v in request.json.iteritems():
        exec "query['%s'] = v" % k
        # print k, v

    result = ore_db.oreWorkerActivities(query)

    return { "result": result }

@route('/ore/output', method='POST')
def ore_rest_output_query():

    from ore_rest import ore_db, ore_rest_model
    inputs = request.json

    # query = {}
    # for k, v in request.json.iteritems():
    #     exec "query['%s'] = v" % k
    #     # print k, v

    query_result_list = ore_db.oreOutputQuery(inputs)
    output = ore_rest_model.ore(inputs, query_result_list)

    # result = "Done"

    return { "result": {
                "input": inputs,
                "output": output
            }}


"""
    Execute command for Bottle server
"""
run(host='localhost', port=7777, debug=True)
# run(host='localhost', port=7777, server='gevent', debug=True)
