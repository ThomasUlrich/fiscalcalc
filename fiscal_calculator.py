import fiscalyear
# import workdays
import calendar
import datetime as dt
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
import pandas as pd

import json
from collections import namedtuple
from json import JSONEncoder

def format_print(label, value):
    value_str = str(value)
    total_length = 100
    value_length = len(value_str)
    label_length = len(label)
    fill_length = total_length-value_length-label_length
    print(label, '.'*fill_length, value_str)


def log_month(text, filepath):
    with open(filepath, 'a') as f:
        f.write(text)

def working_days(from_date, to_date):
    from_weekday = from_date.weekday()
    to_weekday = to_date.weekday()
    # If start date is after Friday, modify it to Monday
    if from_weekday > 4:
        from_weekday = 0
    day_diff = to_weekday - from_weekday
    whole_weeks = ((to_date - from_date).days - day_diff) / 7
    workdays_in_whole_weeks = whole_weeks * 5
    beginning_end_correction = min(day_diff, 5) - (max(to_weekday - 4, 0) % 5)
    working_days = workdays_in_whole_weeks + beginning_end_correction
    # Final sanity check (i.e. if the entire range is weekends)
    return max(0, working_days)

def friday_off_days(friday_off_start_date, to_date):
    num_fri = 0
    fridays = []
    days = (to_date - friday_off_start_date).days
    for x in range(0, days, 14):
        fridays.append(friday_off_start_date + dt.timedelta(days=x))
        num_fri += 1
    return num_fri, fridays

def weekend_days(start_date, sunday_start_date, to_date):
    num_weekend_days = 0
    weekends = []
    days = (to_date - sunday_start_date).days

    if (sunday_start_date-start_date).days > 0:
        weekends.append(sunday_start_date - dt.timedelta(days=1))
        num_weekend_days += 1

    for x in range(0, days, 7):
        weekends.append(sunday_start_date + dt.timedelta(days=x))
        num_weekend_days += 1
        if x >= 1:
            weekends.append(sunday_start_date + dt.timedelta(days=x-1))
            num_weekend_days += 1 #get the first saturday too
    return num_weekend_days, weekends

def daterange(date1, date2):
    dates = []
    for n in range(int ((date2 - date1).days)+1):
        dates.append(date1 + dt.timedelta(n))
    return dates

def remaining_days(start_date, active_start_date, to_date):
    active_days = daterange(active_start_date, to_date)
    inactive_days = daterange(start_date, active_start_date)
    active_days_count = (to_date - active_start_date).days
    inactive_days_count = (active_start_date - start_date).days
    return active_days_count, active_days, inactive_days_count, inactive_days

def swap_months(dates, data, end_year):
    fy_begin_data = []
    fy_end_data = []
    fy_end_dates = []
    fy_begin_dates = []
    swapped_dates = []
    swapped_data = []
    for i, d in enumerate(dates):
        if d <= end_year:
            fy_begin_dates.append(d)
            fy_begin_data.append(data[i])
        else:
            fy_end_dates.append(d)
            fy_end_data.append(data[i])
    swapped_dates = fy_end_dates+fy_begin_dates
    swapped_data = fy_end_data+fy_begin_data
    return swapped_dates, swapped_data

def map_calendar(start_date, end_date, fridays, weekends, active_days):
    days = (end_date - start_date).days
    dates = []
    data = []
    day_types = ['weekday_active', 'weekday_inactive', 'weekend_active', 'weekend_inactive', 'friday_off_active', 'friday_off_inactive']
    day_type_counts = {}

    cat_count = len(day_types)
    incr = 1

    coding_dict = {}
    for x in range(cat_count):
        coding_dict.update({day_types[x]:round(incr*x,2)})
        day_type_counts.update({day_types[x]:0})

    for x in range(0, days+1):
        code = ''

        if start_date+dt.timedelta(x) in active_days:
            if start_date+dt.timedelta(x) in fridays:
                code = 'friday_off_active'
            elif start_date+dt.timedelta(x) in weekends:
                code = 'weekend_active'
            else:
                code = 'weekday_active'
            

        else:
            if start_date+dt.timedelta(x) in fridays:
                code = 'friday_off_inactive'
            elif start_date+dt.timedelta(x) in weekends:
                code = 'weekend_inactive'
            else:
                code = 'weekday_inactive'

        data.append(coding_dict[code])
        dates.append(start_date+dt.timedelta(x))
        day_type_counts.update({code:day_type_counts[code]+1})

    return dates, data, day_type_counts

def month_segments(dates):
    months = []
    month_curr = []
    mo_curr = dates[0].month
    mo_last = dates[0].month
    for i, d in enumerate(dates):
        mo_curr = d.month
        if mo_curr != mo_last:
            months.append(month_curr)
            month_curr = []
            month_curr.append(d)
        else:
            month_curr.append(d)
        mo_last = d.month
    #add last month after loop ends since mo_curr != mo_last won't trigger to save it 
    months.append(month_curr)
    return months



def get_week_of_month(year, month, day):
    calendar.setfirstweekday(6)
    # calendar.setfirstweekday(6)
    x = np.array(calendar.monthcalendar(year, month))
    week_of_month = np.where(x==day)[0][0]
    return(week_of_month)

