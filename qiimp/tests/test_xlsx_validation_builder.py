from unittest import main, TestCase
import datetime
import qiimp.xlsx_validation_builder as xvb


class TestFunctions(TestCase):
    # region _make_date_constraint tests
    def test__make_date_constraint_YYYY(self):
        exp = ('(IFERROR(DATEVALUE(IF(LEN({cell})=4,'
               'CONCATENATE({cell},"-01-01"),'
               'IF(LEN({cell})=7,CONCATENATE({cell},"-01"),IF(LEN({cell})=13,'
               'CONCATENATE({cell},":00"),{cell})))),0)+'
               'IFERROR(TIMEVALUE(IF(LEN({cell})=4,'
               'CONCATENATE({cell},"-01-01"),'
               'IF(LEN({cell})=7,CONCATENATE({cell},"-01"),IF(LEN({cell})=13,'
               'CONCATENATE({cell},":00"),{cell})))),0))>='
               '(IFERROR(DATEVALUE("2008-01-01 00:00:00"),0)+'
               'IFERROR(TIMEVALUE("2008-01-01 00:00:00"),0))')
        obs = xvb._make_date_constraint(">=", "2008")
        self.assertEqual(exp, obs)

    def test__make_date_constraint_YYYY_MM(self):
        exp = ('(IFERROR(DATEVALUE(IF(LEN({cell})=4,'
               'CONCATENATE({cell},"-01-01"),'
               'IF(LEN({cell})=7,CONCATENATE({cell},"-01"),IF(LEN({cell})=13,'
               'CONCATENATE({cell},":00"),{cell})))),0)+'
               'IFERROR(TIMEVALUE(IF(LEN({cell})=4,'
               'CONCATENATE({cell},"-01-01"),'
               'IF(LEN({cell})=7,CONCATENATE({cell},"-01"),IF(LEN({cell})=13,'
               'CONCATENATE({cell},":00"),{cell})))),0))>='
               '(IFERROR(DATEVALUE("2008-12-01 00:00:00"),0)+'
               'IFERROR(TIMEVALUE("2008-12-01 00:00:00"),0))')
        obs = xvb._make_date_constraint(">=", "2008-12")
        self.assertEqual(exp, obs)

    def test__make_date_constraint_YYYY_MM_DD(self):
        exp = ('(IFERROR(DATEVALUE(IF(LEN({cell})=4,'
               'CONCATENATE({cell},"-01-01"),'
               'IF(LEN({cell})=7,CONCATENATE({cell},"-01"),IF(LEN({cell})=13,'
               'CONCATENATE({cell},":00"),{cell})))),0)+'
               'IFERROR(TIMEVALUE(IF(LEN({cell})=4,'
               'CONCATENATE({cell},"-01-01"),'
               'IF(LEN({cell})=7,CONCATENATE({cell},"-01"),IF(LEN({cell})=13,'
               'CONCATENATE({cell},":00"),{cell})))),0))>'
               '(IFERROR(DATEVALUE("2008-12-03 00:00:00"),0)+'
               'IFERROR(TIMEVALUE("2008-12-03 00:00:00"),0))')
        # NB: this test uses > rather than >= in other tests, just to show it
        # can be done :)
        obs = xvb._make_date_constraint(">", "2008-12-03")
        self.assertEqual(exp, obs)

    def test__make_date_constraint_YYYY_MM_DD_HH(self):
        exp = ('(IFERROR(DATEVALUE(IF(LEN({cell})=4,CONCATENATE({cell},"-01-01"),'
               'IF(LEN({cell})=7,CONCATENATE({cell},"-01"),IF(LEN({cell})=13,'
               'CONCATENATE({cell},":00"),{cell})))),0)+'
               'IFERROR(TIMEVALUE(IF(LEN({cell})=4,CONCATENATE({cell},"-01-01"),'
               'IF(LEN({cell})=7,CONCATENATE({cell},"-01"),IF(LEN({cell})=13,'
               'CONCATENATE({cell},":00"),{cell})))),0))>='
               '(IFERROR(DATEVALUE("2008-12-03 14:00:00"),0)+'
               'IFERROR(TIMEVALUE("2008-12-03 14:00:00"),0))')
        obs = xvb._make_date_constraint(">=", "2008-12-03 14")
        self.assertEqual(exp, obs)

    def test__make_date_constraint_YYYY_MM_DD_HH_mm(self):
        exp = ('(IFERROR(DATEVALUE(IF(LEN({cell})=4,'
               'CONCATENATE({cell},"-01-01"),'
               'IF(LEN({cell})=7,CONCATENATE({cell},"-01"),IF(LEN({cell})=13,'
               'CONCATENATE({cell},":00"),{cell})))),0)+'
               'IFERROR(TIMEVALUE(IF(LEN({cell})=4,'
               'CONCATENATE({cell},"-01-01"),'
               'IF(LEN({cell})=7,CONCATENATE({cell},"-01"),IF(LEN({cell})=13,'
               'CONCATENATE({cell},":00"),{cell})))),0))>='
               '(IFERROR(DATEVALUE("2008-12-03 14:12:00"),0)+'
               'IFERROR(TIMEVALUE("2008-12-03 14:12:00"),0))')
        obs = xvb._make_date_constraint(">=", "2008-12-03 14:12")
        self.assertEqual(exp, obs)

    def test__make_date_constraint_YYYY_MM_DD_HH_mm_ss(self):
        exp = ('(IFERROR(DATEVALUE(IF(LEN({cell})=4,'
               'CONCATENATE({cell},"-01-01"),'
               'IF(LEN({cell})=7,CONCATENATE({cell},"-01"),IF(LEN({cell})=13,'
               'CONCATENATE({cell},":00"),{cell})))),0)+'
               'IFERROR(TIMEVALUE(IF(LEN({cell})=4,'
               'CONCATENATE({cell},"-01-01"),'
               'IF(LEN({cell})=7,CONCATENATE({cell},"-01"),IF(LEN({cell})=13,'
               'CONCATENATE({cell},":00"),{cell})))),0))>='
               '(IFERROR(DATEVALUE("2008-12-03 14:12:01"),0)+'
               'IFERROR(TIMEVALUE("2008-12-03 14:12:01"),0))')
        obs = xvb._make_date_constraint(">=", "2008-12-03 14:12:01")
        self.assertEqual(exp, obs)

    def test__make_date_constraint_HH_mm(self):
        exp = ('(IFERROR(DATEVALUE(IF(LEN({cell})=4,'
               'CONCATENATE({cell},"-01-01"),'
               'IF(LEN({cell})=7,CONCATENATE({cell},"-01"),IF(LEN({cell})=13,'
               'CONCATENATE({cell},":00"),{cell})))),0)+'
               'IFERROR(TIMEVALUE(IF(LEN({cell})=4,'
               'CONCATENATE({cell},"-01-01"),'
               'IF(LEN({cell})=7,CONCATENATE({cell},"-01"),IF(LEN({cell})=13,'
               'CONCATENATE({cell},":00"),{cell})))),0))>='
               '(IFERROR(DATEVALUE("1900-01-01 14:12:00"),0)+'
               'IFERROR(TIMEVALUE("1900-01-01 14:12:00"),0))')
        obs = xvb._make_date_constraint(">=", "14:12")
        self.assertEqual(exp, obs)

    def test__make_date_constraint_HH_mm_ss(self):
        exp = ('(IFERROR(DATEVALUE(IF(LEN({cell})=4,'
               'CONCATENATE({cell},"-01-01"),'
               'IF(LEN({cell})=7,CONCATENATE({cell},"-01"),IF(LEN({cell})=13,'
               'CONCATENATE({cell},":00"),{cell})))),0)+'
               'IFERROR(TIMEVALUE(IF(LEN({cell})=4,'
               'CONCATENATE({cell},"-01-01"),'
               'IF(LEN({cell})=7,CONCATENATE({cell},"-01"),IF(LEN({cell})=13,'
               'CONCATENATE({cell},":00"),{cell})))),0))>='
               '(IFERROR(DATEVALUE("1900-01-01 14:12:01"),0)+'
               'IFERROR(TIMEVALUE("1900-01-01 14:12:01"),0))')
        obs = xvb._make_date_constraint(">=", "14:12:01")
        self.assertEqual(exp, obs)
    # endregion _make_date_constraint tests

    # region _cast_date_time tests
    def test__cast_date_time_YYYY(self):
        input_str = "2008"
        exp = datetime.datetime.strptime(input_str, "%Y")
        obs = xvb._cast_date_time(input_str, xvb.datetime_formats)
        self.assertEqual(exp, obs)
        
    def test__cast_date_time_YYYY_MM(self):
        input_str = "2008-12"
        exp = datetime.datetime.strptime(input_str, "%Y-%m")
        obs = xvb._cast_date_time(input_str, xvb.datetime_formats)
        self.assertEqual(exp, obs)
        
    def test__cast_date_time_YYYY_MM_DD(self):
        input_str = "2008-12-03"
        exp = datetime.datetime.strptime(input_str, "%Y-%m-%d")
        obs = xvb._cast_date_time(input_str, xvb.datetime_formats)
        self.assertEqual(exp, obs)
        
    def test__cast_date_time_YYYY_MM_DD_HH(self):
        input_str = "2008-12-03 13"
        exp = datetime.datetime.strptime(input_str, "%Y-%m-%d %H")
        obs = xvb._cast_date_time(input_str, xvb.datetime_formats)
        self.assertEqual(exp, obs)
        
    def test__cast_date_time_YYYY_MM_DD_HH_mm(self):
        input_str = "2008-12-03 13:04"
        exp = datetime.datetime.strptime(input_str, "%Y-%m-%d %H:%M")
        obs = xvb._cast_date_time(input_str, xvb.datetime_formats)
        self.assertEqual(exp, obs)

    def test__cast_date_time_YYYY_MM_DD_HH_mm_ss(self):
        input_str = "2008-12-03 13:04:08"
        exp = datetime.datetime.strptime(input_str, "%Y-%m-%d %H:%M:%S")
        obs = xvb._cast_date_time(input_str, xvb.datetime_formats)
        self.assertEqual(exp, obs)

    def test__cast_date_time_HH_mm(self):
        time_str = "13:04"
        date_str = "1900-01-01 " + time_str
        exp = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        obs = xvb._cast_date_time(time_str, xvb.datetime_formats)
        self.assertEqual(exp, obs)

    def test__cast_date_time_HH_mm_ss(self):
        time_str = "13:04:08"
        date_str = "1900-01-01 " + time_str
        exp = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        obs = xvb._cast_date_time(time_str, xvb.datetime_formats)
        self.assertEqual(exp, obs)
    # endregion _cast_date_time tests
