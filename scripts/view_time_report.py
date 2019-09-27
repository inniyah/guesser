#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# See: https://sukhbinder.wordpress.com/2016/05/10/quick-gantt-chart-with-matplotlib/
# See: http://www.clowersresearch.com/main/gantt-charts-in-matplotlib/

import json
import datetime
import argparse
import re
import sys

import numpy
import matplotlib.pyplot as pyplot
import matplotlib.font_manager as font_manager
import matplotlib.dates
import matplotlib.style

VERY_SHORT_TASK = 0.005
MIN_TIME_DIFF = 0.05
TIME_STEPS = 10
TIME_PARTIAL_STEPS = 1

class DebugEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return sorted(obj)

        try:
            ret = json.JSONEncoder.default(self, obj)
        except:
            ret = (str)(obj)
        return ret

def CreateGanttChart(tasks):
    ylabels = []
    colors = []
    customDates = []

    max_date = 0
    for ylabel, startdate, enddate, edgecolor, color in tasks:
        ylabels.append(ylabel)
        customDates.append([startdate, enddate])
        colors.append([edgecolor, color])
        max_date = max(max_date, startdate, enddate)

    #print("ylabels:     %s" % (ylabels,))
    #print("colors:      %s" % (colors,))
    #print("customDates: %s" % (customDates,))

    # round to TIME_STEPS seconds
    max_date += TIME_STEPS
    max_date -= max_date % TIME_STEPS

    ilen = len(ylabels)
    pos = numpy.arange(0.5, ilen * 0.5 + 0.5, 0.5)

    fig = pyplot.figure(figsize=(10, 8))
    ax = fig.add_subplot(111)

    for i in range(len(ylabels)):
        start_date_1, end_date_1 = customDates[i]
        ymax = 1.0 - float(i+1)/float(len(ylabels)+1)
        ymin = ymax
        for j in range(len(ylabels)):
            start_date_2, end_date_2 = customDates[j]
            if i != j and start_date_1 > end_date_2 - MIN_TIME_DIFF and start_date_1 < end_date_2 + MIN_TIME_DIFF:
                print("Connection ('%s' (%s -> %s) to '%s' (%s -> %s)" % (ylabels[j], start_date_2, end_date_2, ylabels[i], start_date_1, end_date_1))
                ymin = 1.0 - float(j+1)/float(len(ylabels)+1)
                ax.axvline(x=start_date_1, ymin=ymin, ymax=ymax, linewidth=1, color='silver', linestyle=':', zorder=1)
                break

    for i in range(len(ylabels)):
        start_date, end_date = customDates[i]
        #print("Draw Task: %s -> %s" % (start_date, end_date))
        ax.barh((i*0.5)+0.5, end_date - start_date, left=start_date, height=0.25, align='center', edgecolor=colors[i][0], color=colors[i][1], alpha=0.8, zorder=2)

    locsy, labelsy = pyplot.yticks(pos, ylabels)
    pyplot.setp(labelsy, fontsize=8)
    ax.axis('tight')
    ax.set_ylim(bottom=-0.1, top=ilen*0.5+0.5)
    ax.grid(color='g', linestyle=':')

    ax.set_xticks(numpy.arange(0, max_date + 1, TIME_STEPS))
    ax.set_xticks(numpy.arange(0, max_date + 1, TIME_PARTIAL_STEPS), minor=True)
    ax.grid(which='minor', alpha=0.2)
    ax.grid(which='major', alpha=0.5)

    labelsx = ax.get_xticklabels()
    pyplot.setp(labelsx, rotation=30, fontsize=8)

    font = font_manager.FontProperties(size='small')

    ax.invert_yaxis()
    fig.autofmt_xdate()