def calendar_array(fig, ax, dates, data, day_type_count_dict):
    i = []
    j = []
    last_week_count = None

    print(dates[0].month)

    for c, d in enumerate(dates):
        i.append(get_week_of_month(d.year, d.month, d.day))
        if (d.weekday() == 6):
            j.append(0)
        else:
            j.append(d.weekday()+1)

        if c == len(dates)-1:
            last_week_count = get_week_of_month(d.year, d.month, d.day)

    ni = max(i)+1

    log_dict = {'month':d.month, 'weekd_count':last_week_count+1, 'days_count':len(dates)}
    format_print('*'*100,'')
    format_print(d.strftime('%B'), d.month)
    format_print('Total Weeks', last_week_count+1)
    format_print('Total Days', len(dates))

    data_label = 'Workdays = {}'.format(day_type_count_dict['weekday_active'])
    ax.text(0.5, last_week_count+1.05, data_label, ha='center')

    dict_targets = ['weekday_active', 'weekday_inactive', 'weekend_active', 'weekend_inactive', 'friday_off_active', 'friday_off_inactive']
    for key in day_type_count_dict:
        format_print(key, day_type_count_dict[key])
        log_dict.update({key:day_type_count_dict[key]})

    calendar = np.nan * np.zeros((ni, 7))
    print(calendar.shape)
    calendar[i, j] = data

    print(calendar)

    return i, j, calendar, log_dict

def calendar_highlight(fig, ax, dates, data, day_type_count_dict):
    i, j, calendar, log_dict = calendar_array(fig, ax, dates, data, day_type_count_dict)

    #'weekday_active', 'weekday_inactive', 'weekend_active', 'weekend_inactive', 'friday_off_active', 'friday_off_inactive'
    colors = ['#efc9af99', '#efc9af40', '#104c9199', '#104c9140', '#1f8ac099', '#1f8ac040']
    cmap = ListedColormap(colors)

    im = ax.imshow(calendar, interpolation='none', cmap=cmap, vmin=0, vmax=len(colors))
    label_days(ax, dates, i, j, calendar)
    return log_dict
    # label_months(ax, dates, i, j, calendar)
    # ax.figure.colorbar(im)

def label_days(ax, dates, i, j, calendar):
    ni, nj = calendar.shape
   
    day_of_month = np.nan * np.zeros((ni, 7))
    day_of_month[i, j] = [d.day for d in dates]

    for (i, j), day in np.ndenumerate(day_of_month):
        if np.isfinite(day):
            ax.text(j, i, int(day), ha='center', va='center')
            last_row = i
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
    ax.set(xticks=np.arange(7), 
           xticklabels=['S', 'M', 'T', 'W', 'R', 'F', 'S'])
    ax.xaxis.tick_top()

    ax.set(yticks=np.arange(ni))
    ax.set_yticklabels([str(x+1) for x in np.arange(ni)])


def plot_month(fig, ax, dates, data, day_type_count_dict, title):
    log_dict = calendar_highlight(fig, ax, dates, data, day_type_count_dict)
    ax.set_title(title, fontweight='bold')
    return log_dict


def config_decoder(param_dict):
    # param_dict_datetime = {}
    # for key in param_dict:
    #     x = namedtuple('X', param_dict.keys())(*[dt.datetime.strptime(s, '%Y-%m-%d') for s in param_dict.values()])
    # x = namedtuple('X', param_dict.keys())(*param_dict.values())

    # print(x)
    return namedtuple('config_decoding', param_dict.keys())(*[dt.datetime.strptime(s, '%Y-%m-%d') for s in param_dict.values()])


class Config:
    def __init__(self, fy_start_date, fy_end_date, friday_off_start_date, sunday_start_date, active_start_date):
        self.fy_start_date, self.fy_end_date, self.friday_off_start_date, self.sunday_start_date, self.active_start_date = fy_start_date, fy_end_date, friday_off_start_date, sunday_start_date, active_start_date
#         date_time_str = '2018-06-29 08:15:27.243860'
#         date_time_obj = dt.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S.%f')

# print('Date:', date_time_obj.date())
# print('Time:', date_time_obj.time())
# print('Date-time:', date_time_obj)


        

        




def main():

    #load json file with configuration data for fiscal year and remaining days (active) days of the year
    config = None
    with open('fiscal_config.json') as json_file:
        config = json.loads(json_file.read(), object_hook=config_decoder)

    #categorize dates into day types = weekdays, off fridays, weekends
    fridays_off_count, fridays_off = friday_off_days(config.friday_off_start_date, config.fy_end_date)

    active_days_count, active_days, inactive_days_count, inactive_days = remaining_days(config.fy_start_date, config.active_start_date, config.fy_end_date)

    weekend_day_count, weekends = weekend_days(config.fy_start_date, config.sunday_start_date, config.fy_end_date)

    dates, data, day_type_counts = map_calendar(config.fy_start_date, config.fy_end_date, fridays_off, weekends, active_days)

    #create 12 month bins
    month_arrays = month_segments(dates)

    columns = 4
    rows = 3
    mo_counter = 0

    fig, ax = plt.subplots(columns, rows, figsize=(16,18))

    active_weekdays_count_total = 0

    months_data = []

    for c in range(columns):
        for r in range(rows):
            dates, data, day_type_count = map_calendar(month_arrays[mo_counter][0], month_arrays[mo_counter][-1], fridays_off, weekends, active_days)
            active_weekdays_count_total += day_type_count['weekday_active']
            log_dict = plot_month(fig, ax[c,r], dates, data, day_type_count, dates[0].strftime('%B %Y'))
            months_data.append(log_dict)
            mo_counter += 1  

    df = pd.DataFrame(months_data)
    df.to_csv('fiscal_output.csv', index=False)

    fig.text(0.5, 0.075, 'Total Workdays = {}'.format(active_weekdays_count_total), fontsize = 12, fontweight='bold', ha='center')

    format_print('Total Active Weekdays', active_weekdays_count_total)

    plt.savefig('fy{}.png'.format(config.fy_end_date.year))
    plt.close(fig)


if __name__ == "__main__":
    main()
