# -*- coding: utf-8 -*-
# Version : V1.0
# Author  : Seven
# Date    : 2018/6/2 19:08


import os
import re
import yaml
import logging.config
import xml.dom.minidom


# Put traces into current working path
PWD = os.getcwd()
TRACE_PATH = os.path.join(PWD, "trace")
YAML_PATH = os.path.join(PWD, "logging.yaml")
LOG_PATH = os.path.join(PWD, "smart_timing.log")


# Add and display log
def setup_logging(default_path="logging.yaml", default_level=logging.INFO,
                  env_key="LOG_CFG"):
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, "r") as f:
            logging.config.dictConfig(yaml.load(f))
    else:
        logging.basicConfig(level=default_level)


setup_logging(default_path=YAML_PATH)
logger = logging.getLogger("fileLogger")


def write_time(trace_in, t_final):
    """This func is designed for writing result of time into time_result.txt
    """

    if re.match(re.compile("Timeout"), trace_in):
        # Special format for "Timeout" trace
        logger.info("%s fetch times : %d times" % (trace_in, t_final))
        time_result = trace_in.split('.', 1)[0] + ': ' + str(t_final) + 'times' + "\n"
    else:
        logger.info("%s : %.3f s" % (trace_in, t_final))
        time_result = trace_in.split('.', 1)[0] + ': ' + str(t_final) + 's' + "\n"

    # Path of time_result.txt
    path_result = os.path.join(PWD, "time_result.txt")
    # Judge whether time_result.txt exit or not
    if not os.path.exists(path_result):
        # Create time_result.txt if not exit
        f = open(path_result, 'w')
        f.close()
    else:
        pass

    # Judge whether related time exits in time_result.txt or not
    with open(path_result, 'r') as fr:
        if time_result.split(':')[0] in fr.read():
            # Related time exits in time_result.txt
            trace_exit = True
        else:
            # Related time does not exit in time_result.txt
            trace_exit = False

    # write new result into time_result.txt
    if trace_exit:
        # Over write the old result
        with open(path_result, 'w') as fw:
            fw.write(time_result)
    else:
        # Write a new result
        with open(path_result, 'a') as fa:
            fa.write(time_result)


def bip_performance(trace_in):
    """This func is designed for getting time of BIP Performance and writing result into time_result.txt
    """

    # Time stamp for open channel
    t_open_channel = []
    # Time stamp for close channel
    t_close_channel = []
    # Path of trace
    path_trace = os.path.join(TRACE_PATH, trace_in)

    # Parse the trace and get time stamp
    try:
        DOMTree = xml.dom.minidom.parse(path_trace)
        # Get object of xml
        data = DOMTree.documentElement
        # Get trace item objectives
        items = data.getElementsByTagName("traceitem")
        # Get length of items
        len_item = items.length

        # Get close channel item from all items
        try:
            for i in range(len_item - 1, -1, -1):
                if items[i].getAttribute("type") == "apducommand":
                    interpretation = items[i].childNodes[3]
                    interpretedresult = interpretation.childNodes[1]
                    if interpretedresult.getAttribute("content") == "TERMINAL RESPONSE - CLOSE CHANNEL":
                        time_stamp = items[i].childNodes[5]
                        miliseconds = time_stamp.childNodes[5]
                        t_close_channel.append(int(miliseconds.firstChild.data))
                        logger.info("Time stamp of close channel : %d" % t_close_channel[0])
                        # Get open channel item from all items
                        try:
                            for j in range(i - 1, -1, -1):
                                if items[j].getAttribute("type") == "apducommand":
                                    interpretation = items[j].childNodes[3]
                                    interpretedresult = interpretation.childNodes[1]
                                    if interpretedresult.getAttribute("content") == "TERMINAL RESPONSE - OPEN CHANNEL":
                                        time_stamp = items[j].childNodes[5]
                                        miliseconds = time_stamp.childNodes[5]
                                        t_open_channel.append(int(miliseconds.firstChild.data))
                                        logger.info("Time stamp of open channel : %d" % t_open_channel[0])
                                        break
                        except Exception:
                            logger.info("Cannot find 'TERMINAL RESPONSE - OPEN CHANNEL' in the trace")
                        break
        except Exception:
            logger.info("Cannot find 'TERMINAL RESPONSE - CLOSE CHANNEL' in the trace")

    except Exception:
        logger.info("Failed to parse %s ." % trace_in)

    try:
        t_final = (t_close_channel[0] - t_open_channel[0]) / 1000.0
        # Write result into time_result.txt
        write_time(trace_in, t_final)
    except Exception:
        logger.info("Cannot work out the time and please check trace manually.")


