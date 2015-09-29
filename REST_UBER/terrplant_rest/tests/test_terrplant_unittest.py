import unittest
import pandas as pd
import numpy.testing as npt
# the following works when running test script in parent directory as package:
# python -m tests.test_terrplant_unittest
# the following works for running as nosetests from parent directory:
from .. import terrplant_model_rest as terrplant_model

# load transposed qaqc data for inputs and expected outputs
# csv_transpose_path_in = "./terrplant_qaqc_in_transpose.csv"
# pd_obj_inputs = pd.read_csv(csv_transpose_path_in, index_col=0, engine='python')
# print(pd_obj_inputs)
# csv_transpose_path_exp = "./terrplant_qaqc_exp_transpose.csv"
# pd_obj_exp_out = pd.read_csv(csv_transpose_path_exp, index_col=0, engine='python')
# print(pd_obj_exp_out)

# create empty pandas dataframes to create empty terrplant object
df_empty = pd.DataFrame()
terrplant_empty = terrplant_model.terrplant("empty", df_empty, df_empty)

test = {}


class TestTerrplant(unittest.TestCase):
    def setup(self):
        pass
        # setup the test as needed
        # e.g. pandas to open terrplant qaqc csv
        #  Read qaqc csv and create pandas DataFrames for inputs and expected outputs

    def teardown(self):
        pass
        # teardown called after each test
        # e.g. maybe write test results to some text file