def main():
    parser = argparse.ArgumentParser(description='Compare two different SWE QA JSON File Reports')
    parser.add_argument('-f', '--file', help='Text file with the time reports', required=True)
    parser.add_argument('-s', '--svg', help='SVG file to be generated', required=False)

    view_parser = parser.add_mutually_exclusive_group(required=False)
    view_parser.add_argument('--view', help='View the resulting graph in the screen', dest='view', action='store_true')
    parser.set_defaults(view=False)

    args = vars(parser.parse_args())
    tr_filename = args['file']
    svg_filename = args['svg']
    view_in_screen = args['view']

    tasks = []
    with open(tr_filename, 'r') as f:
        min_dt = None
        for line in f:
            i = {}

            search_results = re.search(r'^(\d{23})-(\d{23}) r=([\d\.]+)m([\d\.]+)s u=([\d\.]+)m([\d\.]+)s s=([\d\.]+)m([\d\.]+)s (.*)$', line, re.IGNORECASE)
            if not search_results:
                print('Cannot parse line: "%s"' % (line.strip(),))
                sys.exit(-1)
            d = search_results.groups()
            start_dt = datetime.datetime(year=int(d[0][0:4]), month=int(d[0][4:6]), day=int(d[0][6:8]), hour=int(d[0][8:10]), minute=int(d[0][10:12]), second=int(d[0][12:14]), microsecond=int(d[0][14:20]))
            end_dt = datetime.datetime(year=int(d[1][0:4]), month=int(d[1][4:6]), day=int(d[1][6:8]), hour=int(d[1][8:10]), minute=int(d[1][10:12]), second=int(d[1][12:14]), microsecond=int(d[1][14:20]))
            #print('Start: {} ({} UTC); End: {} ({} UTC)'.format(d[0], start_dt, d[1], end_dt))

            # pylint: disable=bad-whitespace
            i['AbsStartTime'] = start_dt
            i['AbsEndTime']   = end_dt
            i['RealTime']     = float(d[2]) * 60.0 + float(d[3])
            i['UserTime']     = float(d[4]) * 60.0 + float(d[5])
            i['SysTime']      = float(d[6]) * 60.0 + float(d[7])

            search_results = re.search(r'^(.*)##(.*)##$', d[8].strip(), re.IGNORECASE)
            if search_results:
                i['Command']    = search_results.group(1).strip()
                i['Label']      = search_results.group(2).strip()
                tasks.append(i)
            elif i['RealTime'] >= VERY_SHORT_TASK:
                i['Command']    = d[8].strip()
                i['Label']      = i['Command'] if len(i['Command']) <= 10 else i['Command'][:10] + "..."
                tasks.append(i)

            if min_dt is None or start_dt < min_dt:
                min_dt = start_dt

            if (i['UserTime'] >= VERY_SHORT_TASK or i['SysTime'] >= VERY_SHORT_TASK) and not i.get('Label', None):
                print('Big task unassigned: "%s"' % (line.strip(),))
                json.dump(i, sys.stdout, cls=DebugEncoder, indent=2, sort_keys=True)
                sys.exit(-1)

        #print("Initial Time: %s" % (min_dt,))

        time_zero = None # Hack to fix bug when difference of timestamps do wierd things

        for i in tasks:
            # pylint: disable=bad-whitespace
            i['StartTime'] = (i['AbsStartTime'] - min_dt).total_seconds()
            i['EndTime']   = (i['AbsEndTime'] - min_dt).total_seconds()

            if time_zero is None:
                time_zero = i['StartTime']
            elif time_zero > i['StartTime']:
                time_zero = i['StartTime']

        for i in tasks:
            i['StartTime'] -= time_zero
            i['EndTime']   -= time_zero
            print("Relative time for '%s': %s -> %s" % (i['Label'], i['StartTime'], i['EndTime']))

        #json.dump(tasks, sys.stdout, cls=DebugEncoder, indent=2, sort_keys=True)

    tasks_info = []
    for task in tasks:
        task_name = task['Label']
        start_time = task['StartTime']
        end_time = task['EndTime']
        tasks_info.append((task_name, start_time, end_time, 'darkblue', 'red'))

    tasks_info = sorted(tasks_info, key=lambda x: (x[1], x[2]))
    #json.dump(tasks_info, sys.stdout, cls=DebugEncoder, indent=2, sort_keys=True)

    CreateGanttChart(tasks_info)
    if svg_filename:
        if not svg_filename.lower().endswith('.svg'):
            svg_filename += '.svg'
        pyplot.savefig(svg_filename)

    if view_in_screen:
        pyplot.show()

if __name__ == "__main__":
    main()