def pps(trace_in):
    """This func is designed for getting time of pps and writing result into time_result.txt
    """

    # Time stamp for ATR
    t_atr = []
    # Time stamp for last command before continuous SW
    t_before_status = []
    # Path of trace
    path_trace = os.path.join(TRACE_PATH, trace_in)

    # Parse the trace and get time stamp
    try:
        DOMTree = xml.dom.minidom.parse(path_trace)
        # Get object of xml
        data = DOMTree.documentElement
        # Get trace item objectives
        items = data.getElementsByTagName("traceitem")
        len_item = items.length

        # Get atr_item from all items
        try:
            for i in range(len_item):
                # select item from item with 'type' attribute
                if items[i].getAttribute("type") == "coldreset":
                    time_stamp = items[i].childNodes[5]
                    miliseconds = time_stamp.childNodes[5]
                    t_atr.append(int(miliseconds.firstChild.data))
                    logger.info("Time stamp of ATR : %d" % t_atr[0])
                    break
                i += 1
        except Exception:
            logger.info("Cannot find 'coldreset' in the trace.")

        # Get item before status from all items
        try:
            for i in range(len_item):
                if items[i].getAttribute("type") == "apducommand":
                    interpretation = items[i].childNodes[3]
                    interpretedresult = interpretation.childNodes[1]
                    if (interpretedresult.getAttribute("content") == "STATUS" and
                            items[i + 2].childNodes[3].childNodes[1].getAttribute("content") == "STATUS" and
                            items[i + 4].childNodes[3].childNodes[1].getAttribute("content") == "STATUS" and
                            items[i + 6].childNodes[3].childNodes[1].getAttribute("content") == "STATUS" and
                            items[i + 8].childNodes[3].childNodes[1].getAttribute("content") == "STATUS" and
                            items[i + 10].childNodes[3].childNodes[1].getAttribute("content") == "STATUS"):
                        time_stamp = items[i - 1].childNodes[5]
                        miliseconds = time_stamp.childNodes[5]
                        t_before_status.append(int(miliseconds.firstChild.data))
                        logger.info("Time stamp of last command before continuous SW : %d" % t_before_status[0])
                        break
                i += 1
        except Exception:
            logger.info("Cannot find three continuous 'STATUS' in the trace.")

    except Exception:
        logger.info("Failed to parse %s ." % trace_in)

    try:
        t_final = (t_before_status[0] - t_atr[0]) / 1000.0
        # Write result into time_result.txt
        write_time(trace_in, t_final)
    except Exception:
        logger.info("Cannot work out the time and please check trace manually.")


def average_pps():
    """This func is designed for getting average time of PPS and writing result into time_result.txt
    """

    # Path of time_result.txt
    path_result = os.path.join(PWD, "time_result.txt")

    # Judge whether time_result.txt exit or not
    if os.path.exists(path_result):
        # List for storing pps trace
        time_average_pps96 = []
        time_average_pps97 = []

        with open(path_result, 'r') as fr:
            time_trace = fr.readlines()
        # Match trace and store time by trace name in list
        for time in time_trace:
            if re.match(re.compile('PPS96'), time):
                time_average_pps96.append(time)
            elif re.match(re.compile('PPS97'), time):
                time_average_pps97.append(time)
            else:
                pass

        # Get 3 traces then get average time of pps, write result into time_result.txt
        if len(time_average_pps96) == 3:
            sum = 0
            for trace in time_average_pps96:
                sum += float(trace.split(' ')[1].split('s')[0])
            time_pps96 = ('%.3f' % (sum / 3))
            # result_time = "Average time of pps96: " + str(time_pps96) + 's'
            logger.info("**********************************************************")
            write_time("Average time of pps96", float(time_pps96))
        else:
            logger.info("Not enough PPS96 trace can be found.")

        if len(time_average_pps97) == 3:
            sum = 0
            for trace in time_average_pps97:
                sum += float(trace.split(' ')[1].split('s')[0])
            time_pps97 = ('%.3f' % (sum / 3))
            # result_time = "Average time of pps97: " + str(time_pps97) + 's'
            logger.info("**********************************************************")
            write_time("Average time of pps97", float(time_pps97))
        else:
            logger.info("**********************************************************")
            logger.info("Not enough PPS97 trace can be found.")
    else:
        pass


