def get_lats(data_table):
    lats = data_table["rov LAT"] - data_table["ref LAT"]
    min_lat = abs(lats.min())
    lats = lats + min_lat

    return lats


def get_ppvoltage(data_table):
    return data_table["peak2peak"]


def get_peak(data_table):
    raise Exception("Not implemented")


def get_pulsewidth_omnipolar(data_table):
    raise Exception("Not implemented")
