def test_script(args):
    #Do something
    some_number = 10
    if some_number >= 20:
        return "CRIT: Some number is %s" % some_number
    elif some_number >= 10:
        return "WARN: Some number is %s" % some_number
    return "OK: some number is %s" % some_number