# each of these functions are queued by "run_methods" and have outputs defined as properties in the terrplant qaqc csv
    def test_rundry(self):
        """
        unittest for function terrplant.rundry
        """
        #(self.application_rate/self.incorporation_depth) * self.runoff_fraction
        try:
            terrplant_empty.application_rate = pd.Series([10.], dtype='int')
            terrplant_empty.incorporation_depth = pd.Series([2.], dtype='int')
            terrplant_empty.runoff_fraction = pd.Series([.1], dtype='float')
            result = terrplant_empty.rundry()
            npt.assert_array_almost_equal(result, 0.5, 4, '', True)
        finally:
            pass
        return

    def test_runsemi(self):
        """
        unittest for function terrplant.runsemi
        """
        #self.out_runsemi = (self.application_rate/self.incorporation_depth) * self.runoff_fraction * 10
        try:
            terrplant_empty.application_rate = pd.Series([10.], dtype='int')
            terrplant_empty.incorporation_depth = pd.Series([2.], dtype='int')
            terrplant_empty.runoff_fraction = pd.Series([.1], dtype='float')
            result = terrplant_empty.runsemi()
            npt.assert_array_almost_equal(result,5, 4, '', True)
        finally:
            pass
        return

    def test_spray(self):
        """
        unittest for function terrplant.spray
        """
        #self.out_spray = self.application_rate * self.drift_fraction
        try:
            terrplant_empty.application_rate = pd.Series([10.], dtype='int')
            terrplant_empty.drift_fraction = pd.Series([0.5], dtype='float')
            result = terrplant_empty.spray()
            npt.assert_array_almost_equal(result, 5, 4, '', True)
        finally:
            pass
        return

    def test_totaldry(self):
        """
        unittest for function terrplant.totaldry
        """
        #self.out_totaldry = self.out_rundry + self.out_spray
        try:
            terrplant_empty.rundry = pd.Series([0.5], dtype='float')
            terrplant_empty.spray = pd.Series([5.], dtype='int')
            result = terrplant_empty.totaldry()
            npt.assert_array_almost_equal(result, 5.5, 4, '', True)
        finally:
            pass
        return

    def test_totalsemi(self):
        """
        unittest for function terrplant.totalsemi
        """
        #self.out_totalsemi = self.out_runsemi + self.out_spray
        try:
            terrplant_empty.out_runsemi = pd.Series([5.], dtype='int')
            terrplant_empty.out_spray = pd.Series([5.], dtype='int')
            result = terrplant_empty.totalsemi()
            npt.assert_array_almost_equal(result, 10, 4, '', True)
        finally:
            pass
        return

    def test_nms_rq_dry(self):
        """
        unittest for function terrplant.nms_rq_dry
        """
        #self.out_nms_rq_dry = self.out_totaldry/self.ec25_nonlisted_seedling_emergence_monocot
        try:
            terrplant_empty.out_totaldry = pd.Series([5.5], dtype='float')
            terrplant_empty.ec25_nonlisted_seedling_emergence_monocot = pd.Series([0.05], dtype='float')
            result = terrplant_empty.nmsRQdry()
            npt.assert_array_almost_equal(result, 110, 4, '', True)
        finally:
            pass
        return

    def test_nms_rq_semi(self):
        """
        unittest for function terrplant.nms_rq_semi
        """
        #self.out_nms_rq_semi = self.out_totalsemi/self.ec25_nonlisted_seedling_emergence_monocot
        try:
            terrplant_empty.out_totalsemi = pd.Series([10.], dtype='int')
            terrplant_empty.ec25_nonlisted_seedling_emergence_monocot = pd.Series([0.05], dtype='float')
            result = terrplant_empty.nmsRQsemi()
            npt.assert_array_almost_equal(result, 200, 4, '', True)
        finally:
            pass
        return

    def test_nms_rq_spray(self):
        """
        unittest for function terrplant.nms_rq_spray
        """
        #self.out_nms_rq_spray = self.out_spray/self.ec25_nonlisted_seedling_emergence_monocot
        try:
            terrplant_empty.out_spray = pd.Series([5.], dtype='int')
            terrplant_empty.ec25_nonlisted_seedling_emergence_monocot = pd.Series([0.05], dtype='float')
            result = terrplant_empty.nmsRQspray()
            npt.assert_array_almost_equal(result, 100, 4, '', True)
        finally:
            pass
        return

    def test_lms_rq_dry(self):
        """
        unittest for function terrplant.lms_rq_dry
        """
        #self.out_lms_rq_dry = self.out_totaldry/self.ec25_nonlisted_seedling_emergence_dicot
        try:
            terrplant_empty.out_totaldry = pd.Series([5.5], dtype='float')
            terrplant_empty.ec25_nonlisted_seedling_emergence_dicot = pd.Series([0.01], dtype='float')
            result = terrplant_empty.lmsRQdry()
            npt.assert_array_almost_equal(result, 550, 4, '', True)
        finally:
            pass
        return

    def test_lms_rq_semi(self):
        """
        unittest for function terrplant.lms_rq_semi
        """
        #self.out_lms_rq_semi = self.out_totalsemi/self.ec25_nonlisted_seedling_emergence_dicot
        try:
            terrplant_empty.out_totalsemi = pd.Series([10.], dtype='int')
            terrplant_empty.ec25_nonlisted_seedling_emergence_dicot = pd.Series([0.01], dtype='float')
            result = terrplant_empty.lmsRQsemi()
            npt.assert_array_almost_equal(result, 1000, 4, '', True)
        finally:
            pass
        return

    def test_lms_rq_spray(self):
        """
        unittest for function terrplant.lms_rq_spray
        """
        #self.out_lms_rq_spray = self.out_spray/self.ec25_nonlisted_seedling_emergence_dicot
        try:
            terrplant_empty.out_spray = pd.Series([5.], dtype='int')
            terrplant_empty.ec25_nonlisted_seedling_emergence_dicot = pd.Series([0.01], dtype='float')
            result = terrplant_empty.lmsRQspray()
            npt.assert_array_almost_equal(result, 500, 4, '', True)
        finally:
            pass
        return

    def test_nds_rq_dry(self):
        """
        unittest for function terrplant.nds_rq_dry
        """
        #self.out_nds_rq_dry = self.out_totaldry/self.noaec_listed_seedling_emergence_monocot
        try:
            terrplant_empty.out_totaldry = pd.Series([5.5], dtype='float')
            terrplant_empty.noaec_listed_seedling_emergence_monocot = pd.Series([0.02], dtype='float')
            result = terrplant_empty.ndsRQdry()
            npt.assert_array_almost_equal(result, 275, 4, '', True)
        finally:
            pass
        return

    def test_nds_rq_semi(self):
        """
        unittest for function terrplant.nds_rq_semi
        """
        #self.out_nds_rq_semi = self.out_totalsemi/self.noaec_listed_seedling_emergence_monocot
        try:
            terrplant_empty.out_totalsemi = pd.Series([10.], dtype='int')
            terrplant_empty.noaec_listed_seedling_emergence_monocot = pd.Series([0.02], dtype='float')
            result = terrplant_empty.ndsRQsemi()
            npt.assert_array_almost_equal(result, 500, 4, '', True)
        finally:
            pass
        return

    def test_nds_rq_spray(self):
        """
        unittest for function terrplant.nds_rq_spray
        """
        #self.out_nds_rq_spray = self.out_spray/self.noaec_listed_seedling_emergence_monocot
        try:
            terrplant_empty.out_spray = pd.Series([5.], dtype='int')
            terrplant_empty.noaec_listed_seedling_emergence_monocot = pd.Series([0.02], dtype='float')
            result = terrplant_empty.ndsRQspray()
            npt.assert_array_almost_equal(result, 250, 4, '', True)
        finally:
            pass
        return

    def test_lds_rq_dry(self):
        """
        unittest for function terrplant.lds_rq_dry
        """
        #self.out_lds_rq_dry = self.out_totaldry/self.noaec_listed_seedling_emergence_dicot
        try:
            terrplant_empty.out_totaldry = pd.Series([5.5], dtype='float')
            terrplant_empty.noaec_listed_seedling_emergence_dicot = pd.Series([0.1], dtype='float')
            result = terrplant_empty.ldsRQdry()
            npt.assert_array_almost_equal(result, 55, 4, '', True)
        finally:
            pass
        return

    def test_lds_rq_semi(self):
        """
        unittest for function terrplant.lds_rq_semi
        """
        #self.out_lds_rq_semi = self.out_totalsemi/self.noaec_listed_seedling_emergence_dicot
        try:
            terrplant_empty.out_totalsemi = pd.Series([10.], dtype='int')
            terrplant_empty.noaec_listed_seedling_emergence_dicot = pd.Series([0.1], dtype='float')
            result = terrplant_empty.ldsRQsemi()
            npt.assert_array_almost_equal(result, 100, 4, '', True)
        finally:
            pass
        return

    def test_lds_rq_spray(self):
        """
        unittest for function terrplant.lds_rq_spray
        """
        #self.out_lds_rq_spray = self.out_spray/self.noaec_listed_seedling_emergence_dicot
        try:
            terrplant_empty.out_spray = pd.Series([5.], dtype='int')
            terrplant_empty.noaec_listed_seedling_emergence_dicot = pd.Series([0.1], dtype='float')
            result = terrplant_empty.ldsRQspray()
            npt.assert_array_almost_equal(result, 50, 4, '', True)
        finally:
            pass
        return


# unittest will
# 1) call the setup method,
# 2) then call every method starting with "test",
# 3) then the teardown method
if __name__ == '__main__':
    unittest.main()