def polling_default(trace_in):
    """This func is designed for getting time of default polling and writing result into time_result.txt
    """

    # Time stamp for first status command
    t_status_first = []
    # Time stamp for second status command
    t_status_second = []
    # Path of trace
    path_trace = os.path.join(TRACE_PATH, trace_in)

    # Parse the trace and get time stamp
    try:
        DOMTree = xml.dom.minidom.parse(path_trace)
        # Get object of xml
        data = DOMTree.documentElement
        # Get trace item objectives
        items = data.getElementsByTagName("traceitem")
        len_item = items.length
        # Get status_item1 and status_item2 from all items
        try:
            for i in range(len_item):
                if items[i].getAttribute("type") == "apducommand":
                    interpretation = items[i].childNodes[3]
                    interpretedresult = interpretation.childNodes[1]
                    if (interpretedresult.getAttribute("content") == "STATUS" and
                            items[i + 2].childNodes[3].childNodes[1].getAttribute("content") == "STATUS" and
                            items[i + 4].childNodes[3].childNodes[1].getAttribute("content") == "STATUS" and
                            items[i + 6].childNodes[3].childNodes[1].getAttribute("content") == "STATUS" and
                            items[i + 8].childNodes[3].childNodes[1].getAttribute("content") == "STATUS" and
                            items[i + 10].childNodes[3].childNodes[1].getAttribute("content") == "STATUS"):
                        time_stamp_first = items[i + 8].childNodes[5]
                        miliseconds_first = time_stamp_first.childNodes[5]
                        t_status_first.append(int(miliseconds_first.firstChild.data))
                        logger.info("Time stamp of first SW : %d" % t_status_first[0])
                        time_stamp_second = items[i + 10].childNodes[5]
                        miliseconds_second = time_stamp_second.childNodes[5]
                        t_status_second.append(int(miliseconds_second.firstChild.data))
                        logger.info("Time stamp of second SW : %d" % t_status_second[0])
                        break
                i += 1
        except Exception:
            logger.info("Cannot find six continuous 'STATUS' in the trace.")

    except Exception:
        logger.info("Failed to parse %s ." % trace_in)

    try:
        t_final = (t_status_second[0] - t_status_first[0]) / 1000.0
        # Write result into time_result.txt
        write_time(trace_in, t_final)
    except Exception:
        logger.info("Cannot work out the time and please check trace manually.")


def register(trace_in):
    """This func is designed for getting time of network register and writing result into time_result.txt
    """

    # Time stamp for ATR
    t_atr = []
    # Time stamp for network authentication
    t_auth = []
    # Path of trace
    path_trace = os.path.join(TRACE_PATH, trace_in)

    # Parse the trace and get time stamp
    try:
        DOMTree = xml.dom.minidom.parse(path_trace)
        # Get object of xml
        data = DOMTree.documentElement
        # Get trace item objectives
        items = data.getElementsByTagName("traceitem")
        len_item = items.length
        # Get atr_item and auth_item from all items
        try:
            for i in range(len_item):
                # select item from item with 'type' attribute
                if items[i].getAttribute("type") == "coldreset":
                    time_stamp = items[i].childNodes[5]
                    miliseconds = time_stamp.childNodes[5]
                    t_atr.append(int(miliseconds.firstChild.data))
                    logger.info("Time stamp of ATR : %d" % t_atr[0])
                if items[i].getAttribute("type") == "apducommand":
                    interpretation = items[i].childNodes[3]
                    interpretedresult = interpretation.childNodes[1]
                    if interpretedresult.getAttribute("content") == "INTERNAL AUTHENTICATE":
                        time_stamp = items[i].childNodes[5]
                        miliseconds = time_stamp.childNodes[5]
                        t_auth.append(int(miliseconds.firstChild.data))
                        logger.info("Time stamp of Authentication : %d" % t_auth[0])
                        break
                i += 1
        except Exception:
            logger.info("Cannot find 'coldreset' or 'INTERNAL AUTHENTICATE'in the trace.")

    except Exception:
        logger.info("Failed to parse %s ." % trace_in)

    try:
        t_final = (t_auth[0] - t_atr[0]) / 1000.0
        # Write result into time_result.txt
        write_time(trace_in, t_final)
    except Exception:
        logger.info("Cannot work out the time and please check trace manually.")


