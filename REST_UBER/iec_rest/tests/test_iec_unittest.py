import unittest

import numpy.testing as npt
import pandas as pd

from .. import iec_model_rest as iec_model

# create empty pandas dataframes to create empty sip object for testing
df_empty = pd.DataFrame()
# create an empty sip object
iec_empty = iec_model.iec("empty", df_empty, df_empty)

test = {}

class TestIEC(unittest.TestCase):
    def setup(self):
        pass
        # sip2 = sip_model.sip(0, pd_obj_inputs, pd_obj_exp_out)
        # setup the test as needed
        # e.g. pandas to open sip qaqc csv
        #  Read qaqc csv and create pandas DataFrames for inputs and expected outputs

    def teardown(self):
        pass
        # teardown called after each test
        # e.g. maybe write test results to some text file

    def test_z_score_f(self):
        '''
        unittest for function iec.z_score_f:
        '''
        try:
            iec_empty.threshold = pd.Series([0.6])
            iec_empty.LC50 = pd.Series([3])
            iec_empty.dose_response = pd.Series([2.5])
            result = iec_empty.z_score_f_out()
            npt.assert_array_almost_equal(result, -0.554622, 4, '', True)
        finally:
            pass
        return

    def test_F8_f_out(self):
        # '''
        # unittest for function iec.F8_f:
        # '''
        # try:
        #     result = iec_empty.F8_f_out()
        #     npt.assert_array_almost_equal(result, 0.172, 4, '', True)
        # finally:
        #     pass
        # return

    def test_chance_f(self):
        # '''
        # unittest for function iec.chance_f:
        # '''
        # try:
        #     result = iec_empty.chance_f_out()
        #     npt.assert_array_almost_equal(result, 1000000., 4, '', True)
        # finally:
        #     pass
        # return

# unittest will
# 1) call the setup method,
# 2) then call every method starting with "test",
# 3) then the teardown method
if __name__ == '__main__':
    unittest.main()
    #pass
