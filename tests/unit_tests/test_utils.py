import time 

def get_time(second):
    specific_time = time.struct_time((2024, 5, 28, 12, 0, second, 0, 0, -1))
    return time.mktime(specific_time)