def refresh(trace_in):
    """This func is designed for getting time of refresh and writing result into time_result.txt
    """

    # Time stamp for refresh command
    t_fetch_refresh = []
    # Time stamp for network authentication
    t_auth = []
    # Path of trace
    path_trace = os.path.join(TRACE_PATH, trace_in)

    # Parse the trace and get time stamp
    try:
        DOMTree = xml.dom.minidom.parse(path_trace)
        # Get object of xml
        data = DOMTree.documentElement
        # Get trace item objectives
        items = data.getElementsByTagName("traceitem")
        len_item = items.length
        # Get atr_item and auth_item from all items
        try:
            for i in range(len_item):
                # select item from item with 'type' attribute
                if items[i].getAttribute("type") == "apduresponse":
                    interpretation = items[i].childNodes[3]
                    interpretedresult = interpretation.childNodes[1]
                    if interpretedresult.getAttribute("content") == "FETCH - REFRESH":
                        time_stamp = items[i].childNodes[5]
                        miliseconds = time_stamp.childNodes[5]
                        t_fetch_refresh.append(int(miliseconds.firstChild.data))
                        logger.info("Time stamp of 'Fetch refresh' : %d" % t_fetch_refresh[0])
                        try:
                            for j in range(i, len_item):
                                if items[j].getAttribute("type") == "apducommand":
                                    interpretation = items[j].childNodes[3]
                                    interpretedresult = interpretation.childNodes[1]
                                    if interpretedresult.getAttribute("content") == "INTERNAL AUTHENTICATE":
                                        time_stamp = items[j].childNodes[5]
                                        miliseconds = time_stamp.childNodes[5]
                                        t_auth.append(int(miliseconds.firstChild.data))
                                        logger.info("Time stamp of Authentication : %d" % t_auth[0])
                                        break
                                j += 1
                        except Exception:
                            logger.info("Cannot find 'INTERNAL AUTHENTICATE'in the trace.")
                        break
                i += 1
        except Exception:
            logger.info("Cannot find 'FETCH - REFRESH'in the trace.")
    except Exception:
        logger.info("Failed to parse %s ." % trace_in)

    try:
        t_final = (t_auth[0] - t_fetch_refresh[0]) / 1000.0
        # Write result into time_result.txt
        write_time(trace_in, t_final)
    except Exception:
        logger.info("Cannot work out the time and please check trace manually.")


def sm_timeout(trace_in):
    """This func is designed for getting fetch times of smart message and writing result into time_result.txt
    """
    # Define a counter for fetch smart message times
    count = 0
    # Path of trace
    path_trace = os.path.join(TRACE_PATH, trace_in)
    # Match trace
    trace_match = []

    if re.match(re.compile('Timeout_DT.xti'), trace_in):
        trace_match.append('FETCH - DISPLAY TEXT')
    elif re.match(re.compile('Timeout_SI.xti'), trace_in):
        trace_match.append('FETCH - SELECT ITEM')
    elif re.match(re.compile('Timeout_GI.xti'), trace_in):
        trace_match.append('FETCH - GET INPUT')
    else:
        logger.info("**********************************************************")
        logger.info("Failed to match trace with name.")

    # Parse the trace
    try:
        DOMTree = xml.dom.minidom.parse(path_trace)
        # Get object of xml
        data = DOMTree.documentElement
        # Get trace item objectives
        items = data.getElementsByTagName("traceitem")
        len_item = items.length
        # Get atr_item and auth_item from all items
        try:
            for i in range(len_item):
                # select item from item with 'type' attribute
                if items[i].getAttribute("type") == "apduresponse":
                    interpretation = items[i].childNodes[3]
                    interpretedresult = interpretation.childNodes[1]
                    if interpretedresult.getAttribute("content") == trace_match[0]:
                        count += 1
                i += 1
        except Exception:
            logger.info("Cannot find %s in the trace." % trace_match[0])
    except Exception:
        logger.info("Failed to parse %s ." % trace_in)

    try:
        t_final = count
        # Write result into time_result.txt
        write_time(trace_in, t_final)
    except Exception:
        logger.info("Cannot work out the time and please check trace manually.")


# Dic for trace and operated file
TRACE_OP = {
    'Performance': bip_performance,
    'Polling': polling_default,
    'Timeout': sm_timeout,
    'Register': register,
    'Refresh': refresh,
    'PPS': pps
}


# Match trace name with getting time func
def trace_match():
    # Get all traces in trace path
    for root, dirs, files in os.walk(TRACE_PATH):
        traces = files
    logger.info(traces)

    for trace_name in traces:
        flag = []
        for trace_key in TRACE_OP.keys():
            # Match the trace with function
            if re.match(re.compile(trace_key), trace_name):
                flag.append(1)
                logger.info("**********************************************************")
                TRACE_OP[trace_key](trace_name)
                break
            else:
                pass
        if not flag:
            logger.info("**********************************************************")
            logger.info("Cannot match trace name '%s' with operated file." % trace_name)
            logger.info("Please check trace name and be sure the naming is lawful.")


# Run trace_match
trace_match()

# Run time_average_pps
average_pps()
